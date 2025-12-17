//! Exchange Adapters
//!
//! Unified interface for different exchanges and protocols

pub mod binance;
pub mod traits;
pub mod uniswap;

pub use traits::*;
