from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)

    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    symbol = Column(String, nullable=False)

    quantity = Column(Integer, nullable=False)
    average_price = Column(Numeric, nullable=False)

    account = relationship("Account")
