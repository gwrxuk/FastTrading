"""
Trading Engine
High-performance order matching engine with price-time priority
"""
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
from collections import defaultdict
from dataclasses import dataclass, field
import heapq

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import redis.asyncio as redis

from app.models.order import Order, OrderSide, OrderType, OrderStatus
from app.models.trade import Trade
from app.schemas.order import OrderCreate, OrderResponse, OrderBookEntry
from app.config import settings


@dataclass(order=True)
class OrderEntry:
    """
    Order entry for the matching engine
    Optimized for heap-based priority queue
    """
    priority: float  # Negative for buy (max-heap), positive for sell (min-heap)
    timestamp: float  # Secondary sort by time
    order_id: UUID = field(compare=False)
    price: Decimal = field(compare=False)
    quantity: Decimal = field(compare=False)
    user_id: UUID = field(compare=False)


class OrderBook:
    """
    In-memory order book for a single trading pair
    Implements price-time priority matching
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: List[OrderEntry] = []  # Max-heap (buy orders)
        self.asks: List[OrderEntry] = []  # Min-heap (sell orders)
        self.orders: dict[UUID, OrderEntry] = {}  # Quick lookup
        self._lock = asyncio.Lock()
        self.sequence = 0
    
    async def add_order(self, order: OrderEntry, side: OrderSide) -> None:
        """Add order to the book"""
        async with self._lock:
            self.orders[order.order_id] = order
            if side == OrderSide.BUY:
                heapq.heappush(self.bids, order)
            else:
                heapq.heappush(self.asks, order)
            self.sequence += 1
    
    async def cancel_order(self, order_id: UUID) -> bool:
        """Cancel order (marks as cancelled, cleaned up lazily)"""
        async with self._lock:
            if order_id in self.orders:
                del self.orders[order_id]
                return True
            return False
    
    async def get_best_bid(self) -> Optional[OrderEntry]:
        """Get best bid (highest buy price)"""
        while self.bids:
            if self.bids[0].order_id in self.orders:
                return self.bids[0]
            heapq.heappop(self.bids)  # Cleanup cancelled orders
        return None
    
    async def get_best_ask(self) -> Optional[OrderEntry]:
        """Get best ask (lowest sell price)"""
        while self.asks:
            if self.asks[0].order_id in self.orders:
                return self.asks[0]
            heapq.heappop(self.asks)
        return None
    
    async def get_depth(self, levels: int = 20) -> Tuple[List[OrderBookEntry], List[OrderBookEntry]]:
        """Get order book depth"""
        async with self._lock:
            bid_depth = defaultdict(lambda: {"quantity": Decimal(0), "count": 0})
            ask_depth = defaultdict(lambda: {"quantity": Decimal(0), "count": 0})
            
            for entry in self.bids:
                if entry.order_id in self.orders:
                    bid_depth[entry.price]["quantity"] += entry.quantity
                    bid_depth[entry.price]["count"] += 1
            
            for entry in self.asks:
                if entry.order_id in self.orders:
                    ask_depth[entry.price]["quantity"] += entry.quantity
                    ask_depth[entry.price]["count"] += 1
            
            bids = [
                OrderBookEntry(price=p, quantity=d["quantity"], order_count=d["count"])
                for p, d in sorted(bid_depth.items(), reverse=True)[:levels]
            ]
            
            asks = [
                OrderBookEntry(price=p, quantity=d["quantity"], order_count=d["count"])
                for p, d in sorted(ask_depth.items())[:levels]
            ]
            
            return bids, asks


class TradingEngine:
    """
    High-performance order matching engine
    
    Features:
    - Price-time priority matching
    - Support for market, limit, stop-limit orders
    - Real-time trade execution
    - Redis pub/sub for trade notifications
    """
    
    def __init__(self):
        self.order_books: dict[str, OrderBook] = {}
        self._trade_counter = 0
        self._lock = asyncio.Lock()
    
    def _get_order_book(self, symbol: str) -> OrderBook:
        """Get or create order book for symbol"""
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
        return self.order_books[symbol]
    
    async def place_order(
        self,
        db: AsyncSession,
        redis_client: redis.Redis,
        user_id: UUID,
        order_create: OrderCreate
    ) -> Tuple[Order, List[Trade]]:
        """
        Place a new order
        Returns the order and any resulting trades
        """
        # Generate client order ID if not provided
        client_order_id = order_create.client_order_id or f"O{uuid4().hex[:16].upper()}"
        
        # Create order record
        order = Order(
            user_id=user_id,
            client_order_id=client_order_id,
            symbol=order_create.symbol,
            side=order_create.side,
            order_type=order_create.order_type,
            time_in_force=order_create.time_in_force,
            price=order_create.price,
            stop_price=order_create.stop_price,
            quantity=order_create.quantity,
            remaining_quantity=order_create.quantity,
            status=OrderStatus.PENDING
        )
        
        db.add(order)
        await db.flush()
        
        # Process order based on type
        trades = []
        
        if order_create.order_type == OrderType.MARKET:
            trades = await self._execute_market_order(db, redis_client, order)
        elif order_create.order_type == OrderType.LIMIT:
            trades = await self._execute_limit_order(db, redis_client, order)
        
        await db.refresh(order)
        return order, trades
    
    async def _execute_market_order(
        self,
        db: AsyncSession,
        redis_client: redis.Redis,
        order: Order
    ) -> List[Trade]:
        """Execute market order immediately against book"""
        book = self._get_order_book(order.symbol)
        trades = []
        remaining = order.remaining_quantity
        
        while remaining > 0:
            if order.side == OrderSide.BUY:
                best = await book.get_best_ask()
            else:
                best = await book.get_best_bid()
            
            if not best:
                break  # No liquidity
            
            # Calculate fill
            fill_qty = min(remaining, best.quantity)
            fill_price = best.price
            
            # Create trade
            trade = await self._create_trade(
                db, order, best.order_id, fill_price, fill_qty
            )
            trades.append(trade)
            
            # Update quantities
            remaining -= fill_qty
            best.quantity -= fill_qty
            
            if best.quantity <= 0:
                await book.cancel_order(best.order_id)
        
        # Update order status
        order.filled_quantity = order.quantity - remaining
        order.remaining_quantity = remaining
        
        if remaining == 0:
            order.status = OrderStatus.FILLED
        elif order.filled_quantity > 0:
            order.status = OrderStatus.PARTIAL
        else:
            order.status = OrderStatus.OPEN
        
        # Calculate average fill price
        if trades:
            total_value = sum(t.price * t.quantity for t in trades)
            total_qty = sum(t.quantity for t in trades)
            order.average_fill_price = total_value / total_qty
        
        # Publish trades to Redis
        await self._publish_trades(redis_client, trades)
        
        return trades
    
    async def _execute_limit_order(
        self,
        db: AsyncSession,
        redis_client: redis.Redis,
        order: Order
    ) -> List[Trade]:
        """Execute limit order - match or add to book"""
        book = self._get_order_book(order.symbol)
        trades = []
        remaining = order.remaining_quantity
        
        # Try to match against existing orders
        while remaining > 0:
            if order.side == OrderSide.BUY:
                best = await book.get_best_ask()
                if not best or best.price > order.price:
                    break  # No match at our price
            else:
                best = await book.get_best_bid()
                if not best or best.price < order.price:
                    break
            
            fill_qty = min(remaining, best.quantity)
            fill_price = best.price
            
            trade = await self._create_trade(
                db, order, best.order_id, fill_price, fill_qty
            )
            trades.append(trade)
            
            remaining -= fill_qty
            best.quantity -= fill_qty
            
            if best.quantity <= 0:
                await book.cancel_order(best.order_id)
        
        # Update order
        order.filled_quantity = order.quantity - remaining
        order.remaining_quantity = remaining
        
        if remaining == 0:
            order.status = OrderStatus.FILLED
        elif order.filled_quantity > 0:
            order.status = OrderStatus.PARTIAL
            # Add remaining to book
            await self._add_to_book(book, order, remaining)
        else:
            order.status = OrderStatus.OPEN
            await self._add_to_book(book, order, remaining)
        
        if trades:
            total_value = sum(t.price * t.quantity for t in trades)
            total_qty = sum(t.quantity for t in trades)
            order.average_fill_price = total_value / total_qty
            await self._publish_trades(redis_client, trades)
        
        return trades
    
    async def _add_to_book(
        self,
        book: OrderBook,
        order: Order,
        quantity: Decimal
    ) -> None:
        """Add order to order book"""
        now = datetime.utcnow().timestamp()
        
        if order.side == OrderSide.BUY:
            priority = -float(order.price)  # Negative for max-heap
        else:
            priority = float(order.price)
        
        entry = OrderEntry(
            priority=priority,
            timestamp=now,
            order_id=order.id,
            price=order.price,
            quantity=quantity,
            user_id=order.user_id
        )
        
        await book.add_order(entry, order.side)
    
    async def _create_trade(
        self,
        db: AsyncSession,
        order: Order,
        counterparty_order_id: UUID,
        price: Decimal,
        quantity: Decimal
    ) -> Trade:
        """Create trade record"""
        async with self._lock:
            self._trade_counter += 1
            trade_id = self._trade_counter
        
        trade = Trade(
            trade_id=trade_id,
            user_id=order.user_id,
            order_id=order.id,
            counterparty_order_id=counterparty_order_id,
            symbol=order.symbol,
            side=order.side.value,
            price=price,
            quantity=quantity,
            quote_quantity=price * quantity,
            commission=quantity * Decimal("0.001"),  # 0.1% fee
            commission_asset=order.symbol.split("-")[0],
            is_maker="taker",
            executed_at=datetime.utcnow()
        )
        
        db.add(trade)
        await db.flush()
        
        return trade
    
    async def _publish_trades(
        self,
        redis_client: redis.Redis,
        trades: List[Trade]
    ) -> None:
        """Publish trades to Redis for WebSocket broadcast"""
        for trade in trades:
            await redis_client.publish(
                f"trades:{trade.symbol}",
                f"{trade.trade_id}|{trade.price}|{trade.quantity}|{trade.side}"
            )
    
    async def cancel_order(
        self,
        db: AsyncSession,
        order_id: UUID,
        user_id: UUID
    ) -> bool:
        """Cancel an open order"""
        result = await db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_id == user_id,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL, OrderStatus.PENDING])
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return False
        
        # Remove from order book
        book = self._get_order_book(order.symbol)
        await book.cancel_order(order_id)
        
        # Update database
        order.status = OrderStatus.CANCELLED
        await db.flush()
        
        return True
    
    async def get_order_book(
        self,
        symbol: str,
        levels: int = 20
    ) -> Tuple[List[OrderBookEntry], List[OrderBookEntry], int]:
        """Get order book depth for symbol"""
        book = self._get_order_book(symbol)
        bids, asks = await book.get_depth(levels)
        return bids, asks, book.sequence
    
    async def get_user_orders(
        self,
        db: AsyncSession,
        user_id: UUID,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get user's orders"""
        query = select(Order).where(Order.user_id == user_id)
        
        if symbol:
            query = query.where(Order.symbol == symbol)
        if status:
            query = query.where(Order.status == status)
        
        query = query.order_by(Order.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

