//! Binance Exchange Adapter
//!
//! Integration with Binance spot trading API

use async_trait::async_trait;
use chrono::Utc;
use hmac::{Hmac, Mac};
use reqwest::Client;
use rust_decimal::Decimal;
use sha2::Sha256;
use std::collections::HashMap;
use tracing::{info, warn};

use super::traits::*;
use common::{ExchangeError, MarketData, Order, Symbol, Trade};

const BINANCE_API_URL: &str = "https://api.binance.com";

pub struct BinanceAdapter {
    client: Client,
    api_key: String,
    api_secret: String,
}

impl BinanceAdapter {
    pub fn new(api_key: String, api_secret: String) -> Self {
        Self {
            client: Client::new(),
            api_key,
            api_secret,
        }
    }

    fn sign(&self, query_string: &str) -> String {
        let mut mac = Hmac::<Sha256>::new_from_slice(self.api_secret.as_bytes())
            .expect("HMAC can take key of any size");
        mac.update(query_string.as_bytes());
        hex::encode(mac.finalize().into_bytes())
    }

    async fn signed_request<T: serde::de::DeserializeOwned>(
        &self,
        method: reqwest::Method,
        endpoint: &str,
        params: &mut HashMap<String, String>,
    ) -> ExchangeResult<T> {
        // Add timestamp
        params.insert(
            "timestamp".to_string(),
            Utc::now().timestamp_millis().to_string(),
        );

        // Build query string
        let query_string: String = params
            .iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join("&");

        // Sign
        let signature = self.sign(&query_string);
        let url = format!(
            "{}{}?{}&signature={}",
            BINANCE_API_URL, endpoint, query_string, signature
        );

        let response = self
            .client
            .request(method, &url)
            .header("X-MBX-APIKEY", &self.api_key)
            .send()
            .await
            .map_err(|e| ExchangeError::ConnectionFailed(e.to_string()))?;

        if !response.status().is_success() {
            let status = response.status();
            let text = response.text().await.unwrap_or_default();
            return Err(ExchangeError::ApiError {
                code: status.as_u16() as i32,
                message: text,
            });
        }

        response.json().await.map_err(|e| ExchangeError::ApiError {
            code: -1,
            message: e.to_string(),
        })
    }
}

