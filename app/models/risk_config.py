from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class RiskConfig(Base):
    __tablename__ = "risk_config"

    id = Column(Integer, primary_key=True)

    account_id = Column(
        Integer,
        ForeignKey("account.id"),
        nullable=False,
        unique=True
    )

    daily_loss_limit = Column(Numeric, nullable=False)
    max_allocation_pct = Column(Numeric, nullable=False)
    max_exposure_pct = Column(Numeric, nullable=False)
    max_open_positions = Column(Integer, nullable=False)

    # NEW
    max_portfolio_heat_pct = Column(Numeric, nullable=False, default=5)

    account = relationship("Account")
