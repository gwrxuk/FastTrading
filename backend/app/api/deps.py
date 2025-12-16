"""
API Dependencies
Reusable dependencies for route handlers
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import get_db, get_redis
from app.services.auth import AuthService
from app.models.user import User


security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user
    """
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = await auth_service.get_user_by_id(db, UUID(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns None if no token
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client for caching and pub/sub
    """
    return await get_redis()


class RateLimiter:
    """
    Rate limiting dependency
    Uses Redis for distributed rate limiting
    """
    
    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests
        self.window = window
    
    async def __call__(
        self,
        user: User = Depends(get_current_user),
        redis_client: redis.Redis = Depends(get_redis_client)
    ) -> None:
        key = f"ratelimit:{user.id}"
        
        count = await redis_client.incr(key)
        
        if count == 1:
            await redis_client.expire(key, self.window)
        
        if count > self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {self.window} seconds."
            )


# Pre-configured rate limiters
standard_rate_limit = RateLimiter(requests=100, window=60)
trading_rate_limit = RateLimiter(requests=10, window=1)  # 10 orders per second

