//! Core trading types with high precision for financial data
//!
//! Uses rust_decimal for exact decimal arithmetic - critical for
//! financial calculations where floating point errors are unacceptable.

use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Trading pair symbol (e.g., "ETH-USDT")
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Symbol(pub String);

impl Symbol {
    pub fn new(base: &str, quote: &str) -> Self {
        Self(format!("{}-{}", base.to_uppercase(), quote.to_uppercase()))
    }

    pub fn base(&self) -> &str {
        self.0.split('-').next().unwrap_or("")
    }

    pub fn quote(&self) -> &str {
        self.0.split('-').nth(1).unwrap_or("")
    }
}

impl std::fmt::Display for Symbol {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Order side - Buy or Sell
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Side {
    Buy,
    Sell,
}

impl Side {
    pub fn opposite(&self) -> Self {
        match self {
            Side::Buy => Side::Sell,
            Side::Sell => Side::Buy,
        }
    }
}

/// Order type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderType {
    Market,
    Limit,
    StopLimit,
    StopMarket,
}

/// Time in force - How long the order remains active
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TimeInForce {
    /// Good Till Cancel - remains until filled or cancelled
    GTC,
    /// Immediate Or Cancel - fill what's possible, cancel rest
    IOC,
    /// Fill Or Kill - fill completely or cancel entirely
    FOK,
    /// Good Till Date - remains until specified date
    GTD,
}

/// Order status in the matching engine
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderStatus {
    Pending,
    Open,
    PartiallyFilled,
    Filled,
    Cancelled,
    Rejected,
    Expired,
}

/// Core Order structure
///
/// Designed for high-performance order matching with:
/// - Nanosecond timestamp precision
/// - Exact decimal arithmetic
/// - Minimal memory footprint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Order {
    pub id: Uuid,
    pub client_order_id: String,
    pub user_id: Uuid,
    pub symbol: Symbol,
    pub side: Side,
    pub order_type: OrderType,
    pub time_in_force: TimeInForce,
    pub status: OrderStatus,

    /// Limit price (None for market orders)
    #[serde(with = "rust_decimal::serde::str_option")]
    pub price: Option<Decimal>,

    /// Stop trigger price
    #[serde(with = "rust_decimal::serde::str_option")]
    pub stop_price: Option<Decimal>,

    /// Original order quantity
    #[serde(with = "rust_decimal::serde::str")]
    pub quantity: Decimal,

    /// Quantity already filled
    #[serde(with = "rust_decimal::serde::str")]
    pub filled_quantity: Decimal,

    /// Remaining quantity to fill
    #[serde(with = "rust_decimal::serde::str")]
    pub remaining_quantity: Decimal,

    /// Average execution price
    #[serde(with = "rust_decimal::serde::str_option")]
    pub avg_fill_price: Option<Decimal>,

    /// Sequence number for FIFO ordering
    pub sequence: u64,

    /// Timestamps with nanosecond precision
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Order {
    pub fn is_buy(&self) -> bool {
        self.side == Side::Buy
    }

    pub fn is_complete(&self) -> bool {
        matches!(
            self.status,
            OrderStatus::Filled
                | OrderStatus::Cancelled
                | OrderStatus::Rejected
                | OrderStatus::Expired
        )
    }

    pub fn can_match(&self) -> bool {
        matches!(
            self.status,
            OrderStatus::Open | OrderStatus::PartiallyFilled
        )
    }
}

/// Trade execution record - immutable after creation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub id: Uuid,
    pub trade_id: u64,
    pub symbol: Symbol,

    /// Maker order (was in the book)
    pub maker_order_id: Uuid,
    pub maker_user_id: Uuid,

    /// Taker order (incoming order)
    pub taker_order_id: Uuid,
    pub taker_user_id: Uuid,

    /// Execution details
    #[serde(with = "rust_decimal::serde::str")]
    pub price: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub quantity: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub quote_quantity: Decimal,

    /// Taker side
    pub taker_side: Side,

    pub executed_at: DateTime<Utc>,
}

/// Order book price level
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceLevel {
    #[serde(with = "rust_decimal::serde::str")]
    pub price: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub quantity: Decimal,

    pub order_count: u32,
}

/// Market data snapshot
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub symbol: Symbol,

    #[serde(with = "rust_decimal::serde::str")]
    pub bid: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub ask: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub last: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub volume_24h: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub high_24h: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub low_24h: Decimal,

    pub timestamp: DateTime<Utc>,
}

/// OHLCV Candlestick
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Candle {
    pub symbol: Symbol,
    pub interval: String,
    pub open_time: DateTime<Utc>,

    #[serde(with = "rust_decimal::serde::str")]
    pub open: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub high: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub low: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub close: Decimal,

    #[serde(with = "rust_decimal::serde::str")]
    pub volume: Decimal,

    pub close_time: DateTime<Utc>,
    pub trade_count: u32,
}
