"""
# app/crud.py
from sqlalchemy.orm import Session
from .models import Coin
from .schemas import CoinBase
from datetime import datetime

def upsert_coin(db: Session, coin_data: CoinBase):
    db_coin = db.query(Coin).filter(Coin.symbol == coin_data.symbol).first()
    if db_coin:
        db_coin.name = coin_data.name
        db_coin.current_price = coin_data.current_price
        db_coin.market_cap = coin_data.market_cap
        db_coin.change_24h = coin_data.change_24h
        db_coin.last_updated = datetime.utcnow()
    else:
        db_coin = Coin(**coin_data.dict(), last_updated=datetime.utcnow())
        db.add(db_coin)
    db.commit()
    db.refresh(db_coin)
    return db_coin

def get_coins(db: Session):
    return db.query(Coin).all()
"""



# app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy import desc

from . import models, schemas

async def get_coins(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Coin).offset(skip).limit(limit))
    return result.scalars().all()

async def upsert_coin(db: AsyncSession, coin: schemas.CoinBase):
    stmt = select(models.Coin).where(models.Coin.symbol == coin.symbol)
    result = await db.execute(stmt)
    existing_coin = result.scalars().first()
    if existing_coin:
        # Update existing coin
        existing_coin.name = coin.name
        existing_coin.current_price = coin.current_price
        existing_coin.market_cap = coin.market_cap
        existing_coin.change_24h = coin.change_24h
        existing_coin.last_updated = coin.last_updated
    else:
        # Insert new coin
        new_coin = models.Coin(
            name=coin.name,
            symbol=coin.symbol,
            current_price=coin.current_price,
            market_cap=coin.market_cap,
            change_24h=coin.change_24h,
            last_updated=coin.last_updated
        )
        db.add(new_coin)
    # Note: Commit is handled in the background task after all operations

async def get_coins_ordered_by_market_cap(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    Fetches a list of coins ordered by market capitalization in descending order.

    Args:
        db (AsyncSession): The database session.
        skip (int, optional): Number of records to skip for pagination. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        List[models.Coin]: A list of Coin objects ordered by market cap.
    """
    query = select(models.Coin).order_by(desc(models.Coin.market_cap)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
