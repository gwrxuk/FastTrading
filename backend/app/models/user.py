"""
User Model
Secure user management for trading platform
"""
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Wallet binding
    eth_address = Column(String(42), unique=True, nullable=True, index=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    
    # Trading limits
    daily_trade_limit = Column(Numeric(20, 8), default=100000.0)
    daily_withdrawal_limit = Column(Numeric(20, 8), default=10000.0)
    
    # KYC
    kyc_level = Column(String(20), default="basic")
    
    # API keys
    api_key = Column(String(64), unique=True, nullable=True, index=True)
    api_secret = Column(String(128), nullable=True)
    
    # Relationships
    orders = relationship("Order", back_populates="user", lazy="dynamic")
    trades = relationship("Trade", back_populates="user", lazy="dynamic")
    wallets = relationship("Wallet", back_populates="user", lazy="dynamic")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_users_active_verified', 'is_active', 'is_verified'),
    )
    
    def __repr__(self):
        return f"<User {self.email}>"