#[async_trait]
impl ExchangeAdapter for BinanceAdapter {
    fn name(&self) -> &'static str {
        "Binance"
    }

    async fn is_available(&self) -> bool {
        let result = self
            .client
            .get(format!("{}/api/v3/ping", BINANCE_API_URL))
            .send()
            .await;
        result.is_ok()
    }

    async fn get_symbols(&self) -> ExchangeResult<Vec<Symbol>> {
        #[derive(serde::Deserialize)]
        struct ExchangeInfo {
            symbols: Vec<SymbolInfo>,
        }

        #[derive(serde::Deserialize)]
        struct SymbolInfo {
            symbol: String,
            #[serde(rename = "baseAsset")]
            base_asset: String,
            #[serde(rename = "quoteAsset")]
            quote_asset: String,
            status: String,
        }

        let info: ExchangeInfo = self
            .client
            .get(format!("{}/api/v3/exchangeInfo", BINANCE_API_URL))
            .send()
            .await
            .map_err(|e| ExchangeError::ConnectionFailed(e.to_string()))?
            .json()
            .await
            .map_err(|e| ExchangeError::ApiError {
                code: -1,
                message: e.to_string(),
            })?;

        Ok(info
            .symbols
            .into_iter()
            .filter(|s| s.status == "TRADING")
            .map(|s| Symbol::new(&s.base_asset, &s.quote_asset))
            .collect())
    }

    async fn get_market_data(&self, symbol: &Symbol) -> ExchangeResult<MarketData> {
        #[derive(serde::Deserialize)]
        struct Ticker {
            symbol: String,
            #[serde(rename = "bidPrice")]
            bid_price: String,
            #[serde(rename = "askPrice")]
            ask_price: String,
            #[serde(rename = "lastPrice")]
            last_price: String,
            #[serde(rename = "volume")]
            volume: String,
            #[serde(rename = "highPrice")]
            high_price: String,
            #[serde(rename = "lowPrice")]
            low_price: String,
        }

        let binance_symbol = format!("{}{}", symbol.base(), symbol.quote());

        let ticker: Ticker = self
            .client
            .get(format!(
                "{}/api/v3/ticker/24hr?symbol={}",
                BINANCE_API_URL, binance_symbol
            ))
            .send()
            .await
            .map_err(|e| ExchangeError::ConnectionFailed(e.to_string()))?
            .json()
            .await
            .map_err(|e| ExchangeError::ApiError {
                code: -1,
                message: e.to_string(),
            })?;

        Ok(MarketData {
            symbol: symbol.clone(),
            bid: ticker.bid_price.parse().unwrap_or_default(),
            ask: ticker.ask_price.parse().unwrap_or_default(),
            last: ticker.last_price.parse().unwrap_or_default(),
            volume_24h: ticker.volume.parse().unwrap_or_default(),
            high_24h: ticker.high_price.parse().unwrap_or_default(),
            low_24h: ticker.low_price.parse().unwrap_or_default(),
            timestamp: Utc::now(),
        })
    }

    async fn get_balances(&self) -> ExchangeResult<Vec<ExchangeBalance>> {
        #[derive(serde::Deserialize)]
        struct AccountInfo {
            balances: Vec<BalanceInfo>,
        }

        #[derive(serde::Deserialize)]
        struct BalanceInfo {
            asset: String,
            free: String,
            locked: String,
        }

        let mut params = HashMap::new();
        let account: AccountInfo = self
            .signed_request(reqwest::Method::GET, "/api/v3/account", &mut params)
            .await?;

        Ok(account
            .balances
            .into_iter()
            .filter(|b| {
                let free: Decimal = b.free.parse().unwrap_or_default();
                let locked: Decimal = b.locked.parse().unwrap_or_default();
                free > Decimal::ZERO || locked > Decimal::ZERO
            })
            .map(|b| ExchangeBalance {
                asset: b.asset,
                free: b.free.parse().unwrap_or_default(),
                locked: b.locked.parse().unwrap_or_default(),
            })
            .collect())
    }

    async fn place_order(&self, order: &Order) -> ExchangeResult<ExchangeOrder> {
        let binance_symbol = format!("{}{}", order.symbol.base(), order.symbol.quote());

        let mut params = HashMap::new();
        params.insert("symbol".to_string(), binance_symbol);
        params.insert(
            "side".to_string(),
            if order.side == common::Side::Buy {
                "BUY"
            } else {
                "SELL"
            }
            .to_string(),
        );
        params.insert(
            "type".to_string(),
            match order.order_type {
                common::OrderType::Market => "MARKET",
                common::OrderType::Limit => "LIMIT",
                _ => "LIMIT",
            }
            .to_string(),
        );
        params.insert("quantity".to_string(), order.quantity.to_string());

        if let Some(price) = order.price {
            params.insert("price".to_string(), price.to_string());
            params.insert("timeInForce".to_string(), "GTC".to_string());
        }

        params.insert(
            "newClientOrderId".to_string(),
            order.client_order_id.clone(),
        );

        #[derive(serde::Deserialize)]
        struct OrderResponse {
            #[serde(rename = "orderId")]
            order_id: u64,
            #[serde(rename = "clientOrderId")]
            client_order_id: String,
            status: String,
            #[serde(rename = "executedQty")]
            executed_qty: String,
            #[serde(rename = "avgPrice", default)]
            avg_price: Option<String>,
        }

        let response: OrderResponse = self
            .signed_request(reqwest::Method::POST, "/api/v3/order", &mut params)
            .await?;

        info!(
            order_id = response.order_id,
            status = %response.status,
            "Order placed on Binance"
        );

        Ok(ExchangeOrder {
            exchange_order_id: response.order_id.to_string(),
            client_order_id: response.client_order_id,
            symbol: order.symbol.clone(),
            status: response.status,
            filled_quantity: response.executed_qty.parse().unwrap_or_default(),
            avg_price: response.avg_price.and_then(|p| p.parse().ok()),
        })
    }

    async fn cancel_order(&self, symbol: &Symbol, order_id: &str) -> ExchangeResult<()> {
        let binance_symbol = format!("{}{}", symbol.base(), symbol.quote());

        let mut params = HashMap::new();
        params.insert("symbol".to_string(), binance_symbol);
        params.insert("orderId".to_string(), order_id.to_string());

        let _: serde_json::Value = self
            .signed_request(reqwest::Method::DELETE, "/api/v3/order", &mut params)
            .await?;

        info!(order_id = order_id, "Order cancelled on Binance");

        Ok(())
    }

    async fn get_order(&self, symbol: &Symbol, order_id: &str) -> ExchangeResult<ExchangeOrder> {
        let binance_symbol = format!("{}{}", symbol.base(), symbol.quote());

        let mut params = HashMap::new();
        params.insert("symbol".to_string(), binance_symbol);
        params.insert("orderId".to_string(), order_id.to_string());

        #[derive(serde::Deserialize)]
        struct OrderResponse {
            #[serde(rename = "orderId")]
            order_id: u64,
            #[serde(rename = "clientOrderId")]
            client_order_id: String,
            status: String,
            #[serde(rename = "executedQty")]
            executed_qty: String,
            #[serde(rename = "avgPrice", default)]
            avg_price: Option<String>,
        }

        let response: OrderResponse = self
            .signed_request(reqwest::Method::GET, "/api/v3/order", &mut params)
            .await?;

        Ok(ExchangeOrder {
            exchange_order_id: response.order_id.to_string(),
            client_order_id: response.client_order_id,
            symbol: symbol.clone(),
            status: response.status,
            filled_quantity: response.executed_qty.parse().unwrap_or_default(),
            avg_price: response.avg_price.and_then(|p| p.parse().ok()),
        })
    }

    async fn get_trades(&self, symbol: &Symbol, limit: u32) -> ExchangeResult<Vec<Trade>> {
        // Implementation would fetch recent trades
        Ok(vec![])
    }
}
