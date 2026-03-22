-- Block 2: initial PostgreSQL schema for Jack/Data_collector

CREATE SCHEMA IF NOT EXISTS collector;

CREATE TABLE IF NOT EXISTS collector.raw_trades (
    id BIGSERIAL PRIMARY KEY,
    event_time_utc TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price NUMERIC(24, 12) NOT NULL,
    quantity NUMERIC(24, 12) NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    trade_id BIGINT NOT NULL,
    source TEXT NOT NULL,
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trade_day_utc DATE GENERATED ALWAYS AS ((event_time_utc AT TIME ZONE 'UTC')::date) STORED,
    quote_notional NUMERIC(36, 12) GENERATED ALWAYS AS (price * quantity) STORED,
    CONSTRAINT raw_trades_source_symbol_trade_id_key UNIQUE (source, symbol, trade_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_trades_symbol_event_time
    ON collector.raw_trades (symbol, event_time_utc);

CREATE INDEX IF NOT EXISTS idx_raw_trades_trade_day_utc
    ON collector.raw_trades (trade_day_utc);

CREATE INDEX IF NOT EXISTS idx_raw_trades_symbol_trade_day_utc
    ON collector.raw_trades (symbol, trade_day_utc);

CREATE TABLE IF NOT EXISTS collector.second_bar (
    ts_second_utc TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    source TEXT NOT NULL,
    open NUMERIC(24, 12),
    high NUMERIC(24, 12),
    low NUMERIC(24, 12),
    close NUMERIC(24, 12),
    trade_count BIGINT NOT NULL DEFAULT 0,
    base_volume NUMERIC(36, 12) NOT NULL DEFAULT 0,
    quote_volume NUMERIC(36, 12) NOT NULL DEFAULT 0,
    buy_volume NUMERIC(36, 12) NOT NULL DEFAULT 0,
    sell_volume NUMERIC(36, 12) NOT NULL DEFAULT 0,
    delta_volume NUMERIC(36, 12) NOT NULL DEFAULT 0,
    vwap NUMERIC(24, 12),
    status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('ready', 'partial')),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, ts_second_utc)
);

CREATE INDEX IF NOT EXISTS idx_second_bar_ts_second_utc
    ON collector.second_bar (ts_second_utc);

CREATE INDEX IF NOT EXISTS idx_second_bar_symbol_ts_second_utc
    ON collector.second_bar (symbol, ts_second_utc);

CREATE TABLE IF NOT EXISTS collector.ingest_watermark (
    pipeline TEXT NOT NULL,
    symbol TEXT NOT NULL,
    watermark_type TEXT NOT NULL,
    watermark_value TEXT NOT NULL,
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (pipeline, symbol, watermark_type)
);

CREATE OR REPLACE VIEW collector.second_bar_with_timeframes AS
WITH second_with_bucket AS (
    SELECT
        sb.*,
        date_trunc('minute', sb.ts_second_utc) AS bucket_1m,
        to_timestamp(floor(extract(epoch FROM sb.ts_second_utc) / 300) * 300) AT TIME ZONE 'UTC' AS bucket_5m_utc,
        date_trunc('hour', sb.ts_second_utc) AS bucket_60m
    FROM collector.second_bar sb
),
windowed AS (
    SELECT
        swb.*,
        first_value(open) OVER (
            PARTITION BY symbol, bucket_1m
            ORDER BY ts_second_utc
        ) AS open_1m,
        max(high) OVER (PARTITION BY symbol, bucket_1m) AS high_1m,
        min(low) OVER (PARTITION BY symbol, bucket_1m) AS low_1m,
        last_value(close) OVER (
            PARTITION BY symbol, bucket_1m
            ORDER BY ts_second_utc
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS close_1m,

        first_value(open) OVER (
            PARTITION BY symbol, bucket_5m_utc
            ORDER BY ts_second_utc
        ) AS open_5m,
        max(high) OVER (PARTITION BY symbol, bucket_5m_utc) AS high_5m,
        min(low) OVER (PARTITION BY symbol, bucket_5m_utc) AS low_5m,
        last_value(close) OVER (
            PARTITION BY symbol, bucket_5m_utc
            ORDER BY ts_second_utc
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS close_5m,

        first_value(open) OVER (
            PARTITION BY symbol, bucket_60m
            ORDER BY ts_second_utc
        ) AS open_60m,
        max(high) OVER (PARTITION BY symbol, bucket_60m) AS high_60m,
        min(low) OVER (PARTITION BY symbol, bucket_60m) AS low_60m,
        last_value(close) OVER (
            PARTITION BY symbol, bucket_60m
            ORDER BY ts_second_utc
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS close_60m
    FROM second_with_bucket swb
)
SELECT
    ts_second_utc,
    symbol,
    source,
    open,
    high,
    low,
    close,
    trade_count,
    base_volume,
    quote_volume,
    buy_volume,
    sell_volume,
    delta_volume,
    vwap,
    status,
    updated_at_utc,
    bucket_1m,
    open_1m,
    high_1m,
    low_1m,
    close_1m,
    bucket_5m_utc,
    open_5m,
    high_5m,
    low_5m,
    close_5m,
    bucket_60m,
    open_60m,
    high_60m,
    low_60m,
    close_60m
FROM windowed;
