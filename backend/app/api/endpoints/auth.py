"""
Authentication Endpoints
User registration, login, and wallet binding
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token, WalletBindRequest
from app.services.auth import AuthService
from app.api.deps import get_current_user

router = APIRouter()
auth_service = AuthService()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    """
    # Check if email exists
    result = await db.execute(
        select(User).where(User.email == user_create.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await auth_service.create_user(db, user_create)
    await db.commit()
    
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate and receive access token
    """
    user = await auth_service.authenticate_user(
        db, credentials.email, credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return auth_service.create_access_token(user.id)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile
    """
    return current_user


@router.post("/bind-wallet", response_model=UserResponse)
async def bind_wallet(
    request: WalletBindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bind Ethereum wallet to account
    Requires signature verification
    """
    # Verify wallet not already bound
    if current_user.eth_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet already bound to account"
        )
    
    # Verify signature and bind
    success = await auth_service.bind_wallet(
        db,
        current_user.id,
        request.address,
        request.signature,
        request.message
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature or address"
        )
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token
    """
    return auth_service.create_access_token(current_user.id)

