//! Event types for the event-driven architecture
//!
//! All inter-service communication uses strongly-typed events
//! published through Kafka for reliability and scalability.

use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::types::{Order, OrderStatus, Side, Symbol, Trade};

/// Event envelope with metadata for tracing and replay
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event<T> {
    /// Unique event ID
    pub id: Uuid,
    
    /// Event type for routing
    pub event_type: String,
    
    /// Correlation ID for request tracing
    pub correlation_id: Option<Uuid>,
    
    /// Source service
    pub source: String,
    
    /// Event timestamp
    pub timestamp: DateTime<Utc>,
    
    /// Sequence number for ordering
    pub sequence: u64,
    
    /// Event payload
    pub payload: T,
}

impl<T: Serialize> Event<T> {
    pub fn new(event_type: &str, source: &str, payload: T) -> Self {
        Self {
            id: Uuid::new_v4(),
            event_type: event_type.to_string(),
            correlation_id: None,
            source: source.to_string(),
            timestamp: Utc::now(),
            sequence: 0, // Set by producer
            payload,
        }
    }

    pub fn with_correlation(mut self, correlation_id: Uuid) -> Self {
        self.correlation_id = Some(correlation_id);
        self
    }
}

// ============== Order Events ==============

/// New order submitted to matching engine
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderSubmitted {
    pub order: Order,
}

/// Order accepted by matching engine
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderAccepted {
    pub order_id: Uuid,
    pub client_order_id: String,
    pub symbol: Symbol,
    pub status: OrderStatus,
    pub timestamp: DateTime<Utc>,
}

/// Order rejected by matching engine
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderRejected {
    pub order_id: Uuid,
    pub client_order_id: String,
    pub reason: String,
    pub timestamp: DateTime<Utc>,
}

/// Order status update
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderUpdated {
    pub order_id: Uuid,
    pub client_order_id: String,
    pub symbol: Symbol,
    pub status: OrderStatus,
    
    #[serde(with = "rust_decimal::serde::str")]
    pub filled_quantity: Decimal,
    
    #[serde(with = "rust_decimal::serde::str")]
    pub remaining_quantity: Decimal,
    
    #[serde(with = "rust_decimal::serde::str_option")]
    pub avg_fill_price: Option<Decimal>,
    
    pub timestamp: DateTime<Utc>,
}

/// Order cancelled
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderCancelled {
    pub order_id: Uuid,
    pub client_order_id: String,
    pub symbol: Symbol,
    pub reason: String,
    pub timestamp: DateTime<Utc>,
}

// ============== Trade Events ==============

/// Trade executed
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeExecuted {
    pub trade: Trade,
}

// ============== Market Data Events ==============

/// Order book update
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBookUpdate {
    pub symbol: Symbol,
    pub bids: Vec<(Decimal, Decimal)>, // (price, quantity)
    pub asks: Vec<(Decimal, Decimal)>,
    pub sequence: u64,
    pub timestamp: DateTime<Utc>,
}

/// Price tick
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceTick {
    pub symbol: Symbol,
    
    #[serde(with = "rust_decimal::serde::str")]
    pub price: Decimal,
    
    #[serde(with = "rust_decimal::serde::str")]
    pub quantity: Decimal,
    
    pub side: Side,
    pub timestamp: DateTime<Utc>,
}

// ============== Risk Events ==============

/// Position update
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionUpdate {
    pub user_id: Uuid,
    pub symbol: Symbol,
    
    #[serde(with = "rust_decimal::serde::str")]
    pub quantity: Decimal,
    
    #[serde(with = "rust_decimal::serde::str")]
    pub avg_entry_price: Decimal,
    
    #[serde(with = "rust_decimal::serde::str")]
    pub unrealized_pnl: Decimal,
    
    pub timestamp: DateTime<Utc>,
}

/// Risk alert
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskAlert {
    pub alert_id: Uuid,
    pub user_id: Option<Uuid>,
    pub alert_type: RiskAlertType,
    pub severity: AlertSeverity,
    pub message: String,
    pub metadata: serde_json::Value,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RiskAlertType {
    MarginCall,
    PositionLimit,
    ExposureLimit,
    Liquidation,
    AnomalousTrading,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AlertSeverity {
    Info,
    Warning,
    Critical,
}

// ============== Kafka Topics ==============

pub mod topics {
    pub const ORDERS: &str = "trading.orders";
    pub const TRADES: &str = "trading.trades";
    pub const ORDER_BOOK: &str = "market.orderbook";
    pub const PRICES: &str = "market.prices";
    pub const POSITIONS: &str = "risk.positions";
    pub const ALERTS: &str = "risk.alerts";
    pub const AUDIT: &str = "audit.events";
}

