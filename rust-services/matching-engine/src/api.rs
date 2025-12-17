//! HTTP API for the Matching Engine
//!
//! Exposes REST endpoints for order management and market data

use std::sync::Arc;

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{delete, get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use tower_http::{
    compression::CompressionLayer,
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};
use uuid::Uuid;

use crate::config::Config;
use crate::engine::MatchingEngine;
use common::{Order, OrderStatus, OrderType, PriceLevel, Side, Symbol, TimeInForce};

type AppState = Arc<MatchingEngine>;

/// Run the HTTP server
pub async fn run_server(engine: Arc<MatchingEngine>, config: &Config) -> anyhow::Result<()> {
    let app = Router::new()
        // Health & Info
        .route("/health", get(health_check))
        .route("/info", get(info))
        // Orders
        .route("/orders", post(submit_order))
        .route("/orders/:order_id", delete(cancel_order))
        // Market Data
        .route("/orderbook/:symbol", get(get_orderbook))
        .route("/symbols", get(get_symbols))
        // State
        .with_state(engine)
        // Middleware
        .layer(TraceLayer::new_for_http())
        .layer(CompressionLayer::new())
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        );

    let addr = format!("{}:{}", config.host, config.port);
    tracing::info!("Starting HTTP server on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

// ============== Request/Response Types ==============

#[derive(Debug, Deserialize)]
pub struct SubmitOrderRequest {
    pub client_order_id: Option<String>,
    pub symbol: String,
    pub side: Side,
    pub order_type: OrderType,
    pub quantity: String,
    pub price: Option<String>,
    pub time_in_force: Option<TimeInForce>,
    pub user_id: Uuid,
}

#[derive(Debug, Serialize)]
pub struct OrderResponse {
    pub id: Uuid,
    pub client_order_id: String,
    pub symbol: String,
    pub side: Side,
    pub order_type: OrderType,
    pub status: OrderStatus,
    pub quantity: String,
    pub price: Option<String>,
    pub filled_quantity: String,
    pub remaining_quantity: String,
}

#[derive(Debug, Serialize)]
pub struct OrderBookResponse {
    pub symbol: String,
    pub bids: Vec<PriceLevel>,
    pub asks: Vec<PriceLevel>,
    pub sequence: u64,
}

#[derive(Debug, Deserialize)]
pub struct OrderBookQuery {
    pub levels: Option<usize>,
}

#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: &'static str,
    pub version: &'static str,
}

#[derive(Debug, Serialize)]
pub struct InfoResponse {
    pub name: &'static str,
    pub version: &'static str,
    pub symbols: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct ApiError {
    pub error: String,
    pub code: String,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        (StatusCode::BAD_REQUEST, Json(self)).into_response()
    }
}

// ============== Handlers ==============

async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy",
        version: env!("CARGO_PKG_VERSION"),
    })
}

async fn info(State(engine): State<AppState>) -> Json<InfoResponse> {
    Json(InfoResponse {
        name: "FastTrading Matching Engine",
        version: env!("CARGO_PKG_VERSION"),
        symbols: engine.symbols().iter().map(|s| s.to_string()).collect(),
    })
}

async fn submit_order(
    State(engine): State<AppState>,
    Json(req): Json<SubmitOrderRequest>,
) -> Result<Json<OrderResponse>, ApiError> {
    use chrono::Utc;
    use rust_decimal::Decimal;
    use std::str::FromStr;

    // Parse quantity
    let quantity = Decimal::from_str(&req.quantity).map_err(|_| ApiError {
        error: "Invalid quantity".to_string(),
        code: "INVALID_QUANTITY".to_string(),
    })?;

    // Parse price
    let price = req
        .price
        .as_ref()
        .map(|p| Decimal::from_str(p))
        .transpose()
        .map_err(|_| ApiError {
            error: "Invalid price".to_string(),
            code: "INVALID_PRICE".to_string(),
        })?;

    // Validate limit order has price
    if req.order_type == OrderType::Limit && price.is_none() {
        return Err(ApiError {
            error: "Limit order requires price".to_string(),
            code: "PRICE_REQUIRED".to_string(),
        });
    }

    // Parse symbol
    let parts: Vec<&str> = req.symbol.split('-').collect();
    if parts.len() != 2 {
        return Err(ApiError {
            error: "Invalid symbol format".to_string(),
            code: "INVALID_SYMBOL".to_string(),
        });
    }
    let symbol = Symbol::new(parts[0], parts[1]);

    // Create order
    let order = Order {
        id: Uuid::new_v4(),
        client_order_id: req
            .client_order_id
            .unwrap_or_else(|| Uuid::new_v4().to_string()),
        user_id: req.user_id,
        symbol,
        side: req.side,
        order_type: req.order_type,
        time_in_force: req.time_in_force.unwrap_or(TimeInForce::GTC),
        status: OrderStatus::Pending,
        price,
        stop_price: None,
        quantity,
        filled_quantity: Decimal::ZERO,
        remaining_quantity: quantity,
        avg_fill_price: None,
        sequence: 0,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };

    // Submit to engine
    engine
        .submit_order(order.clone())
        .await
        .map_err(|e| ApiError {
            error: e.to_string(),
            code: "SUBMIT_FAILED".to_string(),
        })?;

    Ok(Json(OrderResponse {
        id: order.id,
        client_order_id: order.client_order_id,
        symbol: order.symbol.to_string(),
        side: order.side,
        order_type: order.order_type,
        status: OrderStatus::Pending,
        quantity: order.quantity.to_string(),
        price: order.price.map(|p| p.to_string()),
        filled_quantity: "0".to_string(),
        remaining_quantity: order.quantity.to_string(),
    }))
}

async fn cancel_order(
    State(engine): State<AppState>,
    Path(order_id): Path<Uuid>,
    Query(params): Query<CancelQuery>,
) -> Result<StatusCode, ApiError> {
    let symbol = Symbol::new(
        &params.base.unwrap_or_else(|| "ETH".to_string()),
        &params.quote.unwrap_or_else(|| "USDT".to_string()),
    );

    engine
        .cancel_order(order_id, symbol)
        .await
        .map_err(|e| ApiError {
            error: e.to_string(),
            code: "CANCEL_FAILED".to_string(),
        })?;

    Ok(StatusCode::NO_CONTENT)
}

#[derive(Debug, Deserialize)]
pub struct CancelQuery {
    pub base: Option<String>,
    pub quote: Option<String>,
}

async fn get_orderbook(
    State(engine): State<AppState>,
    Path(symbol): Path<String>,
    Query(query): Query<OrderBookQuery>,
) -> Result<Json<OrderBookResponse>, ApiError> {
    let parts: Vec<&str> = symbol.split('-').collect();
    if parts.len() != 2 {
        return Err(ApiError {
            error: "Invalid symbol format".to_string(),
            code: "INVALID_SYMBOL".to_string(),
        });
    }

    let sym = Symbol::new(parts[0], parts[1]);
    let levels = query.levels.unwrap_or(20);

    let (bids, asks) = engine.get_depth(&sym, levels).map_err(|e| ApiError {
        error: e.to_string(),
        code: "SYMBOL_NOT_FOUND".to_string(),
    })?;

    Ok(Json(OrderBookResponse {
        symbol,
        bids,
        asks,
        sequence: 0, // TODO: get from order book
    }))
}

async fn get_symbols(State(engine): State<AppState>) -> Json<Vec<String>> {
    Json(engine.symbols().iter().map(|s| s.to_string()).collect())
}
