//! FastTrading Data Pipeline
//!
//! High-throughput data pipeline for:
//! - Real-time price aggregation
//! - Trade stream processing
//! - Market data distribution
//! - Position and PnL calculation

use anyhow::Result;
use std::sync::Arc;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod aggregator;
mod cache;
mod config;
mod consumer;
mod publisher;

use config::Config;

#[tokio::main]
async fn main() -> Result<()> {
    dotenvy::dotenv().ok();
    let config = Config::load()?;

    // Initialize tracing
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(&config.log_level))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    info!(
        "Starting FastTrading Data Pipeline v{}",
        env!("CARGO_PKG_VERSION")
    );

    // Initialize Redis cache
    let cache = Arc::new(cache::RedisCache::new(&config.redis_url).await?);

    // Initialize price aggregator
    let aggregator = Arc::new(aggregator::PriceAggregator::new(cache.clone()));

    // Start trade consumer
    let agg_clone = aggregator.clone();
    let config_clone = config.clone();
    tokio::spawn(async move {
        if let Err(e) = consumer::run_trade_consumer(agg_clone, &config_clone).await {
            tracing::error!("Trade consumer error: {}", e);
        }
    });

    // Start price publisher
    let agg_clone = aggregator.clone();
    let config_clone = config.clone();
    tokio::spawn(async move {
        if let Err(e) = publisher::run_price_publisher(agg_clone, &config_clone).await {
            tracing::error!("Price publisher error: {}", e);
        }
    });

    // Start candle aggregation
    let agg_clone = aggregator.clone();
    tokio::spawn(async move {
        if let Err(e) = aggregator::run_candle_aggregation(agg_clone).await {
            tracing::error!("Candle aggregation error: {}", e);
        }
    });

    // Run HTTP API for health checks and metrics
    publisher::run_api_server(&config).await?;

    Ok(())
}
