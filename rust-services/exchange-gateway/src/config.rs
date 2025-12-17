//! Exchange Gateway Configuration

#![allow(dead_code)]

use anyhow::Result;
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    #[serde(default = "default_host")]
    pub host: String,

    #[serde(default = "default_port")]
    pub port: u16,

    #[serde(default = "default_log_level")]
    pub log_level: String,

    pub redis_url: String,
    pub kafka_brokers: String,

    // Ethereum
    pub eth_rpc_url: String,

    #[serde(default = "default_chain_id")]
    pub chain_id: u64,

    // Exchange API Keys (encrypted in production)
    pub binance_api_key: Option<String>,
    pub binance_api_secret: Option<String>,

    pub coinbase_api_key: Option<String>,
    pub coinbase_api_secret: Option<String>,
    pub coinbase_passphrase: Option<String>,
}

fn default_host() -> String {
    "0.0.0.0".to_string()
}
fn default_port() -> u16 {
    8082
}
fn default_log_level() -> String {
    "info".to_string()
}
fn default_chain_id() -> u64 {
    1
}

impl Config {
    pub fn load() -> Result<Self> {
        let config = config::Config::builder()
            .add_source(config::Environment::default().separator("__"))
            .build()?;
        Ok(config.try_deserialize()?)
    }
}
