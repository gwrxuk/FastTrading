"""
Trade Model
Immutable trade records for audit and compliance
"""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base


class Trade(Base):
    """
    Trade execution record
    Immutable after creation for audit compliance
    """
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(BigInteger, unique=True, nullable=False, index=True)
    
    # References
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    
    # Counterparty (for matching engine)
    counterparty_order_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Trading pair
    symbol = Column(String(20), nullable=False, index=True)
    
    # Execution details
    side = Column(String(4), nullable=False)  # buy/sell
    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    quote_quantity = Column(Numeric(20, 8), nullable=False)  # price * quantity
    
    # Fees
    commission = Column(Numeric(20, 8), nullable=False)
    commission_asset = Column(String(10), nullable=False)
    
    # Maker/Taker
    is_maker = Column(String(10), nullable=False)
    
    # Timestamps (nanosecond precision for HFT)
    executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Blockchain settlement (if applicable)
    tx_hash = Column(String(66), nullable=True, index=True)
    block_number = Column(BigInteger, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    order = relationship("Order", back_populates="trades")
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_trades_symbol_time', 'symbol', 'executed_at'),
        Index('ix_trades_user_time', 'user_id', 'executed_at'),
        Index('ix_trades_order', 'order_id'),
    )
    
    def __repr__(self):
        return f"<Trade {self.trade_id} {self.symbol} {self.quantity}@{self.price}>"

