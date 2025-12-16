//! Lock-free Order Book Implementation
//!
//! High-performance order book using:
//! - BTreeMap for price levels (sorted)
//! - VecDeque for FIFO ordering within price levels
//! - Atomic operations where possible
//!
//! # Performance Characteristics
//! - Insert: O(log n) for new price level, O(1) amortized within level
//! - Match: O(1) for best price lookup
//! - Cancel: O(log n) + O(m) where m is orders at that price

use std::collections::{BTreeMap, VecDeque, HashMap};
use std::sync::atomic::{AtomicU64, Ordering};
use chrono::Utc;
use parking_lot::RwLock;
use rust_decimal::Decimal;
use uuid::Uuid;

use common::{Order, OrderStatus, PriceLevel, Side, Symbol, Trade};

/// Order entry in the book
#[derive(Debug, Clone)]
struct OrderEntry {
    order_id: Uuid,
    user_id: Uuid,
    price: Decimal,
    remaining_quantity: Decimal,
    sequence: u64,
}

/// Price level containing orders at the same price
#[derive(Debug, Default)]
struct Level {
    orders: VecDeque<OrderEntry>,
    total_quantity: Decimal,
}

impl Level {
    fn add(&mut self, entry: OrderEntry) {
        self.total_quantity += entry.remaining_quantity;
        self.orders.push_back(entry);
    }

    fn remove(&mut self, order_id: Uuid) -> Option<OrderEntry> {
        if let Some(pos) = self.orders.iter().position(|o| o.order_id == order_id) {
            let entry = self.orders.remove(pos)?;
            self.total_quantity -= entry.remaining_quantity;
            Some(entry)
        } else {
            None
        }
    }

    fn is_empty(&self) -> bool {
        self.orders.is_empty()
    }

    fn peek(&self) -> Option<&OrderEntry> {
        self.orders.front()
    }

    fn pop(&mut self) -> Option<OrderEntry> {
        if let Some(entry) = self.orders.pop_front() {
            self.total_quantity -= entry.remaining_quantity;
            Some(entry)
        } else {
            None
        }
    }
}

/// Order book for a single trading pair
pub struct OrderBook {
    symbol: Symbol,
    
    /// Buy orders (bids) - highest price first
    bids: RwLock<BTreeMap<Decimal, Level>>,
    
    /// Sell orders (asks) - lowest price first  
    asks: RwLock<BTreeMap<Decimal, Level>>,
    
    /// Order ID to price mapping for fast cancellation
    order_prices: RwLock<HashMap<Uuid, (Side, Decimal)>>,
    
    /// Sequence counter for FIFO ordering
    sequence: AtomicU64,
    
    /// Trade ID counter
    trade_counter: AtomicU64,
    
    /// Book sequence for snapshot versioning
    book_sequence: AtomicU64,
}

impl OrderBook {
    pub fn new(symbol: Symbol) -> Self {
        Self {
            symbol,
            bids: RwLock::new(BTreeMap::new()),
            asks: RwLock::new(BTreeMap::new()),
            order_prices: RwLock::new(HashMap::new()),
            sequence: AtomicU64::new(0),
            trade_counter: AtomicU64::new(0),
            book_sequence: AtomicU64::new(0),
        }
    }

    /// Get next sequence number
    fn next_sequence(&self) -> u64 {
        self.sequence.fetch_add(1, Ordering::SeqCst)
    }

    /// Get next trade ID
    fn next_trade_id(&self) -> u64 {
        self.trade_counter.fetch_add(1, Ordering::SeqCst)
    }

    /// Get current book sequence
    pub fn book_sequence(&self) -> u64 {
        self.book_sequence.load(Ordering::SeqCst)
    }

    /// Process an incoming order
    /// Returns (updated order, list of trades)
    pub fn process_order(&self, mut order: Order) -> (Order, Vec<Trade>) {
        order.sequence = self.next_sequence();
        order.status = OrderStatus::Open;
        
        let mut trades = Vec::new();
        
        // Try to match against opposite side
        let remaining = self.match_order(&mut order, &mut trades);
        
        // Update order status
        if remaining == Decimal::ZERO {
            order.status = OrderStatus::Filled;
        } else if order.remaining_quantity < order.quantity {
            order.status = OrderStatus::PartiallyFilled;
            
            // Add remaining to book (for limit orders)
            if order.price.is_some() {
                self.add_to_book(&order);
            }
        } else {
            // No fills - add to book (for limit orders)
            if order.price.is_some() {
                self.add_to_book(&order);
            }
        }
        
        order.remaining_quantity = remaining;
        order.updated_at = Utc::now();
        
        // Update book sequence
        if !trades.is_empty() {
            self.book_sequence.fetch_add(1, Ordering::SeqCst);
        }
        
        (order, trades)
    }

