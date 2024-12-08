"""
# app/schemas.py
from pydantic import BaseModel
from datetime import datetime

class CoinBase(BaseModel):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    change_24h: float

class CoinDB(CoinBase):
    id: int
    last_updated: datetime

    class Config:
        orm_mode = True
"""

# app/schemas.py
from pydantic import BaseModel
from datetime import datetime

class CoinBase(BaseModel):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    change_24h: float
    last_updated: datetime

    class Config:
        from_attributes = True

class CoinDB(CoinBase):
    id: int

    class Config:
        from_attributes = True
