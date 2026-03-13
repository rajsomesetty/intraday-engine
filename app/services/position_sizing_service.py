from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.account import Account

MAX_ALLOCATION = Decimal("0.20")


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

    # Use MTM-adjusted equity
    capital = Decimal(str(account.current_equity or account.total_capital))

    entry_price = Decimal(str(entry_price))
    stop_loss = Decimal(str(stop_loss))
    risk_per_trade = Decimal(str(risk_per_trade))

    # Risk per trade amount
    risk_amount = capital * risk_per_trade

    # Per share risk
    per_share_risk = abs(entry_price - stop_loss)

    if per_share_risk <= 0:
        return 0

    # Quantity based on risk
    risk_quantity = risk_amount / per_share_risk

    # Allocation cap
    max_trade_value = capital * MAX_ALLOCATION
    max_quantity = max_trade_value / entry_price

    # Final position size
    final_quantity = min(risk_quantity, max_quantity)

    return max(int(final_quantity), 0)
