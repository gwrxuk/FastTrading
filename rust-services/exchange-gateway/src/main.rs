//! FastTrading Exchange Gateway
//!
//! Provides unified interface for:
//! - Centralized exchanges (Binance, Coinbase, etc.)
//! - DEX integrations (Uniswap, SushiSwap, etc.)
//! - DeFi protocols (Aave, Compound, etc.)

use anyhow::Result;
use std::sync::Arc;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod adapters;
mod api;
mod config;
mod router;

use config::Config;

#[tokio::main]
async fn main() -> Result<()> {
    dotenvy::dotenv().ok();
    let config = Config::load()?;

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(&config.log_level))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    info!(
        "Starting FastTrading Exchange Gateway v{}",
        env!("CARGO_PKG_VERSION")
    );

    // Initialize exchange adapters
    let exchange_router = Arc::new(router::ExchangeRouter::new(&config).await?);

    // Start API server
    api::run_server(exchange_router, &config).await?;

    Ok(())
}
