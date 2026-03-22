-- Step 8: elliott candidate + volatility feature storage

CREATE TABLE IF NOT EXISTS collector.feature_elliott_vol_tf (
    symbol TEXT NOT NULL,
    frame TEXT NOT NULL CHECK (frame IN ('1m', '5m', '60m')),
    observed_at TIMESTAMPTZ NOT NULL,
    feature_version TEXT NOT NULL DEFAULT 'v1',
    computed_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    feature_status TEXT NOT NULL DEFAULT 'partial',
    result_code TEXT NOT NULL DEFAULT 'insufficient_data',

    elliott_direction TEXT,
    elliott_pattern_family TEXT,
    elliott_candidate_wave TEXT,
    elliott_position_in_sequence INTEGER,
    elliott_structure_age_bars INTEGER,
    elliott_swings_used INTEGER,
    elliott_confidence NUMERIC(24, 12),
    elliott_confidence_band TEXT,
    elliott_noise_ratio NUMERIC(24, 12),
    elliott_monotonicity_score NUMERIC(24, 12),
    elliott_pivot_clarity_score NUMERIC(24, 12),
    elliott_leg_symmetry_score NUMERIC(24, 12),

    wave2_retrace_pct_of_wave1 NUMERIC(24, 12),
    wave3_ext_pct_of_wave1 NUMERIC(24, 12),
    wave4_retrace_pct_of_wave3 NUMERIC(24, 12),
    wave5_ext_pct_of_wave1 NUMERIC(24, 12),

    elliott_invalidation_price NUMERIC(24, 12),
    elliott_distance_to_invalidation_atr NUMERIC(24, 12),
    elliott_distance_to_invalidation_pct NUMERIC(24, 12),

    tr NUMERIC(24, 12),
    atr_14 NUMERIC(24, 12),
    atr_28 NUMERIC(24, 12),
    atr_pct_14 NUMERIC(24, 12),
    atr_pct_28 NUMERIC(24, 12),
    range_hl NUMERIC(24, 12),
    range_hl_pct NUMERIC(24, 12),
    realized_vol_20 NUMERIC(24, 12),
    realized_vol_50 NUMERIC(24, 12),
    return_std_20 NUMERIC(24, 12),
    return_std_50 NUMERIC(24, 12),
    atr_pct_zscore_100 NUMERIC(24, 12),
    atr_pct_percentile_100 NUMERIC(24, 12),
    vol_regime TEXT,
    vol_of_vol_20 NUMERIC(24, 12),
    range_expansion_5 NUMERIC(24, 12),
    range_expansion_20 NUMERIC(24, 12),
    swing_size_to_atr_last NUMERIC(24, 12),
    structure_total_move_atr NUMERIC(24, 12),
    pullback_depth_atr NUMERIC(24, 12),
    breakout_bar_range_atr NUMERIC(24, 12),
    impulse_efficiency_ratio NUMERIC(24, 12),

    PRIMARY KEY (symbol, frame, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_feature_elliott_vol_tf_symbol_frame_observed_at
    ON collector.feature_elliott_vol_tf (symbol, frame, observed_at);
