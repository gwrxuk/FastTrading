"""
Order Schemas
Validated order data structures for trading engine
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LIMIT = "stop_limit"
    STOP_MARKET = "stop_market"


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TimeInForce(str, Enum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class OrderCreate(BaseModel):
    """Order creation request"""
    symbol: str = Field(..., min_length=3, max_length=20, description="Trading pair e.g. ETH-USDT")
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(..., gt=0, description="Order quantity")
    price: Optional[Decimal] = Field(None, gt=0, description="Limit price (required for limit orders)")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="Stop trigger price")
    time_in_force: TimeInForce = TimeInForce.GTC
    client_order_id: Optional[str] = Field(None, max_length=64)
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v = v.upper()
        if '-' not in v:
            raise ValueError('Symbol must be in format BASE-QUOTE (e.g., ETH-USDT)')
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price_for_limit(cls, v, info):
        values = info.data
        if values.get('order_type') == OrderType.LIMIT and v is None:
            raise ValueError('Price is required for limit orders')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "ETH-USDT",
                "side": "buy",
                "order_type": "limit",
                "quantity": "1.5",
                "price": "2500.00",
                "time_in_force": "gtc"
            }
        }


class OrderResponse(BaseModel):
    """Order response"""
    id: UUID
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    time_in_force: TimeInForce
    price: Optional[Decimal]
    stop_price: Optional[Decimal]
    quantity: Decimal
    filled_quantity: Decimal
    remaining_quantity: Decimal
    average_fill_price: Optional[Decimal]
    commission: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderBookEntry(BaseModel):
    """Single price level in order book"""
    price: Decimal
    quantity: Decimal
    order_count: int


class OrderBookResponse(BaseModel):
    """Full order book response"""
    symbol: str
    bids: List[OrderBookEntry]  # Buy orders (descending price)
    asks: List[OrderBookEntry]  # Sell orders (ascending price)
    timestamp: datetime
    sequence: int


class CancelOrderRequest(BaseModel):
    """Cancel order request"""
    order_id: Optional[UUID] = None
    client_order_id: Optional[str] = None
    
    @field_validator('client_order_id')
    @classmethod
    def validate_one_id_provided(cls, v, info):
        values = info.data
        if not v and not values.get('order_id'):
            raise ValueError('Either order_id or client_order_id must be provided')
        return v

