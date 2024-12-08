"""
# app/services/coingecko.py
import httpx

async def fetch_coin_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
"""

# app/services/coingecko.py
import httpx
from typing import List, Dict

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 100,
    "page": 1,
    "sparkline": False,
}

async def fetch_coin_data() -> List[Dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(COINGECKO_API_URL, params=PARAMS)
        response.raise_for_status()
        return response.json()
