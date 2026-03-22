from __future__ import annotations

import argparse
from pathlib import Path

from collector.config import get_settings
from collector.db import Database

UPSERT_ELLIOTT_VOL_SQL = """
WITH base AS (
    SELECT
        symbol,
        frame,
        observed_at,
        high,
        low,
        close,
        return_1,
        atr_14,
        atr_pct,
        candle_range,
        rolling_high_20,
        rolling_low_20,
        LAG(close) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AS prev_close,
        LAG(close, 5) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AS close_lag_5,
        LAG(close, 20) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AS close_lag_20,
        LAG(low, 5) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AS low_5,
        LAG(high, 5) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AS high_5,
        ROW_NUMBER() OVER (PARTITION BY symbol, frame ORDER BY observed_at) AS rn
    FROM collector.feature_base_tf
    WHERE symbol = %(symbol)s
      AND observed_at >= %(start_at)s
      AND observed_at < %(end_at)s
), tr_stage AS (
    SELECT
        *,
        GREATEST(high - low, abs(high - prev_close), abs(low - prev_close)) AS tr
    FROM base
), vol_stage AS (
    SELECT
        *,
        AVG(tr) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 27 PRECEDING AND CURRENT ROW) AS atr_28,
        STDDEV_POP(return_1) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS return_std_20,
        STDDEV_POP(return_1) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS return_std_50,
        SUM(POWER(COALESCE(return_1, 0), 2)) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS rv20_sum,
        SUM(POWER(COALESCE(return_1, 0), 2)) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS rv50_sum,
        AVG(atr_pct) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 99 PRECEDING AND CURRENT ROW) AS atr_pct_avg_100,
        STDDEV_POP(atr_pct) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 99 PRECEDING AND CURRENT ROW) AS atr_pct_std_100,
        PERCENT_RANK() OVER (PARTITION BY symbol, frame ORDER BY atr_pct) AS atr_pct_percentile_100,
        STDDEV_POP(atr_pct) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS vol_of_vol_20,
        AVG(candle_range) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS avg_range_5,
        AVG(candle_range) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg_range_20,
        SUM(abs(COALESCE(return_1, 0))) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS abs_return_sum_20
    FROM tr_stage
), elliott AS (
    SELECT
        *,
        CASE
            WHEN close > rolling_high_20 THEN 'bullish'
            WHEN close < rolling_low_20 THEN 'bearish'
            ELSE 'neutral'
        END AS elliott_direction,
        CASE
            WHEN close > rolling_high_20 OR close < rolling_low_20 THEN 'impulse'
            ELSE 'correction'
        END AS elliott_pattern_family,
        CASE
            WHEN close > rolling_high_20 THEN 'wave_3'
            WHEN close < rolling_low_20 THEN 'wave_c'
            ELSE 'unknown'
        END AS elliott_candidate_wave,
        CASE
            WHEN close > rolling_high_20 THEN 3
            WHEN close < rolling_low_20 THEN 3
            ELSE 0
        END AS elliott_position_in_sequence,
        20 AS elliott_structure_age_bars,
        5 AS elliott_swings_used,
        CASE
            WHEN atr_14 > 0 AND close_lag_5 IS NOT NULL THEN LEAST(1.0, GREATEST(0.0, abs(close - close_lag_5) / (5 * atr_14)))
            ELSE 0.0
        END AS elliott_monotonicity_score,
        CASE WHEN atr_14 > 0 THEN LEAST(1.0, GREATEST(0.0, abs(rolling_high_20 - rolling_low_20) / NULLIF(10 * atr_14, 0))) ELSE 0.0 END AS elliott_pivot_clarity_score,
        0.5::numeric AS elliott_leg_symmetry_score,
        CASE WHEN abs((close / NULLIF(close_lag_20, 0)) - 1) > 0 THEN abs_return_sum_20 / abs((close / NULLIF(close_lag_20, 0)) - 1) ELSE NULL END AS elliott_noise_ratio,
        0.42::numeric AS elliott_confidence,
        'low'::text AS elliott_confidence_band,
        CASE WHEN low_5 IS NOT NULL AND high_5 IS NOT NULL THEN abs(close - low_5) / NULLIF(abs(high_5 - low_5), 0) ELSE NULL END AS wave2_retrace_pct_of_wave1,
        CASE WHEN low_5 IS NOT NULL AND high_5 IS NOT NULL THEN abs(close - high_5) / NULLIF(abs(high_5 - low_5), 0) ELSE NULL END AS wave3_ext_pct_of_wave1,
        0.38::numeric AS wave4_retrace_pct_of_wave3,
        0.62::numeric AS wave5_ext_pct_of_wave1,
        CASE WHEN close > rolling_high_20 THEN rolling_low_20 WHEN close < rolling_low_20 THEN rolling_high_20 ELSE NULL END AS elliott_invalidation_price
    FROM vol_stage
), calc AS (
    SELECT
        symbol,
        frame,
        observed_at,
        CASE WHEN rn >= 30 THEN 'ready' ELSE 'partial' END AS feature_status,
        CASE WHEN rn >= 30 THEN 'ok' ELSE 'insufficient_data' END AS result_code,
        elliott_direction,
        elliott_pattern_family,
        elliott_candidate_wave,
        elliott_position_in_sequence,
        elliott_structure_age_bars,
        elliott_swings_used,
        elliott_confidence,
        elliott_confidence_band,
        elliott_noise_ratio,
        elliott_monotonicity_score,
        elliott_pivot_clarity_score,
        elliott_leg_symmetry_score,
        wave2_retrace_pct_of_wave1,
        wave3_ext_pct_of_wave1,
        wave4_retrace_pct_of_wave3,
        wave5_ext_pct_of_wave1,
        elliott_invalidation_price,
        CASE WHEN atr_14 > 0 AND elliott_invalidation_price IS NOT NULL THEN abs(close - elliott_invalidation_price) / atr_14 ELSE NULL END AS elliott_distance_to_invalidation_atr,
        CASE WHEN close <> 0 AND elliott_invalidation_price IS NOT NULL THEN abs(close - elliott_invalidation_price) / close ELSE NULL END AS elliott_distance_to_invalidation_pct,
        tr,
        atr_14,
        atr_28,
        atr_pct AS atr_pct_14,
        CASE WHEN close <> 0 AND atr_28 IS NOT NULL THEN atr_28 / close ELSE NULL END AS atr_pct_28,
        candle_range AS range_hl,
        CASE WHEN close <> 0 THEN candle_range / close ELSE NULL END AS range_hl_pct,
        sqrt(rv20_sum) AS realized_vol_20,
        sqrt(rv50_sum) AS realized_vol_50,
        return_std_20,
        return_std_50,
        CASE WHEN atr_pct_std_100 > 0 THEN (atr_pct - atr_pct_avg_100) / atr_pct_std_100 ELSE NULL END AS atr_pct_zscore_100,
        atr_pct_percentile_100,
        CASE
            WHEN atr_pct_percentile_100 < 0.20 THEN 'compressed'
            WHEN atr_pct_percentile_100 <= 0.80 THEN 'normal'
            WHEN atr_pct_percentile_100 <= 0.95 THEN 'expanded'
            ELSE 'extreme'
        END AS vol_regime,
        vol_of_vol_20,
        CASE WHEN avg_range_5 > 0 THEN candle_range / avg_range_5 ELSE NULL END AS range_expansion_5,
        CASE WHEN avg_range_20 > 0 THEN candle_range / avg_range_20 ELSE NULL END AS range_expansion_20,
        CASE WHEN atr_14 > 0 AND close_lag_5 IS NOT NULL THEN abs(close - close_lag_5) / atr_14 ELSE NULL END AS swing_size_to_atr_last,
        CASE WHEN atr_14 > 0 THEN abs(rolling_high_20 - rolling_low_20) / atr_14 ELSE NULL END AS structure_total_move_atr,
        CASE WHEN atr_14 > 0 THEN abs(close - rolling_low_20) / atr_14 ELSE NULL END AS pullback_depth_atr,
        CASE WHEN atr_14 > 0 THEN candle_range / atr_14 ELSE NULL END AS breakout_bar_range_atr,
        CASE WHEN abs_return_sum_20 > 0 AND close_lag_20 IS NOT NULL THEN abs(close - close_lag_20) / abs_return_sum_20 ELSE NULL END AS impulse_efficiency_ratio
    FROM elliott
)
INSERT INTO collector.feature_elliott_vol_tf (
    symbol, frame, observed_at, feature_status, result_code,
    elliott_direction, elliott_pattern_family, elliott_candidate_wave,
    elliott_position_in_sequence, elliott_structure_age_bars, elliott_swings_used,
    elliott_confidence, elliott_confidence_band,
    elliott_noise_ratio, elliott_monotonicity_score, elliott_pivot_clarity_score, elliott_leg_symmetry_score,
    wave2_retrace_pct_of_wave1, wave3_ext_pct_of_wave1, wave4_retrace_pct_of_wave3, wave5_ext_pct_of_wave1,
    elliott_invalidation_price, elliott_distance_to_invalidation_atr, elliott_distance_to_invalidation_pct,
    tr, atr_14, atr_28, atr_pct_14, atr_pct_28, range_hl, range_hl_pct,
    realized_vol_20, realized_vol_50, return_std_20, return_std_50,
    atr_pct_zscore_100, atr_pct_percentile_100, vol_regime, vol_of_vol_20,
    range_expansion_5, range_expansion_20,
    swing_size_to_atr_last, structure_total_move_atr, pullback_depth_atr, breakout_bar_range_atr, impulse_efficiency_ratio,
    computed_at_utc
)
SELECT
    symbol, frame, observed_at, feature_status, result_code,
    elliott_direction, elliott_pattern_family, elliott_candidate_wave,
    elliott_position_in_sequence, elliott_structure_age_bars, elliott_swings_used,
    elliott_confidence, elliott_confidence_band,
    elliott_noise_ratio, elliott_monotonicity_score, elliott_pivot_clarity_score, elliott_leg_symmetry_score,
    wave2_retrace_pct_of_wave1, wave3_ext_pct_of_wave1, wave4_retrace_pct_of_wave3, wave5_ext_pct_of_wave1,
    elliott_invalidation_price, elliott_distance_to_invalidation_atr, elliott_distance_to_invalidation_pct,
    tr, atr_14, atr_28, atr_pct_14, atr_pct_28, range_hl, range_hl_pct,
    realized_vol_20, realized_vol_50, return_std_20, return_std_50,
    atr_pct_zscore_100, atr_pct_percentile_100, vol_regime, vol_of_vol_20,
    range_expansion_5, range_expansion_20,
    swing_size_to_atr_last, structure_total_move_atr, pullback_depth_atr, breakout_bar_range_atr, impulse_efficiency_ratio,
    NOW()
FROM calc
ON CONFLICT (symbol, frame, observed_at)
DO UPDATE SET
    feature_status = EXCLUDED.feature_status,
    result_code = EXCLUDED.result_code,
    elliott_direction = EXCLUDED.elliott_direction,
    elliott_pattern_family = EXCLUDED.elliott_pattern_family,
    elliott_candidate_wave = EXCLUDED.elliott_candidate_wave,
    elliott_position_in_sequence = EXCLUDED.elliott_position_in_sequence,
    elliott_structure_age_bars = EXCLUDED.elliott_structure_age_bars,
    elliott_swings_used = EXCLUDED.elliott_swings_used,
    elliott_confidence = EXCLUDED.elliott_confidence,
    elliott_confidence_band = EXCLUDED.elliott_confidence_band,
    elliott_noise_ratio = EXCLUDED.elliott_noise_ratio,
    elliott_monotonicity_score = EXCLUDED.elliott_monotonicity_score,
    elliott_pivot_clarity_score = EXCLUDED.elliott_pivot_clarity_score,
    elliott_leg_symmetry_score = EXCLUDED.elliott_leg_symmetry_score,
    wave2_retrace_pct_of_wave1 = EXCLUDED.wave2_retrace_pct_of_wave1,
    wave3_ext_pct_of_wave1 = EXCLUDED.wave3_ext_pct_of_wave1,
    wave4_retrace_pct_of_wave3 = EXCLUDED.wave4_retrace_pct_of_wave3,
    wave5_ext_pct_of_wave1 = EXCLUDED.wave5_ext_pct_of_wave1,
    elliott_invalidation_price = EXCLUDED.elliott_invalidation_price,
    elliott_distance_to_invalidation_atr = EXCLUDED.elliott_distance_to_invalidation_atr,
    elliott_distance_to_invalidation_pct = EXCLUDED.elliott_distance_to_invalidation_pct,
    tr = EXCLUDED.tr,
    atr_14 = EXCLUDED.atr_14,
    atr_28 = EXCLUDED.atr_28,
    atr_pct_14 = EXCLUDED.atr_pct_14,
    atr_pct_28 = EXCLUDED.atr_pct_28,
    range_hl = EXCLUDED.range_hl,
    range_hl_pct = EXCLUDED.range_hl_pct,
    realized_vol_20 = EXCLUDED.realized_vol_20,
    realized_vol_50 = EXCLUDED.realized_vol_50,
    return_std_20 = EXCLUDED.return_std_20,
    return_std_50 = EXCLUDED.return_std_50,
    atr_pct_zscore_100 = EXCLUDED.atr_pct_zscore_100,
    atr_pct_percentile_100 = EXCLUDED.atr_pct_percentile_100,
    vol_regime = EXCLUDED.vol_regime,
    vol_of_vol_20 = EXCLUDED.vol_of_vol_20,
    range_expansion_5 = EXCLUDED.range_expansion_5,
    range_expansion_20 = EXCLUDED.range_expansion_20,
    swing_size_to_atr_last = EXCLUDED.swing_size_to_atr_last,
    structure_total_move_atr = EXCLUDED.structure_total_move_atr,
    pullback_depth_atr = EXCLUDED.pullback_depth_atr,
    breakout_bar_range_atr = EXCLUDED.breakout_bar_range_atr,
    impulse_efficiency_ratio = EXCLUDED.impulse_efficiency_ratio,
    computed_at_utc = NOW()
"""


class FeatureElliottVolBuilder:
    def __init__(self, db: Database):
        self.db = db

    def build_window(self, symbol: str, start_at, end_at) -> int:
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(UPSERT_ELLIOTT_VOL_SQL, {'symbol': symbol, 'start_at': start_at, 'end_at': end_at})
                affected = cur.rowcount if cur.rowcount != -1 else 0
            conn.commit()
        return affected


def main() -> None:
    parser = argparse.ArgumentParser(description='Build elliott+volatility features from feature_base_tf')
    parser.add_argument('--symbol', default='BTCUSDC')
    parser.add_argument('--start-at', required=True)
    parser.add_argument('--end-at', required=True)
    parser.add_argument('--apply-schema', action='store_true')
    args = parser.parse_args()

    settings = get_settings()
    db = Database(settings.database_url)
    if args.apply_schema:
        db.apply_sql_file(str(Path(__file__).resolve().parent / 'sql' / '007_feature_elliott_vol.sql'))

    builder = FeatureElliottVolBuilder(db)
    affected = builder.build_window(symbol=args.symbol.upper(), start_at=args.start_at, end_at=args.end_at)
    print(f'Affected feature_elliott_vol_tf rows: {affected}')


if __name__ == '__main__':
    main()
