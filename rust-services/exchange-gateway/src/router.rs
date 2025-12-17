//! Exchange Router
//!
//! Routes orders to appropriate exchanges based on configuration

use anyhow::Result;
use std::collections::HashMap;
use std::sync::Arc;

use crate::adapters::{BinanceAdapter, ExchangeAdapter, UniswapAdapter};
use crate::config::Config;
use common::{ExchangeError, Symbol};

pub struct ExchangeRouter {
    exchanges: HashMap<String, Arc<dyn ExchangeAdapter>>,
    symbol_routing: HashMap<String, String>, // symbol -> exchange name
}

impl ExchangeRouter {
    pub async fn new(config: &Config) -> Result<Self> {
        let mut exchanges: HashMap<String, Arc<dyn ExchangeAdapter>> = HashMap::new();

        // Initialize Binance if configured
        if let (Some(key), Some(secret)) = (&config.binance_api_key, &config.binance_api_secret) {
            let binance = BinanceAdapter::new(key.clone(), secret.clone());
            if binance.is_available().await {
                exchanges.insert("binance".to_string(), Arc::new(binance));
                tracing::info!("Binance adapter initialized");
            }
        }

        // Initialize Uniswap
        match UniswapAdapter::new(&config.eth_rpc_url, config.chain_id) {
            Ok(uniswap) => {
                if uniswap.is_available().await {
                    exchanges.insert("uniswap".to_string(), Arc::new(uniswap));
                    tracing::info!("Uniswap adapter initialized");
                }
            }
            Err(e) => {
                tracing::warn!("Failed to initialize Uniswap: {}", e);
            }
        }

        // Default routing (can be configured)
        let symbol_routing = HashMap::new();

        Ok(Self {
            exchanges,
            symbol_routing,
        })
    }

    /// Get exchange adapter by name
    pub fn get_exchange(&self, name: &str) -> Option<&Arc<dyn ExchangeAdapter>> {
        self.exchanges.get(name)
    }

    /// Get exchange for a symbol
    pub fn get_exchange_for_symbol(&self, symbol: &Symbol) -> Option<&Arc<dyn ExchangeAdapter>> {
        let exchange_name = self
            .symbol_routing
            .get(&symbol.to_string())
            .cloned()
            .unwrap_or_else(|| "binance".to_string()); // Default to Binance

        self.exchanges.get(&exchange_name)
    }

    /// List all available exchanges
    pub fn list_exchanges(&self) -> Vec<String> {
        self.exchanges.keys().cloned().collect()
    }

    /// Check if exchange is available
    pub async fn is_exchange_available(&self, name: &str) -> bool {
        if let Some(exchange) = self.exchanges.get(name) {
            exchange.is_available().await
        } else {
            false
        }
    }
}
