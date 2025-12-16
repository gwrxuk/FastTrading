"""
Wallet Schemas
Web3 wallet and transaction structures
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum


class WalletType(str, Enum):
    HOT = "hot"
    COLD = "cold"
    USER = "user"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTERNAL = "internal"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class WalletCreate(BaseModel):
    """Bind external wallet request"""
    address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    chain: str = "ethereum"
    currency: str = "ETH"
    signature: str  # Signed message proving ownership
    message: str  # Original message that was signed


class WalletResponse(BaseModel):
    """Wallet information"""
    id: UUID
    address: str
    chain: str
    currency: str
    balance: Decimal
    locked_balance: Decimal
    is_verified: str
    wallet_type: WalletType
    created_at: datetime
    
    class Config:
        from_attributes = True


class WalletBalance(BaseModel):
    """Balance for a specific currency"""
    currency: str
    available: Decimal
    locked: Decimal
    total: Decimal


class TransactionCreate(BaseModel):
    """Withdrawal request"""
    to_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    currency: str
    amount: Decimal = Field(..., gt=0)
    chain: str = "ethereum"


class TransactionResponse(BaseModel):
    """Transaction status"""
    id: UUID
    tx_type: TransactionType
    status: TransactionStatus
    tx_hash: Optional[str]
    from_address: str
    to_address: str
    currency: str
    amount: Decimal
    gas_used: Optional[int]
    block_number: Optional[int]
    confirmations: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SignMessageRequest(BaseModel):
    """Request message to sign for wallet verification"""
    address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")


class SignMessageResponse(BaseModel):
    """Message to be signed by wallet"""
    message: str
    nonce: str
    expires_at: datetime


class GasEstimate(BaseModel):
    """Gas estimation for transaction"""
    gas_limit: int
    gas_price_gwei: Decimal
    estimated_fee_eth: Decimal
    estimated_fee_usd: Decimal

