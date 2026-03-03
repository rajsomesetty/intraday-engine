from sqlalchemy import Column, Integer, String, Float
from app.models.base import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, index=True)
    quantity = Column(Integer, default=0)
    average_price = Column(Float, default=0.0)
