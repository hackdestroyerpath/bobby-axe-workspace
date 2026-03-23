-- Step 13: canonical Ben_Kim analysis_result storage

CREATE TABLE IF NOT EXISTS collector.analysis_results (
    analysis_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    correlation_id TEXT,
    producer TEXT,
    event_type TEXT NOT NULL CHECK (event_type = 'analysis_result'),
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    frame TEXT NOT NULL CHECK (frame IN ('1m', '5m', '60m')),
    signal TEXT NOT NULL CHECK (signal IN ('bullish', 'bearish', 'neutral', 'ignore')),
    conclusion TEXT NOT NULL,
    confidence NUMERIC(10, 6) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    observed_at TIMESTAMPTZ NOT NULL,
    source_window_from TIMESTAMPTZ NOT NULL,
    source_window_to TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ready', 'partial', 'rejected')),
    result_code TEXT NOT NULL CHECK (result_code IN ('ok', 'skipped', 'insufficient_data', 'error')),
    details_json JSONB,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_analysis_results_snapshot_symbol_strategy_frame
    ON collector.analysis_results (snapshot_id, symbol, strategy, frame);

CREATE INDEX IF NOT EXISTS idx_analysis_results_snapshot_id
    ON collector.analysis_results (snapshot_id);

CREATE INDEX IF NOT EXISTS idx_analysis_results_symbol_observed_at
    ON collector.analysis_results (symbol, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_results_correlation_id
    ON collector.analysis_results (correlation_id);
