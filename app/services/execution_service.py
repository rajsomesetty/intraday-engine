from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from app.models.trade import Trade
from app.models.position import Position
from app.services.risk_service import enforce_risk, RiskException
from app.models.account import Account


def execute_trade(
    db: Session,
    symbol: str,
    quantity: int,
    price: float,
    side: str,
    idempotency_key: str,
):

    try:
        # --------------------------------
        # 1️⃣ Idempotency Check
        # --------------------------------
        existing = (
            db.query(Trade)
            .filter(Trade.order_idempotency_key == idempotency_key)
            .first()
        )
        if existing:
            return existing

        trade_value = quantity * price

        # --------------------------------
        # 2️⃣ Lock Account Row
        # --------------------------------
        account = (
            db.query(Account)
            .filter(Account.id == 1)
            .with_for_update()
            .first()
        )

if not account:
    raise Exception("Account not initialized")

        if not account:
            raise Exception("Account not initialized")

        # --------------------------------
        # 3️⃣ Lock Position Row
        # --------------------------------
        position = (
            db.query(Position)
            .filter(Position.symbol == symbol)
            .with_for_update()
            .first()
        )

        if not position:
            position = Position(
                symbol=symbol,
                quantity=0,
                average_price=0.0,
            )
            db.add(position)
            db.flush()

        # --------------------------------
        # 4️⃣ SIMULATE POST-TRADE STATE
        # --------------------------------
        simulated_qty = position.quantity
        simulated_avg = position.average_price

        if side == "BUY":

            new_total_qty = simulated_qty + quantity

            if new_total_qty == 0:
                simulated_avg = 0
            else:
                simulated_avg = (
                    (simulated_qty * simulated_avg)
                    + (quantity * price)
                ) / new_total_qty

            simulated_qty = new_total_qty

        elif side == "SELL":

            if quantity > simulated_qty:
                raise RiskException("Cannot sell more than held quantity")

            simulated_qty -= quantity

        else:
            raise Exception("Invalid side. Must be BUY or SELL")

        # --------------------------------
        # 5️⃣ Build Simulated Portfolio
        # --------------------------------
        all_positions = db.query(Position).all()

        simulated_positions = []

        for pos in all_positions:
            if pos.symbol == symbol:
                simulated_positions.append({
                    "symbol": symbol,
                    "quantity": simulated_qty,
                    "average_price": simulated_avg,
                })
            else:
                simulated_positions.append({
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                })

        # If new symbol not previously present
        if not any(p["symbol"] == symbol for p in simulated_positions):
            simulated_positions.append({
                "symbol": symbol,
                "quantity": simulated_qty,
                "average_price": simulated_avg,
            })

        # --------------------------------
        # 6️⃣ Enforce Risk on Simulated State
        # --------------------------------
        enforce_risk(
            account=account,
            simulated_positions=simulated_positions,
            trade_value=trade_value,
            ltp=price,
        )

        # --------------------------------
        # 7️⃣ Apply Mutation After Risk Passes
        # --------------------------------
        position.quantity = simulated_qty
        position.average_price = simulated_avg

        if side == "SELL":
            realized_pnl = (price - position.average_price) * quantity

            db.execute(
                text(
                    "UPDATE account SET daily_pnl = daily_pnl + :pnl WHERE id=1"
                ),
                {"pnl": realized_pnl},
            )

        # --------------------------------
        # 8️⃣ Insert Trade
        # --------------------------------
        trade = Trade(
            order_idempotency_key=idempotency_key,
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            status=f"{side}_EXECUTED",
        )

        db.add(trade)

        # --------------------------------
        # 9️⃣ Commit
        # --------------------------------
        db.commit()
        db.refresh(trade)

        return trade

    except RiskException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        return (
            db.query(Trade)
            .filter(Trade.order_idempotency_key == idempotency_key)
            .first()
        )

    except Exception:
        db.rollback()
        raise
