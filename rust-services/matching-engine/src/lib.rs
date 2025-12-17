//! FastTrading Matching Engine Library
//!
//! High-performance order matching engine written in Rust for
//! ultra-low latency trade execution.
//!
//! # Architecture
//!
//! - Lock-free order books per symbol
//! - Price-time priority matching
//! - Event sourcing for audit trail
//! - Kafka for event distribution

pub mod api;
pub mod config;
pub mod engine;
pub mod kafka;
pub mod metrics;
pub mod orderbook;
