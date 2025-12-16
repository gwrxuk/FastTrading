//! Exchange Adapter Traits
//!
//! Defines the interface all exchange adapters must implement

use async_trait::async_trait;
use rust_decimal::Decimal;
use uuid::Uuid;

use common::{Order, Symbol, Trade, MarketData, ExchangeError};

/// Result type for exchange operations
pub type ExchangeResult<T> = Result<T, ExchangeError>;

/// Order response from exchange
#[derive(Debug, Clone)]
pub struct ExchangeOrder {
    pub exchange_order_id: String,
    pub client_order_id: String,
    pub symbol: Symbol,
    pub status: String,
    pub filled_quantity: Decimal,
    pub avg_price: Option<Decimal>,
}

/// Balance on exchange
#[derive(Debug, Clone)]
pub struct ExchangeBalance {
    pub asset: String,
    pub free: Decimal,
    pub locked: Decimal,
}

/// Unified exchange adapter interface
#[async_trait]
pub trait ExchangeAdapter: Send + Sync {
    /// Get exchange name
    fn name(&self) -> &'static str;
    
    /// Check if exchange is available
    async fn is_available(&self) -> bool;
    
    /// Get supported symbols
    async fn get_symbols(&self) -> ExchangeResult<Vec<Symbol>>;
    
    /// Get current market data
    async fn get_market_data(&self, symbol: &Symbol) -> ExchangeResult<MarketData>;
    
    /// Get account balances
    async fn get_balances(&self) -> ExchangeResult<Vec<ExchangeBalance>>;
    
    /// Place order
    async fn place_order(&self, order: &Order) -> ExchangeResult<ExchangeOrder>;
    
    /// Cancel order
    async fn cancel_order(&self, symbol: &Symbol, order_id: &str) -> ExchangeResult<()>;
    
    /// Get order status
    async fn get_order(&self, symbol: &Symbol, order_id: &str) -> ExchangeResult<ExchangeOrder>;
    
    /// Get recent trades
    async fn get_trades(&self, symbol: &Symbol, limit: u32) -> ExchangeResult<Vec<Trade>>;
}

/// DEX-specific adapter interface
#[async_trait]
pub trait DexAdapter: ExchangeAdapter {
    /// Get quote for swap
    async fn get_quote(
        &self,
        token_in: &str,
        token_out: &str,
        amount_in: Decimal,
    ) -> ExchangeResult<Decimal>;
    
    /// Execute swap
    async fn swap(
        &self,
        token_in: &str,
        token_out: &str,
        amount_in: Decimal,
        min_amount_out: Decimal,
        deadline: u64,
    ) -> ExchangeResult<String>; // Returns tx hash
    
    /// Get liquidity pool info
    async fn get_pool_info(&self, token_a: &str, token_b: &str) -> ExchangeResult<PoolInfo>;
}

#[derive(Debug, Clone)]
pub struct PoolInfo {
    pub token_a: String,
    pub token_b: String,
    pub reserve_a: Decimal,
    pub reserve_b: Decimal,
    pub fee: Decimal,
}

