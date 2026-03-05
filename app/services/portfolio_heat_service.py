from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.position import Position
from app.models.account import Account

MAX_PORTFOLIO_HEAT = Decimal("0.05")


def calculate_portfolio_heat(db: Session, account_id: int):

    positions = db.query(Position).filter(
        Position.account_id == account_id
    ).all()

    total_risk = Decimal("0")

    for p in positions:

        if p.stop_loss is None:
            continue

        risk_per_share = abs(
            Decimal(p.entry_price) - Decimal(p.stop_loss)
        )

        position_risk = risk_per_share * p.quantity

        total_risk += position_risk

    return total_risk


def check_portfolio_heat(
    db: Session,
    account_id: int,
    new_trade_risk: Decimal
):

    account = db.query(Account).filter(
        Account.id == account_id
    ).first()

    capital = Decimal(account.equity)

    max_allowed_risk = capital * MAX_PORTFOLIO_HEAT

    current_heat = calculate_portfolio_heat(db, account_id)

    if current_heat + new_trade_risk > max_allowed_risk:
        return False

    return True
