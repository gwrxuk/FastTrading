//! Price and Trade Aggregation
//!
//! Aggregates trades into OHLCV candles and maintains
//! real-time price statistics.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;

use chrono::{DateTime, Utc, Timelike, Duration as ChronoDuration};
use dashmap::DashMap;
use parking_lot::RwLock;
use rust_decimal::Decimal;
use tokio::time;
use tracing::info;

use common::{Candle, MarketData, Symbol, Trade};
use crate::cache::RedisCache;

/// Real-time price data for a symbol
#[derive(Debug, Clone)]
pub struct SymbolStats {
    pub symbol: Symbol,
    pub last_price: Decimal,
    pub bid: Decimal,
    pub ask: Decimal,
    pub volume_24h: Decimal,
    pub high_24h: Decimal,
    pub low_24h: Decimal,
    pub open_24h: Decimal,
    pub trade_count_24h: u64,
    pub last_update: DateTime<Utc>,
}

impl SymbolStats {
    pub fn new(symbol: Symbol) -> Self {
        Self {
            symbol,
            last_price: Decimal::ZERO,
            bid: Decimal::ZERO,
            ask: Decimal::ZERO,
            volume_24h: Decimal::ZERO,
            high_24h: Decimal::ZERO,
            low_24h: Decimal::MAX,
            open_24h: Decimal::ZERO,
            trade_count_24h: 0,
            last_update: Utc::now(),
        }
    }

    pub fn update_from_trade(&mut self, trade: &Trade) {
        self.last_price = trade.price;
        self.volume_24h += trade.quantity;
        self.trade_count_24h += 1;
        
        if trade.price > self.high_24h {
            self.high_24h = trade.price;
        }
        if trade.price < self.low_24h {
            self.low_24h = trade.price;
        }
        if self.open_24h == Decimal::ZERO {
            self.open_24h = trade.price;
        }
        
        self.last_update = trade.executed_at;
    }

    pub fn to_market_data(&self) -> MarketData {
        MarketData {
            symbol: self.symbol.clone(),
            bid: self.bid,
            ask: self.ask,
            last: self.last_price,
            volume_24h: self.volume_24h,
            high_24h: self.high_24h,
            low_24h: self.low_24h,
            timestamp: self.last_update,
        }
    }
}

/// Candle builder for a specific interval
#[derive(Debug, Clone)]
pub struct CandleBuilder {
    pub symbol: Symbol,
    pub interval: String,
    pub open_time: DateTime<Utc>,
    pub open: Decimal,
    pub high: Decimal,
    pub low: Decimal,
    pub close: Decimal,
    pub volume: Decimal,
    pub trade_count: u32,
}

impl CandleBuilder {
    pub fn new(symbol: Symbol, interval: &str, open_time: DateTime<Utc>) -> Self {
        Self {
            symbol,
            interval: interval.to_string(),
            open_time,
            open: Decimal::ZERO,
            high: Decimal::ZERO,
            low: Decimal::MAX,
            close: Decimal::ZERO,
            volume: Decimal::ZERO,
            trade_count: 0,
        }
    }

    pub fn update(&mut self, price: Decimal, quantity: Decimal) {
        if self.open == Decimal::ZERO {
            self.open = price;
        }
        if price > self.high {
            self.high = price;
        }
        if price < self.low {
            self.low = price;
        }
        self.close = price;
        self.volume += quantity;
        self.trade_count += 1;
    }

    pub fn to_candle(&self, close_time: DateTime<Utc>) -> Candle {
        Candle {
            symbol: self.symbol.clone(),
            interval: self.interval.clone(),
            open_time: self.open_time,
            open: self.open,
            high: self.high,
            low: if self.low == Decimal::MAX { self.open } else { self.low },
            close: self.close,
            volume: self.volume,
            close_time,
            trade_count: self.trade_count,
        }
    }
}

/// Price Aggregator
pub struct PriceAggregator {
    /// Real-time stats per symbol
    stats: DashMap<String, SymbolStats>,
    
    /// Candle builders per symbol per interval
    candles: DashMap<String, HashMap<String, CandleBuilder>>,
    
