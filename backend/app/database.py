"""
Database Configuration
High-performance async PostgreSQL connection pooling
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import redis.asyncio as redis

from app.config import settings


# Create async engine with optimized settings
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.DEBUG,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session():
    """
    Async context manager for database sessions
    Handles commit/rollback automatically
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI endpoints
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Redis connection pool
redis_pool = None


async def get_redis() -> redis.Redis:
    """
    Get Redis connection from pool
    """
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=100,
            decode_responses=True,
        )
    return redis.Redis(connection_pool=redis_pool)


async def init_db():
    """
    Initialize database tables
    """
    from app.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close all database connections
    """
    await engine.dispose()
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()

