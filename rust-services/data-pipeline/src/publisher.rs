//! Price Publisher and API Server

use std::sync::Arc;
use std::time::Duration;

use axum::{routing::get, Json, Router};
use tokio::time;
use tower_http::trace::TraceLayer;
use tracing::info;

use crate::aggregator::PriceAggregator;
use crate::config::Config;

/// Run price publisher task
pub async fn run_price_publisher(
    aggregator: Arc<PriceAggregator>,
    config: &Config,
) -> anyhow::Result<()> {
    let mut interval = time::interval(Duration::from_millis(config.publish_interval_ms));

    info!(
        "Price publisher started with {}ms interval",
        config.publish_interval_ms
    );

    loop {
        interval.tick().await;

        // Get all market data and publish
        let market_data = aggregator.get_all_market_data();

        for data in market_data {
            // Publish to Redis pub/sub
            // This is picked up by WebSocket servers
            metrics::gauge!("last_price", "symbol" => data.symbol.to_string())
                .set(data.last.to_string().parse::<f64>().unwrap_or(0.0));
        }
    }
}

/// Run API server for health checks
pub async fn run_api_server(config: &Config) -> anyhow::Result<()> {
    let app = Router::new()
        .route("/health", get(health))
        .route("/ready", get(ready))
        .layer(TraceLayer::new_for_http());

    let addr = format!("{}:{}", config.host, config.port);
    info!("Starting data pipeline API on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "healthy",
        "service": "data-pipeline"
    }))
}

async fn ready() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "ready": true
    }))
}
