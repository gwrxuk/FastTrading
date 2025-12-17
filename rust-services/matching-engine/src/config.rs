//! Configuration management
//!
//! Loads configuration from environment variables and config files
//! with sensible defaults for development.

use anyhow::Result;
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    // Server
    #[serde(default = "default_host")]
    pub host: String,

    #[serde(default = "default_port")]
    pub port: u16,

    // Logging
    #[serde(default = "default_log_level")]
    pub log_level: String,

    // Database
    pub database_url: String,

    #[serde(default = "default_pool_size")]
    pub database_pool_size: u32,

    // Redis
    pub redis_url: String,

    // Kafka
    pub kafka_brokers: String,

    #[serde(default = "default_kafka_group")]
    pub kafka_group_id: String,

    // Matching Engine
    #[serde(default = "default_matching_interval")]
    pub matching_interval_us: u64,

    #[serde(default = "default_max_orders_per_symbol")]
    pub max_orders_per_symbol: usize,

    // Observability
    #[serde(default)]
    pub otlp_endpoint: Option<String>,

    #[serde(default = "default_metrics_port")]
    pub metrics_port: u16,
}

fn default_host() -> String {
    "0.0.0.0".to_string()
}

fn default_port() -> u16 {
    8080
}

fn default_log_level() -> String {
    "info".to_string()
}

fn default_pool_size() -> u32 {
    20
}

fn default_kafka_group() -> String {
    "matching-engine".to_string()
}

fn default_matching_interval() -> u64 {
    100 // 100 microseconds
}

fn default_max_orders_per_symbol() -> usize {
    100_000
}

fn default_metrics_port() -> u16 {
    9090
}

impl Config {
    pub fn load() -> Result<Self> {
        let config = config::Config::builder()
            .add_source(config::Environment::default().separator("__"))
            .build()?;

        Ok(config.try_deserialize()?)
    }
}
