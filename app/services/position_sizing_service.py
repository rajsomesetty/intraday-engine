from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.account import Account

MAX_ALLOCATION = Decimal("0.40")


def calculate_position_size(
    db: Session,
    account_id: int,
    entry_price: Decimal,
    stop_loss: Decimal,
    risk_per_trade: Decimal
) -> int:
    """
    Calculate position size based on risk per trade
    with allocation cap protection.
    """

    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        return 0

    capital = Decimal(account.equity)

    # Risk based sizing
    risk_amount = capital * risk_per_trade

    per_share_risk = abs(entry_price - stop_loss)

    if per_share_risk <= 0:
        return 0

    risk_quantity = risk_amount / per_share_risk

    # Allocation cap
    max_trade_value = capital * MAX_ALLOCATION
    max_quantity = max_trade_value / entry_price

    # Final quantity
    final_quantity = min(risk_quantity, max_quantity)

    return max(int(final_quantity), 0)
