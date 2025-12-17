//! Prometheus metrics for observability
//!
//! Exposes metrics for:
//! - Order processing latency
//! - Trade execution counts
//! - Order book depth
//! - System health

use anyhow::Result;
use metrics_exporter_prometheus::PrometheusBuilder;
use std::net::SocketAddr;

use crate::config::Config;

/// Initialize metrics exporter
pub fn init_metrics(config: &Config) -> Result<()> {
    let addr: SocketAddr = format!("0.0.0.0:{}", config.metrics_port).parse()?;

    PrometheusBuilder::new()
        .with_http_listener(addr)
        .install()?;

    // Register standard metrics
    metrics::describe_histogram!(
        "matching_latency_us",
        "Order matching latency in microseconds"
    );

    metrics::describe_counter!("orders_received", "Total orders received");

    metrics::describe_counter!("orders_matched", "Total orders matched");

    metrics::describe_counter!("orders_cancelled", "Total orders cancelled");

    metrics::describe_counter!("trades_executed", "Total trades executed");

    metrics::describe_gauge!("orderbook_depth_bids", "Number of bid levels in order book");

    metrics::describe_gauge!("orderbook_depth_asks", "Number of ask levels in order book");

    tracing::info!("Metrics server started on port {}", config.metrics_port);

    Ok(())
}
