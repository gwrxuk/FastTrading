//! Kafka consumer for order events
//!
//! Consumes orders from Kafka topics and forwards to matching engine

use std::sync::Arc;
use anyhow::Result;
use rdkafka::{
    consumer::{Consumer, StreamConsumer},
    ClientConfig, Message,
};
use tokio_stream::StreamExt;
use tracing::{error, info, warn};

use common::{events::topics, Order};
use crate::config::Config;
use crate::engine::MatchingEngine;

/// Run Kafka consumer
pub async fn run_consumer(engine: Arc<MatchingEngine>, config: &Config) -> Result<()> {
    let consumer: StreamConsumer = ClientConfig::new()
        .set("bootstrap.servers", &config.kafka_brokers)
        .set("group.id", &config.kafka_group_id)
        .set("enable.auto.commit", "true")
        .set("auto.offset.reset", "latest")
        .set("session.timeout.ms", "10000")
        .create()?;

    consumer.subscribe(&[topics::ORDERS])?;

    info!("Kafka consumer started, subscribed to {}", topics::ORDERS);

    let mut stream = consumer.stream();

    while let Some(message) = stream.next().await {
        match message {
            Ok(msg) => {
                if let Some(payload) = msg.payload() {
                    if let Err(e) = process_message(&engine, payload).await {
                        error!("Failed to process message: {}", e);
                    }
                }
            }
            Err(e) => {
                warn!("Kafka error: {}", e);
            }
        }
    }

    Ok(())
}

async fn process_message(engine: &MatchingEngine, payload: &[u8]) -> Result<()> {
    // Try to parse as an order
    let order: Order = serde_json::from_slice(payload)?;
    
    info!(order_id = %order.id, "Received order from Kafka");
    
    engine.submit_order(order).await?;
    
    Ok(())
}

