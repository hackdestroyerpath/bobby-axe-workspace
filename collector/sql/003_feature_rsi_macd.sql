-- Step 4: RSI + MACD feature storage

CREATE TABLE IF NOT EXISTS collector.feature_rsi_macd_tf (
    symbol TEXT NOT NULL,
    frame TEXT NOT NULL CHECK (frame IN ('1m', '5m', '60m')),
    observed_at TIMESTAMPTZ NOT NULL,
    feature_version TEXT NOT NULL DEFAULT 'v1',
    computed_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    feature_is_valid BOOLEAN NOT NULL DEFAULT FALSE,

    rsi_14 NUMERIC(24, 12),
    rsi_14_prev1 NUMERIC(24, 12),
    rsi_14_delta_1 NUMERIC(24, 12),
    rsi_14_slope_3 NUMERIC(24, 12),
    rsi_14_slope_5 NUMERIC(24, 12),

    rsi_above_50_flag BOOLEAN,
    rsi_below_50_flag BOOLEAN,
    rsi_overbought_70_flag BOOLEAN,
    rsi_oversold_30_flag BOOLEAN,
    rsi_cross_up_30_flag BOOLEAN,
    rsi_cross_down_70_flag BOOLEAN,
    rsi_cross_up_50_flag BOOLEAN,
    rsi_cross_down_50_flag BOOLEAN,

    macd_12_26_9_line NUMERIC(24, 12),
    macd_12_26_9_signal NUMERIC(24, 12),
    macd_12_26_9_hist NUMERIC(24, 12),
    macd_hist_delta_1 NUMERIC(24, 12),
    macd_hist_slope_3 NUMERIC(24, 12),
    macd_hist_slope_5 NUMERIC(24, 12),

    macd_bull_cross_flag BOOLEAN,
    macd_bear_cross_flag BOOLEAN,
    macd_hist_cross_up_0_flag BOOLEAN,
    macd_hist_cross_down_0_flag BOOLEAN,

    rsi_macd_bullish_cluster_flag BOOLEAN,
    rsi_macd_bearish_cluster_flag BOOLEAN,
    rsi_macd_bullish_reversal_flag BOOLEAN,
    rsi_macd_bearish_reversal_flag BOOLEAN,
    rsi_macd_momentum_accel_up_flag BOOLEAN,
    rsi_macd_momentum_accel_down_flag BOOLEAN,

    PRIMARY KEY (symbol, frame, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_feature_rsi_macd_tf_symbol_frame_observed_at
    ON collector.feature_rsi_macd_tf (symbol, frame, observed_at);
