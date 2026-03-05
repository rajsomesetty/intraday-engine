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

from app.services.metrics_service import (
    total_trades,
    total_rejections,
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
):    

    try:

        # --------------------------------
        # 1️⃣ Idempotency Check
        # --------------------------------
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

        # --------------------------------
        # 2️⃣ Global Rate Limit Protection
        # --------------------------------
        enforce_rate_limit(db, account_id)

        trade_value = Decimal(quantity) * Decimal(str(price))

        # --------------------------------
        # 3️⃣ Lock Account Row
        # --------------------------------
        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .with_for_update()
            .first()
        )

        if not account:
            raise Exception("Account not initialized")

        # --------------------------------
        # 4️⃣ Lock Position Row
        # --------------------------------
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
                average_price=0.0,
            )
            db.add(position)
            db.flush()

        # --------------------------------
        # 5️⃣ Simulate Post-Trade State
        # --------------------------------
        simulated_qty = position.quantity
        simulated_avg = position.average_price
        realized_pnl = Decimal("0")

        if side == "BUY":

            new_total_qty = simulated_qty + quantity

            if new_total_qty == 0:
                simulated_avg = 0
            else:
                simulated_avg = (
                    (Decimal(simulated_qty) * Decimal(str(simulated_avg)))
                    + (Decimal(quantity) * Decimal(str(price)))
                ) / Decimal(new_total_qty)

            simulated_qty = new_total_qty

        elif side == "SELL":

            if quantity > simulated_qty:
                raise RiskException("Cannot sell more than held quantity")

            price_decimal = Decimal(str(price))
            old_avg = Decimal(str(position.average_price))
            qty_decimal = Decimal(quantity)

            realized_pnl = (price_decimal - old_avg) * qty_decimal
            simulated_qty -= quantity

        else:
            raise Exception("Invalid side. Must be BUY or SELL")

        # --------------------------------
        # 6️⃣ Build Simulated Portfolio
        # --------------------------------
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
                "average_price": pos.average_price,
            })

        simulated_positions.append({
            "symbol": symbol,
            "quantity": simulated_qty,
            "average_price": simulated_avg,
        })

        # --------------------------------
        # 7️⃣ Update Market Data
        # --------------------------------
        market_data_service.update_price(symbol, price)
        ltp_map = market_data_service.get_all_prices()

        # --------------------------------
        # 8️⃣ Simulate Daily PnL
        # --------------------------------
        simulated_daily_pnl = account.daily_pnl

        if side == "SELL":
            simulated_daily_pnl += realized_pnl

        # --------------------------------
        # 9️⃣ Enforce Risk Engine
        # --------------------------------
        simulation_result = enforce_risk(
            account=account,
            simulated_positions=simulated_positions,
            trade_value=trade_value,
            ltp_map=ltp_map,
            simulated_daily_pnl=simulated_daily_pnl,
        )

        # --------------------------------
        # 🔟 Insert PASSED Audit
        # --------------------------------
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

        # --------------------------------
        # 11️⃣ Apply Position Mutation
        # --------------------------------
        position.quantity = simulated_qty
        position.average_price = simulated_avg

        if side == "SELL":
            account.daily_pnl += realized_pnl

        # --------------------------------
        # 12️⃣ Insert Trade
        # --------------------------------
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

        # --------------------------------
        # 13️⃣ Commit
        # --------------------------------
        db.commit()
        db.refresh(trade)

        return trade

    except RiskException as e:

        db.rollback()

        account = (
            db.query(Account)
            .filter(Account.id == account_id)
            .with_for_update()
            .first()
        )

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
