from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.position import Position


def update_position(
    db: Session,
    symbol: str,
    quantity: int,
    price: float,
) -> Position:

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
            entry_price=0
        )

        db.add(position)
        db.flush()

    new_total_qty = position.quantity + quantity

    price_decimal = Decimal(str(price))

    if new_total_qty == 0:
        position.entry_price = 0
    else:

        position.entry_price = (
            (Decimal(position.quantity) * Decimal(str(position.entry_price)))
            + (Decimal(quantity) * price_decimal)
        ) / Decimal(new_total_qty)

    position.quantity = new_total_qty

    return position
