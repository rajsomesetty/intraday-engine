from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)

    symbol = Column(String)

    quantity = Column(Integer)

    entry_price = Column(Numeric)

    stop_loss = Column(Numeric, nullable=True)

    account_id = Column(Integer)

    highest_price = Column(Numeric, nullable=True)
    trailing_distance = Column(Numeric, nullable=True)
