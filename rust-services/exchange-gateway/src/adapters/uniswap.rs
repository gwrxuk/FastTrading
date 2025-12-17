//! Uniswap DEX Adapter
//!
//! Integration with Uniswap V3 for on-chain swaps

use async_trait::async_trait;
use chrono::Utc;
use ethers::{
    prelude::*,
    providers::{Http, Provider},
    types::{Address, U256},
};
use rust_decimal::Decimal;
use std::sync::Arc;
use tracing::info;

use super::traits::*;
use common::{ExchangeError, MarketData, Order, Symbol, Trade};

// Uniswap V3 Router address on mainnet
const UNISWAP_ROUTER: &str = "0xE592427A0AEce92De3Edee1F18E0157C05861564";

pub struct UniswapAdapter {
    provider: Arc<Provider<Http>>,
    chain_id: u64,
}

impl UniswapAdapter {
    pub fn new(rpc_url: &str, chain_id: u64) -> Result<Self, ExchangeError> {
        let provider = Provider::<Http>::try_from(rpc_url)
            .map_err(|e| ExchangeError::ConnectionFailed(e.to_string()))?;

        Ok(Self {
            provider: Arc::new(provider),
            chain_id,
        })
    }

    fn parse_address(addr: &str) -> Result<Address, ExchangeError> {
        addr.parse().map_err(|_| ExchangeError::ApiError {
            code: -1,
            message: format!("Invalid address: {}", addr),
        })
    }
}

#[async_trait]
impl ExchangeAdapter for UniswapAdapter {
    fn name(&self) -> &'static str {
        "Uniswap V3"
    }

    async fn is_available(&self) -> bool {
        self.provider.get_block_number().await.is_ok()
    }

    async fn get_symbols(&self) -> ExchangeResult<Vec<Symbol>> {
        // Return common trading pairs
        Ok(vec![
            Symbol::new("ETH", "USDC"),
            Symbol::new("ETH", "USDT"),
            Symbol::new("WBTC", "ETH"),
            Symbol::new("LINK", "ETH"),
            Symbol::new("UNI", "ETH"),
        ])
    }

    async fn get_market_data(&self, symbol: &Symbol) -> ExchangeResult<MarketData> {
        // Would query Uniswap pools for current price
        // This is a simplified implementation
        Ok(MarketData {
            symbol: symbol.clone(),
            bid: Decimal::ZERO,
            ask: Decimal::ZERO,
            last: Decimal::ZERO,
            volume_24h: Decimal::ZERO,
            high_24h: Decimal::ZERO,
            low_24h: Decimal::ZERO,
            timestamp: Utc::now(),
        })
    }

    async fn get_balances(&self) -> ExchangeResult<Vec<ExchangeBalance>> {
        // Would query wallet balances
        Ok(vec![])
    }

    async fn place_order(&self, _order: &Order) -> ExchangeResult<ExchangeOrder> {
        Err(ExchangeError::UnsupportedOperation(
            "Use swap() for DEX trades".to_string(),
        ))
    }

    async fn cancel_order(&self, _symbol: &Symbol, _order_id: &str) -> ExchangeResult<()> {
        Err(ExchangeError::UnsupportedOperation(
            "DEX orders cannot be cancelled".to_string(),
        ))
    }

    async fn get_order(&self, _symbol: &Symbol, _order_id: &str) -> ExchangeResult<ExchangeOrder> {
        Err(ExchangeError::UnsupportedOperation(
            "Use transaction hash for DEX trades".to_string(),
        ))
    }

    async fn get_trades(&self, _symbol: &Symbol, _limit: u32) -> ExchangeResult<Vec<Trade>> {
        Ok(vec![])
    }
}

#[async_trait]
impl DexAdapter for UniswapAdapter {
    async fn get_quote(
        &self,
        token_in: &str,
        token_out: &str,
        amount_in: Decimal,
    ) -> ExchangeResult<Decimal> {
        info!(
            token_in = token_in,
            token_out = token_out,
            amount = %amount_in,
            "Getting Uniswap quote"
        );

        // Would call Uniswap Quoter contract
        // This is a placeholder
        Ok(amount_in)
    }

    async fn swap(
        &self,
        token_in: &str,
        token_out: &str,
        amount_in: Decimal,
        min_amount_out: Decimal,
        deadline: u64,
    ) -> ExchangeResult<String> {
        info!(
            token_in = token_in,
            token_out = token_out,
            amount_in = %amount_in,
            min_out = %min_amount_out,
            "Executing Uniswap swap"
        );

        // Would build and send swap transaction
        // This requires wallet/signer integration

        Err(ExchangeError::UnsupportedOperation(
            "Swap execution requires wallet configuration".to_string(),
        ))
    }

    async fn get_pool_info(&self, token_a: &str, token_b: &str) -> ExchangeResult<PoolInfo> {
        // Would query pool contract for reserves
        Ok(PoolInfo {
            token_a: token_a.to_string(),
            token_b: token_b.to_string(),
            reserve_a: Decimal::ZERO,
            reserve_b: Decimal::ZERO,
            fee: Decimal::new(3, 3), // 0.3%
        })
    }
}
