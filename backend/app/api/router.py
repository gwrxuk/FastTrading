"""
API Router
Aggregates all API endpoints
"""
from fastapi import APIRouter

from app.api.endpoints import auth, orders, trades, wallets, market

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(trades.router, prefix="/trades", tags=["Trades"])
api_router.include_router(wallets.router, prefix="/wallets", tags=["Wallets"])
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])

