"""
Trade Schemas
Trade execution data structures
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class TradeResponse(BaseModel):
    """Trade execution record"""
    id: UUID
    trade_id: int
    symbol: str
    side: str
    price: Decimal
    quantity: Decimal
    quote_quantity: Decimal
    commission: Decimal
    commission_asset: str
    is_maker: str
    executed_at: datetime
    tx_hash: Optional[str]
    
    class Config:
        from_attributes = True


class TradeHistoryRequest(BaseModel):
    """Trade history query parameters"""
    symbol: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100


class TradeAggregation(BaseModel):
    """Aggregated trade statistics"""
    symbol: str
    period: str  # 1m, 5m, 1h, 1d
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal
    trade_count: int
    timestamp: datetime


class RecentTradesResponse(BaseModel):
    """Recent trades for a symbol"""
    symbol: str
    trades: List[TradeResponse]
    last_trade_id: int

