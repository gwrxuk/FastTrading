"""
Wallet and Transaction Models
Web3 integration for crypto wallet management
"""
from enum import Enum
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index, Enum as SQLEnum, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base, TimestampMixin


class WalletType(str, Enum):
    HOT = "hot"  # Platform managed
    COLD = "cold"  # Cold storage
    USER = "user"  # User's external wallet


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTERNAL = "internal"
    FEE = "fee"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Wallet(Base, TimestampMixin):
    """
    Crypto wallet management
    Supports both custodial and non-custodial patterns
    """
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Wallet details
    wallet_type = Column(SQLEnum(WalletType), nullable=False)
    address = Column(String(42), unique=True, nullable=False, index=True)
    chain = Column(String(20), nullable=False, default="ethereum")  # ethereum, polygon, etc.
    
    # Balance tracking (cached from blockchain)
    currency = Column(String(10), nullable=False)  # ETH, USDT, etc.
    balance = Column(Numeric(30, 18), default=0, nullable=False)  # 18 decimals for ETH
    locked_balance = Column(Numeric(30, 18), default=0, nullable=False)
    
    # Nonce tracking for transaction signing
    nonce = Column(BigInteger, default=0, nullable=False)
    
    # Verification
    is_verified = Column(String(10), default="pending")
    signature_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="wallets")
    transactions = relationship("Transaction", back_populates="wallet", lazy="dynamic")
    
    __table_args__ = (
        Index('ix_wallets_user_currency', 'user_id', 'currency'),
        Index('ix_wallets_chain_address', 'chain', 'address'),
    )
    
    def __repr__(self):
        return f"<Wallet {self.address[:8]}...{self.address[-4:]} {self.currency}>"


class Transaction(Base, TimestampMixin):
    """
    Blockchain transaction tracking
    Full lifecycle from creation to confirmation
    """
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Transaction details
    tx_type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False, index=True)
    
    # Blockchain data
    tx_hash = Column(String(66), unique=True, nullable=True, index=True)
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42), nullable=False)
    
    # Amount
    currency = Column(String(10), nullable=False)
    amount = Column(Numeric(30, 18), nullable=False)
    
    # Gas tracking
    gas_limit = Column(BigInteger, nullable=True)
    gas_price = Column(Numeric(30, 18), nullable=True)
    gas_used = Column(BigInteger, nullable=True)
    
    # Confirmation tracking
    block_number = Column(BigInteger, nullable=True)
    confirmations = Column(BigInteger, default=0, nullable=False)
    required_confirmations = Column(BigInteger, default=12, nullable=False)
    
    # Raw transaction data (for signing)
    raw_tx = Column(Text, nullable=True)
    signed_tx = Column(Text, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(BigInteger, default=0, nullable=False)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
    
    __table_args__ = (
        Index('ix_transactions_status_type', 'status', 'tx_type'),
        Index('ix_transactions_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Transaction {self.tx_hash or 'pending'} {self.amount} {self.currency}>"

