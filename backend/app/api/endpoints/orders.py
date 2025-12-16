"""
Order Management Endpoints
High-performance order placement and management
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import get_db
from app.models.user import User
from app.models.order import OrderStatus
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderBookResponse,
    CancelOrderRequest
)
from app.services.trading import TradingEngine
from app.api.deps import get_current_user, get_redis_client, trading_rate_limit

router = APIRouter()
trading_engine = TradingEngine()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    order_create: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    _: None = Depends(trading_rate_limit)
):
    """
    Place a new order
    
    Supports:
    - Market orders (immediate execution)
    - Limit orders (price-time priority matching)
    - Stop orders (triggered at stop price)
    
    Rate limited to 10 orders per second
    """
    try:
        order, trades = await trading_engine.place_order(
            db, redis_client, current_user.id, order_create
        )
        await db.commit()
        
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[OrderResponse])
async def get_orders(
    symbol: Optional[str] = Query(None, description="Filter by trading pair"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's orders with optional filters
    """
    orders = await trading_engine.get_user_orders(
        db, current_user.id, symbol, status, limit
    )
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific order by ID
    """
    from sqlalchemy import select
    from app.models.order import Order
    
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an open order
    """
    success = await trading_engine.cancel_order(db, order_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or already filled/cancelled"
        )
    
    await db.commit()


@router.post("/cancel-all", status_code=status.HTTP_200_OK)
async def cancel_all_orders(
    symbol: Optional[str] = Query(None, description="Cancel only for this symbol"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel all open orders
    """
    from sqlalchemy import select
    from app.models.order import Order
    
    query = select(Order).where(
        Order.user_id == current_user.id,
        Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL])
    )
    
    if symbol:
        query = query.where(Order.symbol == symbol.upper())
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    cancelled_count = 0
    for order in orders:
        if await trading_engine.cancel_order(db, order.id, current_user.id):
            cancelled_count += 1
    
    await db.commit()
    
    return {"cancelled_count": cancelled_count}


@router.get("/book/{symbol}", response_model=OrderBookResponse)
async def get_order_book(
    symbol: str,
    levels: int = Query(20, ge=1, le=100, description="Number of price levels")
):
    """
    Get order book depth for a symbol
    
    Returns bid and ask levels sorted by price
    - Bids: descending (best bid first)
    - Asks: ascending (best ask first)
    """
    from datetime import datetime
    
    symbol = symbol.upper()
    bids, asks, sequence = await trading_engine.get_order_book(symbol, levels)
    
    return OrderBookResponse(
        symbol=symbol,
        bids=bids,
        asks=asks,
        timestamp=datetime.utcnow(),
        sequence=sequence
    )

