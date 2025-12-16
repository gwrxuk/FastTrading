"""
Market Data Schemas
Real-time market information structures
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class Ticker(BaseModel):
    """24hr ticker statistics"""
    symbol: str
    price_change: Decimal
    price_change_percent: Decimal
    weighted_avg_price: Decimal
    last_price: Decimal
    last_quantity: Decimal
    bid_price: Decimal
    bid_quantity: Decimal
    ask_price: Decimal
    ask_quantity: Decimal
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    volume: Decimal
    quote_volume: Decimal
    open_time: datetime
    close_time: datetime
    trade_count: int


class MarketData(BaseModel):
    """Real-time market data snapshot"""
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    change_24h: Decimal
    change_percent_24h: Decimal
    timestamp: datetime


class Candle(BaseModel):
    """OHLCV candlestick data"""
    symbol: str
    interval: str  # 1m, 5m, 15m, 1h, 4h, 1d
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: datetime
    quote_volume: Decimal
    trade_count: int


class CandleRequest(BaseModel):
    """Candlestick data request"""
    symbol: str
    interval: str = "1m"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 500


class DepthUpdate(BaseModel):
    """Order book depth update"""
    symbol: str
    bids: List[List[Decimal]]  # [[price, quantity], ...]
    asks: List[List[Decimal]]
    first_update_id: int
    last_update_id: int
    timestamp: datetime


class TradeUpdate(BaseModel):
    """Real-time trade update"""
    symbol: str
    trade_id: int
    price: Decimal
    quantity: Decimal
    buyer_order_id: str
    seller_order_id: str
    timestamp: datetime
    is_buyer_maker: bool

