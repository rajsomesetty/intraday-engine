from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class TradeAudit(Base):
    __tablename__ = "trade_audit"

    id = Column(Integer, primary_key=True)

    # 🔥 Multi-account support
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)

    symbol = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric, nullable=False)
    side = Column(Text, nullable=False)

    simulated_equity = Column(Numeric)
    simulated_drawdown = Column(Numeric)
    simulated_total_pnl = Column(Numeric)

    status = Column(Text, nullable=False)
    rejection_reason = Column(Text)

    created_at = Column(DateTime, server_default=func.now())

    account = relationship("Account")
