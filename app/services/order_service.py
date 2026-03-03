from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.trade import Trade
import uuid


def place_order(db: Session, symbol: str, quantity: int, idempotency_key: str):
    try:
        # Check if already exists
        existing = db.query(Trade).filter(
            Trade.order_idempotency_key == idempotency_key
        ).first()

        if existing:
            return existing

        # TODO: Add risk engine check here

        trade = Trade(
            order_idempotency_key=idempotency_key,
            symbol=symbol,
            quantity=quantity,
            status="PENDING",
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)

        return trade

    except IntegrityError:
        db.rollback()
        return db.query(Trade).filter(
            Trade.order_idempotency_key == idempotency_key
        ).first()
