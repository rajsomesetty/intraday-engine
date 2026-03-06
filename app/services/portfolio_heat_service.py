from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.position import Position
from app.models.account import Account

MAX_PORTFOLIO_HEAT = Decimal("0.05")  # 5%


def calculate_portfolio_heat(db: Session, account_id: int):

    positions = (
        db.query(Position)
        .filter(Position.account_id == account_id)
        .all()
    )

    total_risk = Decimal("0")

    for p in positions:

        if p.stop_loss is None or p.quantity <= 0:
            continue

        entry = Decimal(str(p.entry_price))
        stop = Decimal(str(p.stop_loss))

        risk_per_share = abs(entry - stop)

        position_risk = risk_per_share * abs(p.quantity)

        total_risk += position_risk

    return total_risk


def check_portfolio_heat(
    db: Session,
    account_id: int,
    new_trade_risk: Decimal
):

    account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not account:
        return False

    capital = Decimal(account.current_equity)

    max_allowed_risk = capital * MAX_PORTFOLIO_HEAT

    current_heat = calculate_portfolio_heat(db, account_id)

    if current_heat + new_trade_risk > max_allowed_risk:

        print(
            f"🔥 Portfolio heat exceeded "
            f"(current={current_heat} new={new_trade_risk} "
            f"limit={max_allowed_risk})"
        )

        return False

    return True
