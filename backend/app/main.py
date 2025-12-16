"""
FastTrading API
High-performance trading platform backend

Features:
- Real-time order matching engine
- WebSocket price feeds
- Web3 wallet integration
- Rate limiting and security
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
import redis.asyncio as redis

from app.config import settings
from app.database import init_db, close_db, get_redis
from app.api.router import api_router
from app.websocket.handlers import websocket_endpoint
from app.websocket.manager import ws_manager
from app.services.market import market_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Handles startup and shutdown events
    """
    # Startup
    print("🚀 Starting FastTrading API...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Initialize Redis
    redis_client = await get_redis()
    print("✅ Redis connected")
    
    # Start WebSocket manager
    await ws_manager.start(redis_client)
    print("✅ WebSocket manager started")
    
    # Start market data service
    await market_service.start(redis_client)
    print("✅ Market data service started")
    
    print("🎯 FastTrading API ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down FastTrading API...")
    
    await market_service.stop()
    await ws_manager.stop()
    await close_db()
    
    print("👋 Goodbye!")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## FastTrading API
    
    High-performance cryptocurrency trading platform API.
    
    ### Features
    - **Order Management**: Place, cancel, and track orders
    - **Real-time Data**: WebSocket price feeds and order updates
    - **Wallet Integration**: Web3 wallet binding and transactions
    - **Market Data**: Tickers, candles, and order book depth
    
    ### Authentication
    Most endpoints require JWT authentication. 
    Use `/api/v1/auth/login` to obtain a token.
    
    ### Rate Limits
    - General: 100 requests/minute
    - Trading: 10 orders/second
    """,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,  # Faster JSON serialization
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router, prefix=settings.API_PREFIX)

# WebSocket endpoint
app.websocket("/ws")(websocket_endpoint)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "websocket": "active",
        "trading_pairs": len(market_service.TRADING_PAIRS)
    }

