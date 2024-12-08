"""
# app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from . import crud, schemas
from .services.coingecko import fetch_coin_data
import asyncio

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "API is running..."}

@app.get("/coins", response_model=list[schemas.CoinDB])
def read_coins(db: Session = Depends(get_db)):
    return crud.get_coins(db)

# Background task to fetch and update data
@app.on_event("startup")
async def startup_event():
    async def update_coins():
        while True:
            print("Fetching coin data...")
            coins_data = await fetch_coin_data()
            db = SessionLocal()
            for coin in coins_data:
                coin_base = schemas.CoinBase(
                    name=coin["name"],
                    symbol=coin["symbol"],
                    current_price=coin["current_price"],
                    market_cap=coin["market_cap"],
                    change_24h=coin["price_change_percentage_24h"] if coin["price_change_percentage_24h"] is not None else 0.0
                )
                crud.upsert_coin(db, coin_base)
            db.close()
            print("Coin data updated.")
            await asyncio.sleep(300)  # Wait 5 minutes before next update
    asyncio.create_task(update_coins())
"""

# app/main.py

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, Base, get_db, AsyncSessionLocal
from . import crud, schemas
from .services.coingecko import fetch_coin_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Asynchronous table creation
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Create tables
    await create_tables()

    # Start background task
    asyncio.create_task(update_coins())

async def update_coins():
    while True:
        try:
            logger.info("Fetching coin data...")
            coins_data = await fetch_coin_data()
            logger.debug(f"Fetched coins data: {coins_data}")  # Debug log

            async with AsyncSessionLocal() as db:
                for coin in coins_data:
                    # Extract and parse 'last_updated'
                    last_updated_str = coin.get("last_updated")
                    logger.debug(f"Processing coin: {coin['symbol']}, last_updated: {last_updated_str}")

                    if last_updated_str:
                        # Replace 'Z' with '+00:00' to make it ISO 8601 compliant for fromisoformat
                        if last_updated_str.endswith('Z'):
                            last_updated_str = last_updated_str.replace('Z', '+00:00')
                        try:
                            # Parse the datetime string
                            last_updated = datetime.fromisoformat(last_updated_str)

                            # Convert to UTC and make it naive
                            if last_updated.tzinfo is not None:
                                last_updated = last_updated.astimezone(timezone.utc).replace(tzinfo=None)
                        except ValueError as ve:
                            logger.error(f"Error parsing last_updated for {coin['symbol']}: {ve}")
                            # Fallback to current UTC time, naive
                            last_updated = datetime.utcnow()
                    else:
                        # Fallback to current UTC time, naive
                        last_updated = datetime.utcnow()

                    # Create a CoinBase instance with timezone-naive last_updated
                    coin_base = schemas.CoinBase(
                        name=coin["name"],
                        symbol=coin["symbol"],
                        current_price=coin["current_price"],
                        market_cap=coin["market_cap"],
                        change_24h=coin["price_change_percentage_24h"] if coin.get("price_change_percentage_24h") is not None else 0.0,
                        last_updated=last_updated  # Ensure this is naive
                    )
                    logger.debug(f"Created CoinBase: {coin_base}")
                    
                    # Perform upsert operation
                    await crud.upsert_coin(db, coin_base)
                
                # Commit all changes after processing all coins
                await db.commit()
            
            logger.info("Coin data updated.")
        except Exception as e:
            logger.error(f"Error updating coins: {e}")
        await asyncio.sleep(300)  # Wait 5 minutes before next update

@app.get("/")
async def read_root():
    return {"message": "API is running..."}

@app.get("/coins", response_model=list[schemas.CoinDB])
async def read_coins(db: AsyncSession = Depends(get_db)):
    try:
        coins = await crud.get_coins(db)
        return coins
    except Exception as e:
        logger.error(f"Error fetching coins: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# New endpoint to list coins ordered by market cap
@app.get("/coins_by_marketcap", response_model=list[schemas.CoinDB])
async def read_coins_by_marketcap(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a list of coins ordered by market capitalization in descending order.

    Args:
        skip (int, optional): Number of records to skip for pagination. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        db (AsyncSession): Database session dependency.

    Returns:
        List[schemas.CoinDB]: A list of CoinDB models ordered by market cap.
    """
    try:
        coins = await crud.get_coins_ordered_by_market_cap(db, skip=skip, limit=limit)
        return coins
    except Exception as e:
        logger.error(f"Error fetching coins by market cap: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