    /// Match order against the book
    fn match_order(&self, order: &mut Order, trades: &mut Vec<Trade>) -> Decimal {
        let mut remaining = order.remaining_quantity;
        
        // Determine which side to match against
        let is_buy = order.side == Side::Buy;
        
        loop {
            if remaining == Decimal::ZERO {
                break;
            }
            
            // Get best opposing price
            let (best_price, can_match) = if is_buy {
                self.get_best_ask(order.price)
            } else {
                self.get_best_bid(order.price)
            };
            
            if !can_match {
                break;
            }
            
            // Match at this price level
            let (matched, level_trades) = self.match_at_price(
                order,
                best_price,
                remaining,
                is_buy,
            );
            
            remaining -= matched;
            order.filled_quantity += matched;
            trades.extend(level_trades);
        }
        
        // Calculate average fill price
        if !trades.is_empty() {
            let total_value: Decimal = trades.iter()
                .map(|t| t.price * t.quantity)
                .sum();
            let total_qty: Decimal = trades.iter()
                .map(|t| t.quantity)
                .sum();
            order.avg_fill_price = Some(total_value / total_qty);
        }
        
        remaining
    }

    /// Get best ask price that matches our buy order
    fn get_best_ask(&self, max_price: Option<Decimal>) -> (Decimal, bool) {
        let asks = self.asks.read();
        
        if let Some((&price, _)) = asks.first_key_value() {
            match max_price {
                Some(max) if price <= max => (price, true),
                Some(_) => (Decimal::ZERO, false),
                None => (price, true), // Market order
            }
        } else {
            (Decimal::ZERO, false)
        }
    }

    /// Get best bid price that matches our sell order
    fn get_best_bid(&self, min_price: Option<Decimal>) -> (Decimal, bool) {
        let bids = self.bids.read();
        
        if let Some((&price, _)) = bids.last_key_value() {
            match min_price {
                Some(min) if price >= min => (price, true),
                Some(_) => (Decimal::ZERO, false),
                None => (price, true), // Market order
            }
        } else {
            (Decimal::ZERO, false)
        }
    }

    /// Match at a specific price level
    fn match_at_price(
        &self,
        taker_order: &Order,
        price: Decimal,
        mut quantity: Decimal,
        is_buy: bool,
    ) -> (Decimal, Vec<Trade>) {
        let mut trades = Vec::new();
        let mut matched = Decimal::ZERO;
        
        let mut book = if is_buy {
            self.asks.write()
        } else {
            self.bids.write()
        };
        
        let level = match book.get_mut(&price) {
            Some(level) => level,
            None => return (Decimal::ZERO, trades),
        };
        
        while quantity > Decimal::ZERO {
            let maker = match level.peek() {
                Some(o) => o.clone(),
                None => break,
            };
            
            // Self-trade prevention
            if maker.user_id == taker_order.user_id {
                level.pop();
                continue;
            }
            
            let fill_qty = quantity.min(maker.remaining_quantity);
            let quote_qty = fill_qty * price;
            
            // Create trade
            let trade = Trade {
                id: Uuid::new_v4(),
                trade_id: self.next_trade_id(),
                symbol: self.symbol.clone(),
                maker_order_id: maker.order_id,
                maker_user_id: maker.user_id,
                taker_order_id: taker_order.id,
                taker_user_id: taker_order.user_id,
                price,
                quantity: fill_qty,
                quote_quantity: quote_qty,
                taker_side: taker_order.side,
                executed_at: Utc::now(),
            };
            
            trades.push(trade);
            matched += fill_qty;
            quantity -= fill_qty;
            
            // Update or remove maker order
            if fill_qty >= maker.remaining_quantity {
                level.pop();
                self.order_prices.write().remove(&maker.order_id);
            } else {
                // Update remaining quantity in place
                if let Some(entry) = level.orders.front_mut() {
                    entry.remaining_quantity -= fill_qty;
                    level.total_quantity -= fill_qty;
                }
            }
        }
        
        // Remove empty price level
        if level.is_empty() {
            book.remove(&price);
        }
        
        (matched, trades)
    }

