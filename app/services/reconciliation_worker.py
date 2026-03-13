import time
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.trade import Trade
from app.models.position import Position

# IMPORTANT: load all models
from app.models import account
from app.models import trade
from app.models import position


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLEEP_INTERVAL = 10


def run_reconciliation_cycle(db: Session):

    # Aggregate trades
    trade_positions = (
        db.query(
            Trade.account_id,
            Trade.symbol,
            func.sum(Trade.quantity).label("qty")
        )
        .group_by(Trade.account_id, Trade.symbol)
        .all()
    )

    for trade_pos in trade_positions:

        account_id = trade_pos.account_id
        symbol = trade_pos.symbol
        trade_qty = trade_pos.qty or 0

        position = (
            db.query(Position)
            .filter(
                Position.account_id == account_id,
                Position.symbol == symbol
            )
            .first()
        )

        pos_qty = position.quantity if position else 0

        if trade_qty != pos_qty:

            logger.error(
                f"RECONCILIATION MISMATCH "
                f"account={account_id} symbol={symbol} "
                f"trades={trade_qty} position={pos_qty}"
            )

            # Auto repair
            if position:
                position.quantity = trade_qty
            else:
                position = Position(
                    account_id=account_id,
                    symbol=symbol,
                    quantity=trade_qty,
                    entry_price=0
                )
                db.add(position)

    db.commit()


def reconciliation_loop():

    logger.info("Starting Reconciliation Worker...")

    while True:

        db = SessionLocal()

        try:
            run_reconciliation_cycle(db)

        except Exception as e:
            logger.error(f"Reconciliation cycle failed: {e}")

        finally:
            db.close()

        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    reconciliation_loop()
