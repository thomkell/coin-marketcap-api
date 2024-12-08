# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base
from datetime import datetime

class Coin(Base):
    __tablename__ = "coins"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    symbol = Column(String, unique=True, index=True)
    current_price = Column(Float)
    market_cap = Column(Float)
    change_24h = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
