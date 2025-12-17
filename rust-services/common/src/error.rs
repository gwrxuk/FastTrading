//! Error types for trading platform
//!
//! Comprehensive error handling with context for debugging
//! and appropriate error codes for API responses.

use thiserror::Error;

/// Trading engine errors
#[derive(Error, Debug)]
pub enum TradingError {
    #[error("Order not found: {0}")]
    OrderNotFound(String),

    #[error("Insufficient balance: required {required}, available {available}")]
    InsufficientBalance { required: String, available: String },

    #[error("Invalid order: {0}")]
    InvalidOrder(String),

    #[error("Order rejected: {0}")]
    OrderRejected(String),

    #[error("Symbol not found: {0}")]
    SymbolNotFound(String),

    #[error("Rate limit exceeded")]
    RateLimitExceeded,

    #[error("Market closed")]
    MarketClosed,

    #[error("Self-trade prevention triggered")]
    SelfTradePrevention,
}

/// Data pipeline errors
#[derive(Error, Debug)]
pub enum PipelineError {
    #[error("Kafka error: {0}")]
    Kafka(String),

    #[error("Redis error: {0}")]
    Redis(String),

    #[error("Serialization error: {0}")]
    Serialization(String),

    #[error("Connection lost: {0}")]
    ConnectionLost(String),

    #[error("Timeout: operation took longer than {0}ms")]
    Timeout(u64),
}

/// Exchange gateway errors
#[derive(Error, Debug)]
pub enum ExchangeError {
    #[error("Exchange connection failed: {0}")]
    ConnectionFailed(String),

    #[error("Authentication failed: {0}")]
    AuthenticationFailed(String),

    #[error("API error: {code} - {message}")]
    ApiError { code: i32, message: String },

    #[error("Rate limited by exchange")]
    RateLimited,

    #[error("Order rejected by exchange: {0}")]
    OrderRejected(String),

    #[error("Unsupported operation: {0}")]
    UnsupportedOperation(String),
}

/// Database errors
#[derive(Error, Debug)]
pub enum DatabaseError {
    #[error("Query failed: {0}")]
    QueryFailed(String),

    #[error("Connection pool exhausted")]
    PoolExhausted,

    #[error("Transaction failed: {0}")]
    TransactionFailed(String),

    #[error("Constraint violation: {0}")]
    ConstraintViolation(String),

    #[error("Serialization conflict - retry transaction")]
    SerializationConflict,
}

/// Generic service error that wraps all specific errors
#[derive(Error, Debug)]
pub enum ServiceError {
    #[error(transparent)]
    Trading(#[from] TradingError),

    #[error(transparent)]
    Pipeline(#[from] PipelineError),

    #[error(transparent)]
    Exchange(#[from] ExchangeError),

    #[error(transparent)]
    Database(#[from] DatabaseError),

    #[error("Internal error: {0}")]
    Internal(String),

    #[error("Configuration error: {0}")]
    Configuration(String),
}

impl ServiceError {
    /// Get HTTP status code for this error
    pub fn status_code(&self) -> u16 {
        match self {
            ServiceError::Trading(TradingError::OrderNotFound(_)) => 404,
            ServiceError::Trading(TradingError::SymbolNotFound(_)) => 404,
            ServiceError::Trading(TradingError::InsufficientBalance { .. }) => 400,
            ServiceError::Trading(TradingError::InvalidOrder(_)) => 400,
            ServiceError::Trading(TradingError::RateLimitExceeded) => 429,
            ServiceError::Trading(_) => 400,
            ServiceError::Exchange(ExchangeError::RateLimited) => 429,
            ServiceError::Exchange(ExchangeError::AuthenticationFailed(_)) => 401,
            ServiceError::Exchange(_) => 502,
            ServiceError::Pipeline(_) => 503,
            ServiceError::Database(_) => 503,
            ServiceError::Internal(_) => 500,
            ServiceError::Configuration(_) => 500,
        }
    }

    /// Get error code for API responses
    pub fn error_code(&self) -> &'static str {
        match self {
            ServiceError::Trading(TradingError::OrderNotFound(_)) => "ORDER_NOT_FOUND",
            ServiceError::Trading(TradingError::InsufficientBalance { .. }) => {
                "INSUFFICIENT_BALANCE"
            }
            ServiceError::Trading(TradingError::InvalidOrder(_)) => "INVALID_ORDER",
            ServiceError::Trading(TradingError::RateLimitExceeded) => "RATE_LIMIT_EXCEEDED",
            ServiceError::Trading(_) => "TRADING_ERROR",
            ServiceError::Exchange(_) => "EXCHANGE_ERROR",
            ServiceError::Pipeline(_) => "PIPELINE_ERROR",
            ServiceError::Database(_) => "DATABASE_ERROR",
            ServiceError::Internal(_) => "INTERNAL_ERROR",
            ServiceError::Configuration(_) => "CONFIG_ERROR",
        }
    }
}
