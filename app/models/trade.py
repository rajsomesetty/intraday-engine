from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Numeric,
)
from sqlalchemy.orm import relationship
from app.models.base import Base
import datetime


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 Multi-account support
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)

    # Idempotency key (VERY IMPORTANT)
    order_idempotency_key = Column(String, nullable=False, unique=True)

    symbol = Column(String, index=True)
    quantity = Column(Integer)

    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)

    status = Column(String, default="PENDING")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    strategy_name = Column(String, nullable=True)

    account = relationship("Account")

    __table_args__ = (
        UniqueConstraint("order_idempotency_key", name="uq_order_idempotency_key"),
    )
