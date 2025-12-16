"""
Order Models
High-performance order management for trading engine
"""
from enum import Enum
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index, Enum as SQLEnum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base, TimestampMixin


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
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    GTC = "gtc"  # Good Till Cancel
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    GTD = "gtd"  # Good Till Date


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_order_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Trading pair
    symbol = Column(String(20), nullable=False, index=True)  # e.g., "ETH-USDT"
    
    # Order details
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    time_in_force = Column(SQLEnum(TimeInForce), default=TimeInForce.GTC, nullable=False)
    
    # Pricing (using Numeric for precision - critical for financial data)
    price = Column(Numeric(20, 8), nullable=True)  # Null for market orders
    stop_price = Column(Numeric(20, 8), nullable=True)
    
    # Quantities
    quantity = Column(Numeric(20, 8), nullable=False)
    filled_quantity = Column(Numeric(20, 8), default=0, nullable=False)
    remaining_quantity = Column(Numeric(20, 8), nullable=False)
    
    # Execution details
    average_fill_price = Column(Numeric(20, 8), nullable=True)
    commission = Column(Numeric(20, 8), default=0, nullable=False)
    commission_asset = Column(String(10), nullable=True)
    
    # Sequence for order matching (nanosecond precision)
    sequence_number = Column(BigInteger, autoincrement=True, nullable=False, index=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    trades = relationship("Trade", back_populates="order", lazy="dynamic")
    
    # Critical indexes for trading engine performance
    __table_args__ = (
        Index('ix_orders_symbol_status', 'symbol', 'status'),
        Index('ix_orders_symbol_side_price', 'symbol', 'side', 'price'),
        Index('ix_orders_user_status', 'user_id', 'status'),
        Index('ix_orders_matching', 'symbol', 'status', 'side', 'price', 'sequence_number'),
    )
    
    def __repr__(self):
        return f"<Order {self.client_order_id} {self.symbol} {self.side.value} {self.quantity}@{self.price}>"


class OrderBook(Base):
    """
    Materialized order book for ultra-fast reads
    Updated via triggers or background workers
    """
    __tablename__ = "order_book"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    order_count = Column(BigInteger, default=1, nullable=False)
    
    __table_args__ = (
        Index('ix_orderbook_symbol_side', 'symbol', 'side'),
        Index('ix_orderbook_lookup', 'symbol', 'side', 'price'),
    )

