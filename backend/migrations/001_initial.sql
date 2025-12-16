-- FastTrading Database Migration 001
-- Initial schema with TimescaleDB optimizations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    eth_address VARCHAR(42) UNIQUE,
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,
    is_2fa_enabled BOOLEAN DEFAULT false NOT NULL,
    daily_trade_limit NUMERIC(20, 8) DEFAULT 100000.0,
    daily_withdrawal_limit NUMERIC(20, 8) DEFAULT 10000.0,
    kyc_level VARCHAR(20) DEFAULT 'basic',
    api_key VARCHAR(64) UNIQUE,
    api_secret VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_eth_address ON users(eth_address);
CREATE INDEX ix_users_api_key ON users(api_key);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_order_id VARCHAR(64) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    time_in_force VARCHAR(10) DEFAULT 'gtc' NOT NULL,
    price NUMERIC(20, 8),
    stop_price NUMERIC(20, 8),
    quantity NUMERIC(20, 8) NOT NULL,
    filled_quantity NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    remaining_quantity NUMERIC(20, 8) NOT NULL,
    average_fill_price NUMERIC(20, 8),
    commission NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    commission_asset VARCHAR(10),
    sequence_number BIGSERIAL NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Optimized indexes for order matching
CREATE INDEX ix_orders_symbol_status ON orders(symbol, status);
CREATE INDEX ix_orders_symbol_side_price ON orders(symbol, side, price);
CREATE INDEX ix_orders_user_status ON orders(user_id, status);
CREATE INDEX ix_orders_matching ON orders(symbol, status, side, price, sequence_number);
CREATE INDEX ix_orders_created_at ON orders(created_at DESC);

-- Trades table with TimescaleDB
CREATE TABLE trades (
    id UUID DEFAULT uuid_generate_v4(),
    trade_id BIGSERIAL UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    order_id UUID NOT NULL REFERENCES orders(id),
    counterparty_order_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    quantity NUMERIC(20, 8) NOT NULL,
    quote_quantity NUMERIC(20, 8) NOT NULL,
    commission NUMERIC(20, 8) NOT NULL,
    commission_asset VARCHAR(10) NOT NULL,
    is_maker VARCHAR(10) NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL,
    tx_hash VARCHAR(66),
    block_number BIGINT,
    PRIMARY KEY (id, executed_at)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('trades', 'executed_at', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes on hypertable
CREATE INDEX ix_trades_symbol_time ON trades(symbol, executed_at DESC);
CREATE INDEX ix_trades_user_time ON trades(user_id, executed_at DESC);
CREATE INDEX ix_trades_order ON trades(order_id);

-- Wallets table
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    wallet_type VARCHAR(10) NOT NULL,
    address VARCHAR(42) UNIQUE NOT NULL,
    chain VARCHAR(20) DEFAULT 'ethereum' NOT NULL,
    currency VARCHAR(10) NOT NULL,
    balance NUMERIC(30, 18) DEFAULT 0 NOT NULL,
    locked_balance NUMERIC(30, 18) DEFAULT 0 NOT NULL,
    nonce BIGINT DEFAULT 0 NOT NULL,
    is_verified VARCHAR(10) DEFAULT 'pending',
    signature_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_wallets_user_currency ON wallets(user_id, currency);
CREATE INDEX ix_wallets_chain_address ON wallets(chain, address);

-- Transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    user_id UUID NOT NULL REFERENCES users(id),
    tx_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    tx_hash VARCHAR(66) UNIQUE,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    amount NUMERIC(30, 18) NOT NULL,
    gas_limit BIGINT,
    gas_price NUMERIC(30, 18),
    gas_used BIGINT,
    block_number BIGINT,
    confirmations BIGINT DEFAULT 0 NOT NULL,
    required_confirmations BIGINT DEFAULT 12 NOT NULL,
    raw_tx TEXT,
    signed_tx TEXT,
    error_message TEXT,
    retry_count BIGINT DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_transactions_status_type ON transactions(status, tx_type);
CREATE INDEX ix_transactions_user_status ON transactions(user_id, status);
CREATE INDEX ix_transactions_tx_hash ON transactions(tx_hash);

-- Market data table (for caching)
CREATE TABLE market_data (
    symbol VARCHAR(20) NOT NULL,
    bid NUMERIC(20, 8) NOT NULL,
    ask NUMERIC(20, 8) NOT NULL,
    last NUMERIC(20, 8) NOT NULL,
    volume_24h NUMERIC(30, 8) NOT NULL,
    high_24h NUMERIC(20, 8) NOT NULL,
    low_24h NUMERIC(20, 8) NOT NULL,
    change_24h NUMERIC(20, 8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (symbol, timestamp)
);

SELECT create_hypertable('market_data', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Candles table for OHLCV data
CREATE TABLE candles (
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(10) NOT NULL,
    open_time TIMESTAMPTZ NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(30, 8) NOT NULL,
    close_time TIMESTAMPTZ NOT NULL,
    quote_volume NUMERIC(30, 8) NOT NULL,
    trade_count INTEGER NOT NULL,
    PRIMARY KEY (symbol, interval, open_time)
);

SELECT create_hypertable('candles', 'open_time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX ix_candles_lookup ON candles(symbol, interval, open_time DESC);

-- Continuous aggregate for 1-minute candles (auto-updated)
CREATE MATERIALIZED VIEW candles_1m
WITH (timescaledb.continuous) AS
SELECT 
    symbol,
    time_bucket('1 minute', executed_at) AS open_time,
    first(price, executed_at) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price, executed_at) AS close,
    sum(quantity) AS volume,
    sum(quote_quantity) AS quote_volume,
    count(*) AS trade_count
FROM trades
GROUP BY symbol, time_bucket('1 minute', executed_at);

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('candles_1m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

-- Data retention policy - keep trade data for 1 year
SELECT add_retention_policy('trades', INTERVAL '365 days');
SELECT add_retention_policy('market_data', INTERVAL '30 days');

-- Compression policy for older data
ALTER TABLE trades SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('trades', INTERVAL '7 days');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_wallets_updated_at
    BEFORE UPDATE ON wallets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading;

