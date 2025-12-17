//! FastTrading Matching Engine
//!
//! High-performance order matching engine written in Rust for
//! ultra-low latency trade execution.
//!
//! # Architecture
//!
//! - Lock-free order books per symbol
//! - Price-time priority matching
//! - Event sourcing for audit trail
//! - Kafka for event distribution

use anyhow::Result;
use std::sync::Arc;
use tracing::{info, Level};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod api;
mod config;
mod engine;
mod kafka;
mod metrics;
mod orderbook;

use config::Config;
use engine::MatchingEngine;

#[tokio::main]
async fn main() -> Result<()> {
    // Load configuration
    dotenvy::dotenv().ok();
    let config = Config::load()?;

    // Initialize tracing
    init_tracing(&config)?;

    info!(
        "Starting FastTrading Matching Engine v{}",
        env!("CARGO_PKG_VERSION")
    );

    // Initialize metrics
    metrics::init_metrics(&config)?;

    // Create matching engine
    let engine = Arc::new(MatchingEngine::new(&config).await?);

    // Start background workers
    let engine_clone = engine.clone();
    tokio::spawn(async move {
        if let Err(e) = engine_clone.run_matching_loop().await {
            tracing::error!("Matching loop error: {}", e);
        }
    });

    // Start Kafka consumer
    let engine_clone = engine.clone();
    tokio::spawn(async move {
        if let Err(e) = kafka::run_consumer(engine_clone, &config).await {
            tracing::error!("Kafka consumer error: {}", e);
        }
    });

    // Start HTTP API server
    api::run_server(engine, &config).await?;

    Ok(())
}

fn init_tracing(config: &Config) -> Result<()> {
    let env_filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new(&config.log_level));

    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    Ok(())
}
