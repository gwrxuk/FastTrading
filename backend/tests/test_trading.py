"""
Trading Engine Tests
Comprehensive test suite for order matching and execution
"""
import pytest
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from httpx import AsyncClient

from app.main import app
from app.models.order import OrderSide, OrderType, OrderStatus
from app.services.trading import TradingEngine, OrderBook


@pytest.fixture
def trading_engine():
    """Create a fresh trading engine for each test"""
    return TradingEngine()


@pytest.fixture
def order_book():
    """Create a fresh order book for each test"""
    return OrderBook("ETH-USDT")


class TestOrderBook:
    """Test order book operations"""
    
    @pytest.mark.asyncio
    async def test_add_order_to_empty_book(self, order_book):
        """Test adding first order to empty book"""
        from app.services.trading import OrderEntry
        from datetime import datetime
        
        entry = OrderEntry(
            priority=-2000.0,  # Buy at $2000
            timestamp=datetime.utcnow().timestamp(),
            order_id=uuid4(),
            price=Decimal("2000"),
            quantity=Decimal("1"),
            user_id=uuid4()
        )
        
        await order_book.add_order(entry, OrderSide.BUY)
        
        bids, asks = await order_book.get_depth(10)
        assert len(bids) == 1
        assert len(asks) == 0
        assert bids[0].price == Decimal("2000")
    
    @pytest.mark.asyncio
    async def test_best_bid_ask(self, order_book):
        """Test getting best bid and ask"""
        from app.services.trading import OrderEntry
        from datetime import datetime
        
        # Add buy order
        buy_entry = OrderEntry(
            priority=-2000.0,
            timestamp=datetime.utcnow().timestamp(),
            order_id=uuid4(),
            price=Decimal("2000"),
            quantity=Decimal("1"),
            user_id=uuid4()
        )
        await order_book.add_order(buy_entry, OrderSide.BUY)
        
        # Add sell order
        sell_entry = OrderEntry(
            priority=2050.0,
            timestamp=datetime.utcnow().timestamp(),
            order_id=uuid4(),
            price=Decimal("2050"),
            quantity=Decimal("1"),
            user_id=uuid4()
        )
        await order_book.add_order(sell_entry, OrderSide.SELL)
        
        best_bid = await order_book.get_best_bid()
        best_ask = await order_book.get_best_ask()
        
        assert best_bid is not None
        assert best_bid.price == Decimal("2000")
        assert best_ask is not None
        assert best_ask.price == Decimal("2050")
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, order_book):
        """Test cancelling an order"""
        from app.services.trading import OrderEntry
        from datetime import datetime
        
        order_id = uuid4()
        entry = OrderEntry(
            priority=-2000.0,
            timestamp=datetime.utcnow().timestamp(),
            order_id=order_id,
            price=Decimal("2000"),
            quantity=Decimal("1"),
            user_id=uuid4()
        )
        
        await order_book.add_order(entry, OrderSide.BUY)
        
        result = await order_book.cancel_order(order_id)
        assert result is True
        
        bids, _ = await order_book.get_depth(10)
        assert len(bids) == 0


class TestTradingEngine:
    """Test trading engine operations"""
    
    def test_get_order_book_creates_new(self, trading_engine):
        """Test that getting non-existent order book creates it"""
        from common import Symbol
        
        book = trading_engine._get_order_book("ETH-USDT")
        assert book is not None
        assert book.symbol == "ETH-USDT"
    
    @pytest.mark.asyncio
    async def test_get_order_book_depth(self, trading_engine):
        """Test getting order book depth"""
        bids, asks, sequence = await trading_engine.get_order_book("ETH-USDT", 20)
        
        assert isinstance(bids, list)
        assert isinstance(asks, list)
        assert isinstance(sequence, int)


class TestAPIEndpoints:
    """Test API endpoint integration"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """Create async HTTP client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_symbols(self, client):
        """Test getting trading symbols"""
        response = await client.get("/api/v1/market/symbols")
        assert response.status_code == 200
        data = response.json()
        assert "symbols" in data
        assert isinstance(data["symbols"], list)


class TestOrderValidation:
    """Test order validation logic"""
    
    def test_valid_limit_order(self):
        """Test valid limit order passes validation"""
        from app.schemas.order import OrderCreate
        
        order = OrderCreate(
            symbol="ETH-USDT",
            side="buy",
            order_type="limit",
            quantity=Decimal("1"),
            price=Decimal("2000"),
            time_in_force="gtc"
        )
        
        assert order.symbol == "ETH-USDT"
        assert order.price == Decimal("2000")
    
    def test_limit_order_requires_price(self):
        """Test that limit order without price fails validation"""
        from app.schemas.order import OrderCreate
        import pydantic
        
        with pytest.raises(pydantic.ValidationError):
            OrderCreate(
                symbol="ETH-USDT",
                side="buy",
                order_type="limit",
                quantity=Decimal("1"),
                # Missing price - should fail
                time_in_force="gtc"
            )
    
    def test_market_order_no_price_needed(self):
        """Test market order doesn't require price"""
        from app.schemas.order import OrderCreate
        
        order = OrderCreate(
            symbol="ETH-USDT",
            side="buy",
            order_type="market",
            quantity=Decimal("1"),
            time_in_force="ioc"
        )
        
        assert order.price is None

