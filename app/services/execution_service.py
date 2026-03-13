import redis
import os
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime

from app.models.trade import Trade
from app.models.position import Position
from app.models.account import Account
from app.models.trade_audit import TradeAudit

from app.services.risk_service import enforce_risk, RiskException
from app.services.market_data_service import market_data_service
from app.services.rate_limit_service import enforce_rate_limit
from app.services.strategy_state_service import update_strategy_pnl, check_drawdown
from app.services.metrics_service import total_trades, total_rejections
from app.services.account_lock_service import lock_account
from app.services.liquidity_service import simulate_liquidity
from app.services.system_control_service import trading_enabled

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True
)


def execute_trade(
    db: Session,
    account_id: int,
    symbol: str,
    quantity: int,
    price: float,
    side: str,
    idempotency_key: str,
    strategy_name: str = None,
    stop_loss: float = None,
):

    try:

        # -----------------------------------
        # Global trading switch
        # -----------------------------------

        if not trading_enabled():
            raise RiskException("Global trading disabled")

        # -----------------------------------
        # Idempotency protection
        # -----------------------------------

        existing = (
            db.query(Trade)
            .filter(
                Trade.order_idempotency_key == idempotency_key,
                Trade.account_id == account_id,
            )
            .first()
        )

        if existing:
            return existing

        enforce_rate_limit(db, account_id)

        # -----------------------------------
        # Liquidity simulation
        # -----------------------------------

        price = simulate_liquidity(price, quantity, side)

        trade_value = Decimal(quantity) * Decimal(str(price))

        lock_account(db, account_id)

        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .first()
        )

        if not account:
            raise Exception("Account not initialized")

        # -----------------------------------
        # Load / create position
        # -----------------------------------

        position = (
            db.query(Position)
            .filter(
                Position.account_id == account_id,
                Position.symbol == symbol,
            )
            .with_for_update()
            .first()
        )

        if not position:

            position = Position(
                account_id=account_id,
                symbol=symbol,
                quantity=0,
                entry_price=0,
                stop_loss=stop_loss,
                highest_price=None,
                trailing_distance=None,
            )

            db.add(position)
            db.flush()

        simulated_qty = position.quantity
        simulated_avg = position.entry_price
        realized_pnl = Decimal("0")

        price_decimal = Decimal(str(price))

        # -----------------------------------
        # BUY
        # -----------------------------------

        if side == "BUY":

            new_total_qty = simulated_qty + quantity

            simulated_avg = (
                (Decimal(simulated_qty) * Decimal(str(simulated_avg)))
                + (Decimal(quantity) * price_decimal)
            ) / Decimal(new_total_qty)

            simulated_qty = new_total_qty

        # -----------------------------------
        # SELL
        # -----------------------------------

        elif side == "SELL":

            if quantity > simulated_qty:
                raise RiskException("Cannot sell more than held quantity")

            old_avg = Decimal(str(position.entry_price))
            qty_decimal = Decimal(quantity)

            realized_pnl = (price_decimal - old_avg) * qty_decimal
            simulated_qty -= quantity

        else:
            raise Exception("Invalid side")

        # -----------------------------------
        # Risk simulation
        # -----------------------------------

        simulated_positions = []

        other_positions = (
            db.query(Position)
            .filter(
                Position.account_id == account_id,
                Position.symbol != symbol,
            )
            .all()
        )

        for pos in other_positions:

            simulated_positions.append({
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "entry_price": pos.entry_price,
                "stop_loss": pos.stop_loss,
            })

        simulated_positions.append({
            "symbol": symbol,
            "quantity": simulated_qty,
            "entry_price": simulated_avg,
            "stop_loss": stop_loss,
        })

        market_data_service.update_price(symbol, price)
        ltp_map = market_data_service.get_all_prices()

        simulated_daily_pnl = account.daily_pnl

        if side == "SELL":
            simulated_daily_pnl += realized_pnl

        simulation_result = enforce_risk(
            account=account,
            simulated_positions=simulated_positions,
            trade_value=trade_value,
            ltp_map=ltp_map,
            simulated_daily_pnl=simulated_daily_pnl,
        )

        # -----------------------------------
        # Audit (PASSED)
        # -----------------------------------

        audit = TradeAudit(
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            side=side,
            simulated_equity=simulation_result["equity"],
            simulated_drawdown=simulation_result["drawdown"],
            simulated_total_pnl=simulation_result["total_pnl"],
            status="PASSED",
        )

        db.add(audit)

        # -----------------------------------
        # Apply position updates
        # -----------------------------------

        position.quantity = simulated_qty
        position.entry_price = simulated_avg

        if side == "SELL":
            account.daily_pnl += realized_pnl

        # -----------------------------------
        # Record trade
        # -----------------------------------

        trade = Trade(
            account_id=account_id,
            order_idempotency_key=idempotency_key,
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            status=f"{side}_EXECUTED",
            strategy_name=strategy_name,
        )

        db.add(trade)

        total_trades.inc()

        db.commit()
        db.refresh(trade)

        # -----------------------------------
        # Publish trade event
        # -----------------------------------

        try:

            event = {
                "type": "trade",
                "trade_id": trade.id,
                "account_id": trade.account_id,
                "symbol": trade.symbol,
                "side": side,
                "quantity": trade.quantity,
                "price": float(trade.entry_price),
                "timestamp": datetime.utcnow().isoformat()
            }

            redis_client.publish("trade_events", json.dumps(event))

        except Exception as e:
            logger.error(f"Trade event publish failed: {e}")

        return trade

    # -----------------------------------
    # Risk rejection (DO NOT disable account)
    # -----------------------------------

    except RiskException as e:

        db.rollback()

        logger.warning(f"Trade rejected by risk engine: {e}")

        audit = TradeAudit(
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            side=side,
            status="REJECTED",
            rejection_reason=str(e),
        )

        db.add(audit)

        total_rejections.inc()

        db.commit()

        return None

    except IntegrityError:

        db.rollback()

        return (
            db.query(Trade)
            .filter(
                Trade.order_idempotency_key == idempotency_key,
                Trade.account_id == account_id,
            )
            .first()
        )

    except Exception as e:

        db.rollback()
        logger.error(f"Execution error: {e}")
        raise
