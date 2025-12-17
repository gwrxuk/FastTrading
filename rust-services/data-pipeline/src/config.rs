//! Data Pipeline Configuration

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

    #[serde(default = "default_kafka_group")]
    pub kafka_group_id: String,

    #[serde(default = "default_publish_interval")]
    pub publish_interval_ms: u64,

    #[serde(default = "default_candle_intervals")]
    #[allow(dead_code)]
    pub candle_intervals: Vec<String>,
}

fn default_host() -> String {
    "0.0.0.0".to_string()
}
fn default_port() -> u16 {
    8081
}
fn default_log_level() -> String {
    "info".to_string()
}
fn default_kafka_group() -> String {
    "data-pipeline".to_string()
}
fn default_publish_interval() -> u64 {
    100
}
fn default_candle_intervals() -> Vec<String> {
    vec![
        "1m".to_string(),
        "5m".to_string(),
        "1h".to_string(),
        "1d".to_string(),
    ]
}

impl Config {
    pub fn load() -> Result<Self> {
        let config = config::Config::builder()
            .add_source(config::Environment::default().separator("__"))
            .build()?;
        Ok(config.try_deserialize()?)
    }
}
