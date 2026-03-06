from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.position import Position
from app.services.execution_queue import enqueue_execution


def check_stop_losses(symbol: str, price: float):

    db: Session = SessionLocal()

    try:

        positions = (
            db.query(Position)
            .filter(
                Position.symbol == symbol,
                Position.quantity > 0,
                Position.stop_loss != None
            )
            .with_for_update(skip_locked=True)
            .all()
        )

        price_dec = Decimal(str(price))

        for pos in positions:

            stop = Decimal(pos.stop_loss)

            # -----------------------------------
            # Trailing Stop Logic
            # -----------------------------------

            if pos.trailing_distance is not None:

                trailing_distance = Decimal(pos.trailing_distance)

                # initialize highest price
                if pos.highest_price is None:
                    pos.highest_price = price_dec

                # update highest price
                if price_dec > Decimal(pos.highest_price):
                    pos.highest_price = price_dec

                    new_stop = pos.highest_price - trailing_distance

                    if new_stop > stop:
                        pos.stop_loss = new_stop
                        stop = new_stop

            # -----------------------------------
            # Stop Trigger
            # -----------------------------------

            if price_dec <= stop:

                print(
                    f"🛑 Stop loss triggered "
                    f"{symbol} @ {price} "
                    f"(SL {stop})"
                )

                enqueue_execution({
                    "account_id": pos.account_id,
                    "symbol": symbol,
                    "quantity": pos.quantity,
                    "price": price,
                    "side": "SELL",
                    "strategy_name": "STOP_LOSS_ENGINE",
                    "idempotency_key": f"STOPLOSS-{pos.id}-{price}"
                })

        db.commit()

    except Exception as e:

        print("❌ Stop loss monitor failed:", e)
        db.rollback()

    finally:

        db.close()
