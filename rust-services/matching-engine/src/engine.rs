//! Matching Engine Core
//!
//! Manages multiple order books and coordinates order processing

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;

use anyhow::Result;
use dashmap::DashMap;
use parking_lot::RwLock;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::ClientConfig;
use tokio::sync::mpsc;
use tracing::{info, instrument, warn};

use common::{
    events::{topics, Event, OrderAccepted, OrderUpdated, TradeExecuted},
    Order, OrderStatus, Symbol, Trade, TradingError,
};

use crate::config::Config;
use crate::orderbook::OrderBook;

/// Order command for the matching engine
pub enum OrderCommand {
    NewOrder(Order),
    CancelOrder {
        order_id: uuid::Uuid,
        symbol: Symbol,
    },
}

/// Matching Engine
pub struct MatchingEngine {
    /// Order books per symbol
    order_books: DashMap<String, Arc<OrderBook>>,

    /// Kafka producer for events
    producer: FutureProducer,

    /// Command channel
    command_tx: mpsc::Sender<OrderCommand>,
    command_rx: RwLock<Option<mpsc::Receiver<OrderCommand>>>,

    /// Supported symbols
    symbols: Vec<Symbol>,
}

impl MatchingEngine {
    pub async fn new(config: &Config) -> Result<Self> {
        // Initialize Kafka producer
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", &config.kafka_brokers)
            .set("message.timeout.ms", "5000")
            .set("acks", "all")
            .set("enable.idempotence", "true")
            .create()?;

        // Create command channel
        let (tx, rx) = mpsc::channel(100_000);

        // Initialize symbols
        let symbols = vec![
            Symbol::new("BTC", "USDT"),
            Symbol::new("ETH", "USDT"),
            Symbol::new("SOL", "USDT"),
            Symbol::new("AVAX", "USDT"),
        ];

        let engine = Self {
            order_books: DashMap::new(),
            producer,
            command_tx: tx,
            command_rx: RwLock::new(Some(rx)),
            symbols: symbols.clone(),
        };

        // Initialize order books
        for symbol in symbols {
            engine
                .order_books
                .insert(symbol.to_string(), Arc::new(OrderBook::new(symbol)));
        }

        Ok(engine)
    }

    /// Get command sender
    pub fn command_sender(&self) -> mpsc::Sender<OrderCommand> {
        self.command_tx.clone()
    }

    /// Run the main matching loop
    pub async fn run_matching_loop(&self) -> Result<()> {
        let mut rx = self
            .command_rx
            .write()
            .take()
            .expect("Matching loop already started");

        info!("Starting matching engine loop");

        while let Some(command) = rx.recv().await {
            match command {
                OrderCommand::NewOrder(order) => {
                    self.process_new_order(order).await?;
                }
                OrderCommand::CancelOrder { order_id, symbol } => {
                    self.process_cancel(order_id, symbol).await?;
                }
            }
        }

        Ok(())
    }

    /// Process a new order
    #[instrument(skip(self), fields(order_id = %order.id, symbol = %order.symbol))]
    async fn process_new_order(&self, order: Order) -> Result<()> {
        let start = std::time::Instant::now();

        // Get order book
        let book = self.get_order_book(&order.symbol)?;

        // Process through matching engine
        let (updated_order, trades) = book.process_order(order.clone());

        // Record latency
        let latency = start.elapsed();
        metrics::histogram!("matching_latency_us").record(latency.as_micros() as f64);

        // Publish order accepted event
        self.publish_order_event(&updated_order).await?;

        // Publish trade events
        for trade in &trades {
            self.publish_trade_event(trade).await?;
            metrics::counter!("trades_executed").increment(1);
        }

        info!(
            order_id = %updated_order.id,
            status = ?updated_order.status,
            trades = trades.len(),
            latency_us = latency.as_micros(),
            "Order processed"
        );

        Ok(())
    }

    /// Process order cancellation
    #[instrument(skip(self), fields(order_id = %order_id, symbol = %symbol))]
    async fn process_cancel(&self, order_id: uuid::Uuid, symbol: Symbol) -> Result<()> {
        let book = self.get_order_book(&symbol)?;

        if book.cancel_order(order_id) {
            metrics::counter!("orders_cancelled").increment(1);
            info!("Order cancelled");
        } else {
            warn!("Order not found for cancellation");
        }

        Ok(())
    }

    /// Get order book for symbol
    fn get_order_book(&self, symbol: &Symbol) -> Result<Arc<OrderBook>> {
        self.order_books
            .get(&symbol.to_string())
            .map(|r| r.clone())
            .ok_or_else(|| TradingError::SymbolNotFound(symbol.to_string()).into())
    }

    /// Submit order to matching engine
    pub async fn submit_order(&self, order: Order) -> Result<()> {
        self.command_tx
            .send(OrderCommand::NewOrder(order))
            .await
            .map_err(|_| anyhow::anyhow!("Matching engine channel closed"))?;
        Ok(())
    }

    /// Cancel order
    pub async fn cancel_order(&self, order_id: uuid::Uuid, symbol: Symbol) -> Result<()> {
        self.command_tx
            .send(OrderCommand::CancelOrder { order_id, symbol })
            .await
            .map_err(|_| anyhow::anyhow!("Matching engine channel closed"))?;
        Ok(())
    }

    /// Get order book depth
    pub fn get_depth(
        &self,
        symbol: &Symbol,
        levels: usize,
    ) -> Result<(Vec<common::PriceLevel>, Vec<common::PriceLevel>)> {
        let book = self.get_order_book(symbol)?;
        Ok(book.get_depth(levels))
    }

    /// Get best bid/offer
    pub fn get_bbo(
        &self,
        symbol: &Symbol,
    ) -> Result<(Option<rust_decimal::Decimal>, Option<rust_decimal::Decimal>)> {
        let book = self.get_order_book(symbol)?;
        Ok(book.get_bbo())
    }

    /// Publish order event to Kafka
    async fn publish_order_event(&self, order: &Order) -> Result<()> {
        let event = Event::new(
            "order_updated",
            "matching-engine",
            OrderUpdated {
                order_id: order.id,
                client_order_id: order.client_order_id.clone(),
                symbol: order.symbol.clone(),
                status: order.status,
                filled_quantity: order.filled_quantity,
                remaining_quantity: order.remaining_quantity,
                avg_fill_price: order.avg_fill_price,
                timestamp: order.updated_at,
            },
        );

        let payload = serde_json::to_string(&event)?;

        self.producer
            .send(
                FutureRecord::to(topics::ORDERS)
                    .key(&order.id.to_string())
                    .payload(&payload),
                Duration::from_secs(5),
            )
            .await
            .map_err(|(e, _)| anyhow::anyhow!("Kafka send error: {}", e))?;

        Ok(())
    }

    /// Publish trade event to Kafka
    async fn publish_trade_event(&self, trade: &Trade) -> Result<()> {
        let event = Event::new(
            "trade_executed",
            "matching-engine",
            TradeExecuted {
                trade: trade.clone(),
            },
        );

        let payload = serde_json::to_string(&event)?;

        self.producer
            .send(
                FutureRecord::to(topics::TRADES)
                    .key(&trade.id.to_string())
                    .payload(&payload),
                Duration::from_secs(5),
            )
            .await
            .map_err(|(e, _)| anyhow::anyhow!("Kafka send error: {}", e))?;

        Ok(())
    }

    /// Get supported symbols
    pub fn symbols(&self) -> &[Symbol] {
        &self.symbols
    }
}
