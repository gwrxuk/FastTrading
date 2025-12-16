"""
Authentication Service
Secure JWT-based authentication with Web3 wallet binding
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from eth_account.messages import encode_defunct
from web3 import Web3

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, Token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service handling:
    - Password hashing and verification
    - JWT token generation and validation
    - Ethereum wallet signature verification
    """
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        user_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> Token:
        """
        Create JWT access token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=int(expires_delta.total_seconds())
        )
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and validate JWT token
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def verify_eth_signature(address: str, message: str, signature: str) -> bool:
        """
        Verify Ethereum wallet signature
        Used for wallet binding and message signing verification
        """
        try:
            w3 = Web3()
            message_hash = encode_defunct(text=message)
            recovered_address = w3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            return recovered_address.lower() == address.lower()
        except Exception:
            return False
    
    @staticmethod
    def generate_sign_message(address: str, nonce: str) -> str:
        """
        Generate message for wallet signature verification
        """
        return (
            f"Sign this message to verify your wallet ownership.\n\n"
            f"Wallet: {address}\n"
            f"Nonce: {nonce}\n"
            f"Timestamp: {datetime.utcnow().isoformat()}\n\n"
            f"This signature will not trigger any blockchain transaction."
        )
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        return user
    
    async def create_user(
        self,
        db: AsyncSession,
        user_create: UserCreate
    ) -> User:
        """
        Create new user account
        """
        hashed_password = self.hash_password(user_create.password)
        
        user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        
        return user
    
    async def bind_wallet(
        self,
        db: AsyncSession,
        user_id: UUID,
        address: str,
        signature: str,
        message: str
    ) -> bool:
        """
        Bind Ethereum wallet to user account
        Verifies ownership via signature
        """
        # Verify signature
        if not self.verify_eth_signature(address, message, signature):
            return False
        
        # Update user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.eth_address = address.lower()
        await db.flush()
        
        return True
    
    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_api_key(
        self,
        db: AsyncSession,
        api_key: str
    ) -> Optional[User]:
        """Get user by API key for programmatic access"""
        result = await db.execute(
            select(User).where(User.api_key == api_key)
        )
        return result.scalar_one_or_none()

