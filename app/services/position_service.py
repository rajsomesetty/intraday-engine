from sqlalchemy.orm import Session
from app.models.position import Position


def update_position(
    db: Session,
    symbol: str,
    quantity: int,
    price: float,
) -> Position:
    """
    Atomic position update using row-level locking.
    Must be called inside an active transaction.
    """

    # Lock row for this symbol
    position = (
        db.query(Position)
        .filter(Position.symbol == symbol)
        .with_for_update()
        .first()
    )

    # If position does not exist, create it
    if not position:
        position = Position(
            symbol=symbol,
            quantity=0,
            average_price=0.0,
        )
        db.add(position)
        db.flush()  # ensure ID assigned before update

    new_total_qty = position.quantity + quantity

    if new_total_qty == 0:
        position.average_price = 0.0
    else:
        position.average_price = (
            (position.quantity * position.average_price)
            + (quantity * price)
        ) / new_total_qty

    position.quantity = new_total_qty

    return position
