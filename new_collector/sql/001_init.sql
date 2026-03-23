BEGIN;

CREATE SCHEMA IF NOT EXISTS collector_v2;

CREATE TABLE IF NOT EXISTS collector_v2.tick_trade (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    trade_id TEXT,
    event_time_utc TIMESTAMPTZ NOT NULL,
    price NUMERIC(20, 10) NOT NULL,
    quantity NUMERIC(20, 10) NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, symbol, trade_id)
);

CREATE INDEX IF NOT EXISTS idx_tick_trade_symbol_event_time
    ON collector_v2.tick_trade (symbol, event_time_utc DESC);

CREATE INDEX IF NOT EXISTS idx_tick_trade_event_time
    ON collector_v2.tick_trade (event_time_utc DESC);

CREATE INDEX IF NOT EXISTS idx_tick_trade_ingested_at
    ON collector_v2.tick_trade (ingested_at_utc DESC);

CREATE TABLE IF NOT EXISTS collector_v2.api_client (
    client_id TEXT PRIMARY KEY,
    nickname TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    api_key_hash TEXT NOT NULL UNIQUE,
    note TEXT,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at_utc TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_api_client_status
    ON collector_v2.api_client (status);

CREATE TABLE IF NOT EXISTS collector_v2.api_access_log (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT,
    nickname TEXT,
    request_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    endpoint TEXT NOT NULL,
    symbol TEXT,
    range_from_utc TIMESTAMPTZ,
    range_to_utc TIMESTAMPTZ,
    request_status TEXT NOT NULL,
    row_count INTEGER,
    remote_addr TEXT,
    note TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_access_log_client_time
    ON collector_v2.api_access_log (client_id, request_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_api_access_log_time
    ON collector_v2.api_access_log (request_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_api_access_log_symbol_time
    ON collector_v2.api_access_log (symbol, request_at_utc DESC);

CREATE TABLE IF NOT EXISTS collector_v2.system_checkpoint (
    checkpoint_name TEXT PRIMARY KEY,
    checkpoint_value TEXT NOT NULL,
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
