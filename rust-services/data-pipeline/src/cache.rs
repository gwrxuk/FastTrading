//! Redis Cache for real-time data
//!
//! Provides low-latency access to:
//! - Current prices
//! - Order book snapshots
//! - User positions

use anyhow::Result;
use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use rust_decimal::Decimal;

use common::Symbol;

pub struct RedisCache {
    conn: ConnectionManager,
}

impl RedisCache {
    pub async fn new(redis_url: &str) -> Result<Self> {
        let client = redis::Client::open(redis_url)?;
        let conn = ConnectionManager::new(client).await?;
        Ok(Self { conn })
    }

    /// Set current price for symbol
    pub async fn set_price(&self, symbol: &Symbol, price: Decimal) -> Result<()> {
        let key = format!("price:{symbol}");
        let mut conn = self.conn.clone();
        conn.set_ex::<_, _, ()>(&key, price.to_string(), 60).await?;
        Ok(())
    }

    /// Get current price for symbol
    #[allow(dead_code)]
    pub async fn get_price(&self, symbol: &Symbol) -> Result<Option<Decimal>> {
        let key = format!("price:{symbol}");
        let mut conn = self.conn.clone();
        let result: Option<String> = conn.get(&key).await?;
        Ok(result.and_then(|s| s.parse().ok()))
    }

    /// Publish price update to Redis channel
    #[allow(dead_code)]
    pub async fn publish_price(&self, symbol: &Symbol, price: Decimal) -> Result<()> {
        let channel = format!("prices:{symbol}");
        let mut conn = self.conn.clone();
        conn.publish::<_, _, ()>(&channel, price.to_string())
            .await?;
        Ok(())
    }

    /// Store order book snapshot
    #[allow(dead_code)]
    pub async fn set_orderbook(&self, symbol: &Symbol, bids: &str, asks: &str) -> Result<()> {
        let key = format!("orderbook:{symbol}");
        let mut conn = self.conn.clone();
        conn.hset_multiple::<_, _, _, ()>(&key, &[("bids", bids), ("asks", asks)])
            .await?;
        conn.expire::<_, ()>(&key, 60).await?;
        Ok(())
    }

    /// Store user position
    #[allow(dead_code)]
    pub async fn set_position(&self, user_id: &str, symbol: &Symbol, position: &str) -> Result<()> {
        let key = format!("position:{user_id}:{symbol}");
        let mut conn = self.conn.clone();
        conn.set_ex::<_, _, ()>(&key, position, 300).await?;
        Ok(())
    }
}