    /// Redis cache for persistence
    cache: Arc<RedisCache>,
}

impl PriceAggregator {
    pub fn new(cache: Arc<RedisCache>) -> Self {
        Self {
            stats: DashMap::new(),
            candles: DashMap::new(),
            cache,
        }
    }

    /// Process incoming trade
    pub async fn process_trade(&self, trade: Trade) -> anyhow::Result<()> {
        let symbol_key = trade.symbol.to_string();

        // Update real-time stats
        self.stats
            .entry(symbol_key.clone())
            .or_insert_with(|| SymbolStats::new(trade.symbol.clone()))
            .update_from_trade(&trade);

        // Update candle builders
        self.update_candles(&trade);

        // Cache latest price
        self.cache.set_price(&trade.symbol, trade.price).await?;

        metrics::counter!("trades_processed").increment(1);

        Ok(())
    }

    /// Update candle builders with trade
    fn update_candles(&self, trade: &Trade) {
        let symbol_key = trade.symbol.to_string();
        let intervals = vec!["1m", "5m", "15m", "1h", "4h", "1d"];

        let mut candle_map = self.candles
            .entry(symbol_key)
            .or_insert_with(HashMap::new);

        for interval in intervals {
            let candle_open = get_candle_open_time(trade.executed_at, interval);
            
            let builder = candle_map
                .entry(interval.to_string())
                .or_insert_with(|| CandleBuilder::new(trade.symbol.clone(), interval, candle_open));

            // Check if we need a new candle
            if builder.open_time != candle_open {
                // TODO: Publish completed candle
                *builder = CandleBuilder::new(trade.symbol.clone(), interval, candle_open);
            }

            builder.update(trade.price, trade.quantity);
        }
    }

    /// Get current market data for symbol
    pub fn get_market_data(&self, symbol: &Symbol) -> Option<MarketData> {
        self.stats.get(&symbol.to_string()).map(|s| s.to_market_data())
    }

    /// Get all market data
    pub fn get_all_market_data(&self) -> Vec<MarketData> {
        self.stats.iter().map(|r| r.value().to_market_data()).collect()
    }

    /// Get current candle for symbol and interval
    pub fn get_current_candle(&self, symbol: &Symbol, interval: &str) -> Option<Candle> {
        self.candles.get(&symbol.to_string()).and_then(|map| {
            map.get(interval).map(|b| b.to_candle(Utc::now()))
        })
    }
}

/// Get candle open time for a given timestamp and interval
fn get_candle_open_time(timestamp: DateTime<Utc>, interval: &str) -> DateTime<Utc> {
    let ts = timestamp;
    
    match interval {
        "1m" => ts.with_second(0).unwrap().with_nanosecond(0).unwrap(),
        "5m" => {
            let minute = (ts.minute() / 5) * 5;
            ts.with_minute(minute).unwrap().with_second(0).unwrap().with_nanosecond(0).unwrap()
        }
        "15m" => {
            let minute = (ts.minute() / 15) * 15;
            ts.with_minute(minute).unwrap().with_second(0).unwrap().with_nanosecond(0).unwrap()
        }
        "1h" => ts.with_minute(0).unwrap().with_second(0).unwrap().with_nanosecond(0).unwrap(),
        "4h" => {
            let hour = (ts.hour() / 4) * 4;
            ts.with_hour(hour).unwrap().with_minute(0).unwrap().with_second(0).unwrap().with_nanosecond(0).unwrap()
        }
        "1d" => ts.with_hour(0).unwrap().with_minute(0).unwrap().with_second(0).unwrap().with_nanosecond(0).unwrap(),
        _ => ts,
    }
}

/// Run candle aggregation task
pub async fn run_candle_aggregation(aggregator: Arc<PriceAggregator>) -> anyhow::Result<()> {
    let mut interval = time::interval(Duration::from_secs(60));

    loop {
        interval.tick().await;
        
        // Process candle closures
        info!("Running candle aggregation tick");
        
        // TODO: Close and publish completed candles
    }
}

