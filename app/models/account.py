from sqlalchemy import Column, Integer, Numeric, Boolean
from app.db.base import Base  # adjust if your Base import differs


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
