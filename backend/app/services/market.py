"""
Market Data Service
Real-time market data aggregation and distribution
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from collections import defaultdict
import random

import redis.asyncio as redis
import httpx

from app.schemas.market import MarketData, Ticker, Candle
from app.config import settings


class MarketDataService:
    """
    Market data service providing:
    - Real-time price feeds
    - 24hr ticker statistics
    - OHLCV candlestick data
    - Order book snapshots
    """
    
    # Supported trading pairs
    TRADING_PAIRS = [
        "BTC-USDT", "ETH-USDT", "SOL-USDT", "AVAX-USDT",
        "MATIC-USDT", "LINK-USDT", "UNI-USDT", "AAVE-USDT"
    ]
    
    def __init__(self):
        self._price_cache: Dict[str, MarketData] = {}
        self._candle_cache: Dict[str, List[Candle]] = defaultdict(list)
        self._ticker_cache: Dict[str, Ticker] = {}
        self._running = False
    
    async def start(self, redis_client: redis.Redis) -> None:
        """Start market data feeds"""
        self._running = True
        self._redis = redis_client
        
        # Initialize with simulated data
        await self._initialize_prices()
        
        # Start price update loop
        asyncio.create_task(self._price_update_loop())
    
    async def stop(self) -> None:
        """Stop market data feeds"""
        self._running = False
    
    async def _initialize_prices(self) -> None:
        """Initialize with base prices"""
        base_prices = {
            "BTC-USDT": Decimal("42500.00"),
            "ETH-USDT": Decimal("2250.00"),
            "SOL-USDT": Decimal("98.50"),
            "AVAX-USDT": Decimal("35.20"),
            "MATIC-USDT": Decimal("0.85"),
            "LINK-USDT": Decimal("14.30"),
            "UNI-USDT": Decimal("6.15"),
            "AAVE-USDT": Decimal("92.40"),
        }
        
        now = datetime.utcnow()
        
        for symbol, price in base_prices.items():
            spread = price * Decimal("0.0005")  # 0.05% spread
            
            self._price_cache[symbol] = MarketData(
                symbol=symbol,
                bid=price - spread,
                ask=price + spread,
                last=price,
                volume_24h=Decimal(random.uniform(1000000, 50000000)),
                high_24h=price * Decimal("1.03"),
                low_24h=price * Decimal("0.97"),
                change_24h=price * Decimal(str(random.uniform(-0.05, 0.05))),
                change_percent_24h=Decimal(str(random.uniform(-5, 5))),
                timestamp=now
            )
            
            # Initialize ticker
            self._ticker_cache[symbol] = Ticker(
                symbol=symbol,
                price_change=self._price_cache[symbol].change_24h,
                price_change_percent=self._price_cache[symbol].change_percent_24h,
                weighted_avg_price=price,
                last_price=price,
                last_quantity=Decimal(str(random.uniform(0.1, 10))),
                bid_price=price - spread,
                bid_quantity=Decimal(str(random.uniform(10, 100))),
                ask_price=price + spread,
                ask_quantity=Decimal(str(random.uniform(10, 100))),
                open_price=price * Decimal("0.99"),
                high_price=price * Decimal("1.03"),
                low_price=price * Decimal("0.97"),
                volume=self._price_cache[symbol].volume_24h,
                quote_volume=self._price_cache[symbol].volume_24h * price,
                open_time=now - timedelta(hours=24),
                close_time=now,
                trade_count=random.randint(50000, 500000)
            )
    
    async def _price_update_loop(self) -> None:
        """Continuous price update simulation"""
        while self._running:
            try:
                await self._update_prices()
                await asyncio.sleep(0.1)  # 100ms update interval
            except Exception as e:
                print(f"Price update error: {e}")
                await asyncio.sleep(1)
    
    async def _update_prices(self) -> None:
        """Simulate price movements"""
        now = datetime.utcnow()
        
        for symbol in self.TRADING_PAIRS:
            if symbol not in self._price_cache:
                continue
            
            current = self._price_cache[symbol]
            
            # Random walk with mean reversion
            change_percent = Decimal(str(random.gauss(0, 0.0002)))  # 0.02% std dev
            new_price = current.last * (1 + change_percent)
            
            spread = new_price * Decimal("0.0005")
            
            # Update cache
            self._price_cache[symbol] = MarketData(
                symbol=symbol,
                bid=new_price - spread,
                ask=new_price + spread,
                last=new_price,
                volume_24h=current.volume_24h + Decimal(str(random.uniform(100, 1000))),
                high_24h=max(current.high_24h, new_price),
                low_24h=min(current.low_24h, new_price),
                change_24h=new_price - self._ticker_cache[symbol].open_price,
                change_percent_24h=((new_price / self._ticker_cache[symbol].open_price) - 1) * 100,
                timestamp=now
            )
            
            # Publish to Redis for WebSocket distribution
            if self._redis:
                await self._redis.publish(
                    f"prices:{symbol}",
                    f"{new_price}|{new_price - spread}|{new_price + spread}|{now.isoformat()}"
                )
    
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get current market data for symbol"""
        return self._price_cache.get(symbol.upper())
    
    async def get_all_market_data(self) -> List[MarketData]:
        """Get market data for all symbols"""
        return list(self._price_cache.values())
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get 24hr ticker for symbol"""
        return self._ticker_cache.get(symbol.upper())
    
    async def get_all_tickers(self) -> List[Ticker]:
        """Get 24hr tickers for all symbols"""
        return list(self._ticker_cache.values())
    
    async def get_candles(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 100
    ) -> List[Candle]:
        """
        Get OHLCV candlestick data
        Generates simulated historical data
        """
        symbol = symbol.upper()
        
        if symbol not in self._price_cache:
            return []
        
        current_price = self._price_cache[symbol].last
        candles = []
        
        # Generate historical candles
        interval_minutes = {
            "1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440
        }.get(interval, 1)
        
        now = datetime.utcnow()
        
        for i in range(limit, 0, -1):
            open_time = now - timedelta(minutes=i * interval_minutes)
            close_time = open_time + timedelta(minutes=interval_minutes)
            
            # Generate realistic OHLCV
            volatility = current_price * Decimal("0.002")
            open_price = current_price * (1 + Decimal(str(random.gauss(0, 0.001))))
            high = open_price + volatility * Decimal(str(random.random()))
            low = open_price - volatility * Decimal(str(random.random()))
            close = open_price * (1 + Decimal(str(random.gauss(0, 0.001))))
            volume = Decimal(str(random.uniform(10000, 100000)))
            
            candles.append(Candle(
                symbol=symbol,
                interval=interval,
                open_time=open_time,
                open=open_price,
                high=max(high, open_price, close),
                low=min(low, open_price, close),
                close=close,
                volume=volume,
                close_time=close_time,
                quote_volume=volume * close,
                trade_count=random.randint(100, 1000)
            ))
        
        return candles
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent trades for symbol"""
        symbol = symbol.upper()
        
        if symbol not in self._price_cache:
            return []
        
        current = self._price_cache[symbol]
        trades = []
        now = datetime.utcnow()
        
        for i in range(limit):
            price = current.last * (1 + Decimal(str(random.gauss(0, 0.0001))))
            trades.append({
                "trade_id": 1000000 - i,
                "price": str(price),
                "quantity": str(Decimal(str(random.uniform(0.01, 10)))),
                "time": (now - timedelta(seconds=i * 2)).isoformat(),
                "is_buyer_maker": random.choice([True, False])
            })
        
        return trades


# Singleton instance
market_service = MarketDataService()

