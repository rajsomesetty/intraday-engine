import redis
import os
import json
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

REDIS_HOST = os.getenv("REDIS_HOST", "intraday-redis")

redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


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
        # GLOBAL TRADING KILL SWITCH
        # -----------------------------------

        if not trading_enabled():
            raise RiskException("Global trading disabled")

        # -----------------------------------
        # Idempotency
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
                entry_price=0.0,
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
        # BUY LOGIC
        # -----------------------------------

        if side == "BUY":

            new_total_qty = simulated_qty + quantity

            simulated_avg = (
                (Decimal(simulated_qty) * Decimal(str(simulated_avg)))
                + (Decimal(quantity) * price_decimal)
            ) / Decimal(new_total_qty)

            simulated_qty = new_total_qty

            if stop_loss is not None:

                stop_decimal = Decimal(str(stop_loss))
                trailing_distance = price_decimal - stop_decimal

                if trailing_distance > 0:
                    position.trailing_distance = trailing_distance
                    position.highest_price = price_decimal

        # -----------------------------------
        # SELL LOGIC
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
        # Risk Simulation
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
        # Audit
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
        # Apply Position Updates
        # -----------------------------------

        position.quantity = simulated_qty
        position.entry_price = simulated_avg

        if stop_loss is not None:
            position.stop_loss = stop_loss

        if side == "SELL":
            account.daily_pnl += realized_pnl

        if strategy_name and side == "SELL":

            pnl_value = float(realized_pnl)

            update_strategy_pnl(strategy_name, pnl_value)
            check_drawdown(strategy_name)

        # -----------------------------------
        # Trade Record
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
        # Publish Trade Event (NEW)
        # -----------------------------------

        try:

            trade_event = {
                "id": trade.id,
                "account_id": trade.account_id,
                "symbol": trade.symbol,
                "side": side,
                "quantity": trade.quantity,
                "price": float(trade.entry_price),
                "timestamp": datetime.utcnow().isoformat(),
            }

            redis_client.publish(
                "trade_events",
                json.dumps({
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "side": side,
                    "time": str(datetime.utcnow())
                })
            )

        except Exception as e:
            print("⚠️ Failed to publish trade event:", e)

        return trade

    except RiskException as e:

        db.rollback()

        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .with_for_update()
            .first()
        )

        if account:

            account.is_trading_enabled = False
            account.breach_count = (account.breach_count or 0) + 1
            account.last_breach_reason = str(e)
            account.last_breach_time = datetime.utcnow()

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

        raise e

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

    except Exception:

        db.rollback()
        raise
