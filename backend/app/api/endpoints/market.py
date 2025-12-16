"""
Market Data Endpoints
Real-time market information
"""
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.market import MarketData, Ticker, Candle
from app.services.market import market_service

router = APIRouter()


@router.get("/price/{symbol}", response_model=MarketData)
async def get_price(symbol: str):
    """
    Get current market data for a symbol
    
    Includes:
    - Bid/Ask prices
    - Last trade price
    - 24h statistics
    """
    data = await market_service.get_market_data(symbol)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol.upper()} not found"
        )
    
    return data


@router.get("/prices", response_model=List[MarketData])
async def get_all_prices():
    """
    Get market data for all trading pairs
    """
    return await market_service.get_all_market_data()


@router.get("/ticker/{symbol}", response_model=Ticker)
async def get_ticker(symbol: str):
    """
    Get 24hr ticker statistics for a symbol
    """
    ticker = await market_service.get_ticker(symbol)
    
    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol.upper()} not found"
        )
    
    return ticker


@router.get("/tickers", response_model=List[Ticker])
async def get_all_tickers():
    """
    Get 24hr ticker statistics for all symbols
    """
    return await market_service.get_all_tickers()


@router.get("/candles/{symbol}", response_model=List[Candle])
async def get_candles(
    symbol: str,
    interval: str = Query("1m", regex="^(1m|5m|15m|1h|4h|1d)$"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get OHLCV candlestick data
    
    Intervals:
    - 1m, 5m, 15m: Minute candles
    - 1h, 4h: Hour candles
    - 1d: Daily candles
    """
    candles = await market_service.get_candles(symbol, interval, limit)
    
    if not candles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol.upper()} not found"
        )
    
    return candles


@router.get("/symbols")
async def get_symbols():
    """
    Get list of all supported trading pairs
    """
    return {
        "symbols": market_service.TRADING_PAIRS,
        "count": len(market_service.TRADING_PAIRS)
    }

