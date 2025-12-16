"""
Wallet Management Endpoints
Web3 wallet integration and transaction management
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.wallet import (
    WalletCreate, WalletResponse, TransactionCreate, TransactionResponse,
    SignMessageRequest, SignMessageResponse, GasEstimate, WalletBalance
)
from app.services.wallet import wallet_service
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/sign-message", response_model=SignMessageResponse)
async def request_sign_message(
    request: SignMessageRequest
):
    """
    Get a message to sign for wallet verification
    
    The message includes a nonce and expires in 10 minutes.
    Sign this message with your wallet to prove ownership.
    """
    if not wallet_service.is_valid_address(request.address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Ethereum address"
        )
    
    return wallet_service.generate_sign_message(request.address)


@router.post("/bind", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def bind_wallet(
    wallet_create: WalletCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bind an external wallet to your account
    
    Steps:
    1. Call /sign-message to get a message
    2. Sign the message with your wallet (MetaMask, etc.)
    3. Submit the signature here
    """
    wallet = await wallet_service.bind_wallet(db, current_user.id, wallet_create)
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature or wallet already bound"
        )
    
    await db.commit()
    return wallet


@router.get("", response_model=List[WalletResponse])
async def get_wallets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all bound wallets
    """
    return await wallet_service.get_user_wallets(db, current_user.id)


@router.get("/balances", response_model=List[WalletBalance])
async def get_balances(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated balances across all wallets
    """
    return await wallet_service.get_wallet_balances(db, current_user.id)


@router.get("/estimate-gas", response_model=GasEstimate)
async def estimate_gas(
    to_address: str = Query(..., description="Destination address"),
    amount: float = Query(..., gt=0, description="Amount to transfer"),
    currency: str = Query("ETH", description="Currency to transfer")
):
    """
    Estimate gas fees for a transaction
    """
    if not wallet_service.is_valid_address(to_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid destination address"
        )
    
    from decimal import Decimal
    return await wallet_service.estimate_gas(to_address, Decimal(str(amount)), currency)


@router.post("/withdraw", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_withdrawal(
    wallet_id: UUID,
    tx_create: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a withdrawal request
    
    Withdrawals are processed after confirmations
    """
    if not wallet_service.is_valid_address(tx_create.to_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid destination address"
        )
    
    tx = await wallet_service.create_withdrawal(
        db, current_user.id, wallet_id, tx_create
    )
    
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance or wallet not found"
        )
    
    await db.commit()
    return tx


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transaction history
    """
    return await wallet_service.get_transactions(db, current_user.id, limit)

