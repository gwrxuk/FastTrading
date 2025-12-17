//! Kafka Consumer for trade events

use anyhow::Result;
use rdkafka::{
    consumer::{Consumer, StreamConsumer},
    ClientConfig, Message,
};
use std::sync::Arc;
use tokio_stream::StreamExt;
use tracing::{error, info, warn};

use crate::aggregator::PriceAggregator;
use crate::config::Config;
use common::events::topics;

pub async fn run_trade_consumer(aggregator: Arc<PriceAggregator>, config: &Config) -> Result<()> {
    let consumer: StreamConsumer = ClientConfig::new()
        .set("bootstrap.servers", &config.kafka_brokers)
        .set("group.id", &config.kafka_group_id)
        .set("enable.auto.commit", "true")
        .set("auto.offset.reset", "latest")
        .create()?;

    consumer.subscribe(&[topics::TRADES])?;

    info!("Trade consumer started, subscribed to {}", topics::TRADES);

    let mut stream = consumer.stream();

    while let Some(message) = stream.next().await {
        match message {
            Ok(msg) => {
                if let Some(payload) = msg.payload() {
                    match serde_json::from_slice::<
                        common::events::Event<common::events::TradeExecuted>,
                    >(payload)
                    {
                        Ok(event) => {
                            if let Err(e) = aggregator.process_trade(event.payload.trade).await {
                                error!("Failed to process trade: {}", e);
                            }
                        }
                        Err(e) => {
                            warn!("Failed to parse trade event: {}", e);
                        }
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
