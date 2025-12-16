"""
User Schemas
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "trader@example.com",
                "password": "securepassword123"
            }
        }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    eth_address: Optional[str] = None
    is_active: bool
    is_verified: bool
    kyc_level: str
    daily_trade_limit: float
    daily_withdrawal_limit: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str = "access"


class WalletBindRequest(BaseModel):
    """Request to bind an Ethereum wallet"""
    address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    signature: str
    message: str

