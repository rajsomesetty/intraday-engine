from sqlalchemy import Column, Integer, Numeric, Boolean, Text, DateTime
from app.models.base import Base


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, index=True)

    total_capital = Column(Numeric, nullable=False)
    daily_pnl = Column(Numeric, nullable=False, default=0)
    daily_loss_limit = Column(Numeric, nullable=False)

    # 🔥 New fields
    intraday_peak_equity = Column(Numeric, nullable=False, default=50000)
    current_equity = Column(Numeric, nullable=False, default=50000)
    is_trading_enabled = Column(Boolean, nullable=False, default=True)

    breach_count = Column(Integer, default=0)
    last_breach_reason = Column(Text, nullable=True)
    last_breach_time = Column(DateTime, nullable=True)