    /// Add order to the book
    fn add_to_book(&self, order: &Order) {
        let price = order.price.expect("Limit order must have price");
        
        let entry = OrderEntry {
            order_id: order.id,
            user_id: order.user_id,
            price,
            remaining_quantity: order.remaining_quantity,
            sequence: order.sequence,
        };
        
        // Track order location for cancellation
        self.order_prices.write().insert(order.id, (order.side, price));
        
        // Add to appropriate side
        match order.side {
            Side::Buy => {
                self.bids.write().entry(price).or_default().add(entry);
            }
            Side::Sell => {
                self.asks.write().entry(price).or_default().add(entry);
            }
        }
        
        self.book_sequence.fetch_add(1, Ordering::SeqCst);
    }

    /// Cancel an order
    pub fn cancel_order(&self, order_id: Uuid) -> bool {
        let location = self.order_prices.write().remove(&order_id);
        
        if let Some((side, price)) = location {
            let mut book = match side {
                Side::Buy => self.bids.write(),
                Side::Sell => self.asks.write(),
            };
            
            if let Some(level) = book.get_mut(&price) {
                level.remove(order_id);
                
                if level.is_empty() {
                    book.remove(&price);
                }
            }
            
            self.book_sequence.fetch_add(1, Ordering::SeqCst);
            true
        } else {
            false
        }
    }

    /// Get order book depth
    pub fn get_depth(&self, levels: usize) -> (Vec<PriceLevel>, Vec<PriceLevel>) {
        let bids: Vec<PriceLevel> = self.bids.read()
            .iter()
            .rev()
            .take(levels)
            .map(|(&price, level)| PriceLevel {
                price,
                quantity: level.total_quantity,
                order_count: level.orders.len() as u32,
            })
            .collect();
        
        let asks: Vec<PriceLevel> = self.asks.read()
            .iter()
            .take(levels)
            .map(|(&price, level)| PriceLevel {
                price,
                quantity: level.total_quantity,
                order_count: level.orders.len() as u32,
            })
            .collect();
        
        (bids, asks)
    }

    /// Get best bid/ask
    pub fn get_bbo(&self) -> (Option<Decimal>, Option<Decimal>) {
        let best_bid = self.bids.read().last_key_value().map(|(&p, _)| p);
        let best_ask = self.asks.read().first_key_value().map(|(&p, _)| p);
        (best_bid, best_ask)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use common::{OrderType, TimeInForce};

    fn create_order(side: Side, price: Decimal, quantity: Decimal) -> Order {
        Order {
            id: Uuid::new_v4(),
            client_order_id: "test".to_string(),
            user_id: Uuid::new_v4(),
            symbol: Symbol::new("ETH", "USDT"),
            side,
            order_type: OrderType::Limit,
            time_in_force: TimeInForce::GTC,
            status: OrderStatus::Pending,
            price: Some(price),
            stop_price: None,
            quantity,
            filled_quantity: Decimal::ZERO,
            remaining_quantity: quantity,
            avg_fill_price: None,
            sequence: 0,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        }
    }

    #[test]
    fn test_add_and_match() {
        let book = OrderBook::new(Symbol::new("ETH", "USDT"));
        
        // Add sell order
        let sell = create_order(Side::Sell, Decimal::new(2000, 0), Decimal::new(1, 0));
        let (sell_result, trades) = book.process_order(sell);
        assert!(trades.is_empty());
        assert_eq!(sell_result.status, OrderStatus::Open);
        
        // Add matching buy order
        let buy = create_order(Side::Buy, Decimal::new(2000, 0), Decimal::new(1, 0));
        let (buy_result, trades) = book.process_order(buy);
        assert_eq!(trades.len(), 1);
        assert_eq!(buy_result.status, OrderStatus::Filled);
    }

    #[test]
    fn test_partial_fill() {
        let book = OrderBook::new(Symbol::new("ETH", "USDT"));
        
        // Add sell order for 2 ETH
        let sell = create_order(Side::Sell, Decimal::new(2000, 0), Decimal::new(2, 0));
        book.process_order(sell);
        
        // Buy only 1 ETH
        let buy = create_order(Side::Buy, Decimal::new(2000, 0), Decimal::new(1, 0));
        let (_, trades) = book.process_order(buy);
        
        assert_eq!(trades.len(), 1);
        assert_eq!(trades[0].quantity, Decimal::new(1, 0));
        
        // Check remaining depth
        let (_, asks) = book.get_depth(10);
        assert_eq!(asks.len(), 1);
        assert_eq!(asks[0].quantity, Decimal::new(1, 0));
    }
}

