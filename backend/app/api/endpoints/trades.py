"""
Trade History Endpoints
Trade execution records and history
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.trade import Trade
from app.schemas.trade import TradeResponse, TradeAggregation
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[TradeResponse])
async def get_trades(
    symbol: Optional[str] = Query(None, description="Filter by trading pair"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's trade history
    
    Trades are immutable execution records for audit and compliance
    """
    query = select(Trade).where(Trade.user_id == current_user.id)
    
    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
    
    if start_time:
        query = query.where(Trade.executed_at >= start_time)
    
    if end_time:
        query = query.where(Trade.executed_at <= end_time)
    
    query = query.order_by(Trade.executed_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_trade_stats(
    symbol: Optional[str] = Query(None),
    period: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trading statistics for user
    """
    from datetime import timedelta
    from sqlalchemy import func
    from decimal import Decimal
    
    period_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    
    start_time = datetime.utcnow() - period_map[period]
    
    query = select(
        func.count(Trade.id).label("trade_count"),
        func.sum(Trade.quantity).label("total_quantity"),
        func.sum(Trade.quote_quantity).label("total_volume"),
        func.sum(Trade.commission).label("total_fees")
    ).where(
        Trade.user_id == current_user.id,
        Trade.executed_at >= start_time
    )
    
    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
    
    result = await db.execute(query)
    row = result.one()
    
    return {
        "period": period,
        "symbol": symbol,
        "trade_count": row.trade_count or 0,
        "total_quantity": str(row.total_quantity or Decimal(0)),
        "total_volume": str(row.total_volume or Decimal(0)),
        "total_fees": str(row.total_fees or Decimal(0))
    }


@router.get("/recent/{symbol}")
async def get_recent_trades(
    symbol: str,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get recent public trades for a symbol (no auth required)
    """
    from app.services.market import market_service
    
    trades = await market_service.get_recent_trades(symbol, limit)
    return trades

