//! Common types and utilities for FastTrading Rust services
//!
//! This crate provides shared data structures, error types, and utilities
//! used across all microservices in the trading platform.

pub mod types;
pub mod error;
pub mod events;

pub use types::*;
pub use error::*;
pub use events::*;

