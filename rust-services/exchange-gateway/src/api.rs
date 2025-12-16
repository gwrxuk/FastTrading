//! Exchange Gateway API

use std::sync::Arc;
use axum::{
    extract::{Path, State},
    routing::get,
    Json, Router,
};
use tower_http::trace::TraceLayer;

use crate::config::Config;
use crate::router::ExchangeRouter;

type AppState = Arc<ExchangeRouter>;

pub async fn run_server(router: Arc<ExchangeRouter>, config: &Config) -> anyhow::Result<()> {
    let app = Router::new()
        .route("/health", get(health))
        .route("/exchanges", get(list_exchanges))
        .route("/exchanges/:name/status", get(exchange_status))
        .with_state(router)
        .layer(TraceLayer::new_for_http());

    let addr = format!("{}:{}", config.host, config.port);
    tracing::info!("Starting exchange gateway API on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "healthy",
        "service": "exchange-gateway"
    }))
}

async fn list_exchanges(State(router): State<AppState>) -> Json<Vec<String>> {
    Json(router.list_exchanges())
}

async fn exchange_status(
    State(router): State<AppState>,
    Path(name): Path<String>,
) -> Json<serde_json::Value> {
    let available = router.is_exchange_available(&name).await;
    
    Json(serde_json::json!({
        "exchange": name,
        "available": available
    }))
}

