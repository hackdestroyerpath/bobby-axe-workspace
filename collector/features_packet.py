from __future__ import annotations

import argparse
from pathlib import Path

from collector.config import get_settings
from collector.db import Database

UPSERT_PACKET_SQL = """
INSERT INTO collector.feature_packet_tf (
    symbol, frame, observed_at,
    packet_status, packet_result_code,
    open, high, low, close, volume_total, buy_volume, sell_volume, delta_volume, trade_count,
    lvl_nearest_support_px, lvl_nearest_resistance_px,
    lvl_distance_to_support_pct, lvl_distance_to_resistance_pct,
    lvl_support_touch_count, lvl_resistance_touch_count,
    lvl_is_breakout, lvl_is_false_breakout,
    fib_leg_dir, fib_nearest_ratio, fib_nearest_level_px,
    fib_swing_low, fib_swing_high, fib_236, fib_382, fib_500, fib_618, fib_786, fib_distance_to_nearest_pct,
    hv_poc_px, hv_val_px, hv_vah_px,
    hv_inside_value_area, hv_nearest_hvn_px, hv_nearest_lvn_px, hv_distance_to_poc_pct,
    cluster_primary_context,
    vv_vol_z, vv_delta_z, vv_buy_share, vv_pressure_to_move_z, vv_divergence_3, vv_exhaustion_flag,
    rsi_14, macd_12_26_9_line, macd_12_26_9_signal, macd_12_26_9_hist,
    rsi_state, macd_cross_up, macd_cross_down, macd_hist_slope,
    rsi_macd_bullish_cluster_flag, rsi_macd_bearish_cluster_flag, rsi_macd_bullish_reversal_flag, rsi_macd_bearish_reversal_flag,
    trade_speed_now, trade_speed_ma, trade_speed_ratio, volume_per_sec, avg_trade_size,
    aggressive_buy_rate, aggressive_sell_rate, buy_sell_imbalance,
    burst_detected, flow_accelerating, flow_decelerating, flow_absorption_flag, flow_exhaustion_flag,
    elliott_direction, elliott_pattern_family, elliott_candidate_wave,
    elliott_wave_count, elliott_swing_sequence, elliott_status,
    elliott_confidence, elliott_invalidation_price,
    atr_14, atr_pct, vol_regime, impulse_efficiency_ratio,
    realized_volatility, range_expansion_detected,
    data_quality_status, data_quality_result_code, stale, insufficient_history_flag, notes,
    computed_at_utc
)
WITH joined AS (
    SELECT
        b.symbol,
        b.frame,
        b.observed_at,
        b.feature_status AS base_feature_status,
        b.result_code AS base_result_code,
        b.open, b.high, b.low, b.close, b.volume_total, b.buy_volume, b.sell_volume, b.delta_volume, b.trade_count,
        l.feature_is_valid AS levels_feature_is_valid,
        l.lvl_nearest_support_px,
        l.lvl_nearest_resistance_px,
        CASE WHEN b.close <> 0 AND l.lvl_nearest_support_px IS NOT NULL THEN (b.close - l.lvl_nearest_support_px) / b.close ELSE NULL END AS lvl_distance_to_support_pct,
        CASE WHEN b.close <> 0 AND l.lvl_nearest_resistance_px IS NOT NULL THEN (l.lvl_nearest_resistance_px - b.close) / b.close ELSE NULL END AS lvl_distance_to_resistance_pct,
        l.lvl_support_retests AS lvl_support_touch_count,
        l.lvl_resistance_retests AS lvl_resistance_touch_count,
        (l.lvl_break_state IN ('below_support', 'above_resistance')) AS lvl_is_breakout,
        FALSE AS lvl_is_false_breakout,
        l.fib_leg_dir,
        l.fib_nearest_ratio,
        l.fib_nearest_level_px,
        CASE WHEN l.fib_leg_dir = 'up' THEN b.rolling_low_20 ELSE b.rolling_high_20 END AS fib_swing_low,
        CASE WHEN l.fib_leg_dir = 'up' THEN b.rolling_high_20 ELSE b.rolling_low_20 END AS fib_swing_high,
        CASE WHEN l.fib_leg_dir = 'up' THEN b.rolling_high_20 - ((b.rolling_high_20 - b.rolling_low_20) * 0.236)
             ELSE b.rolling_low_20 + ((b.rolling_high_20 - b.rolling_low_20) * 0.236) END AS fib_236,
        CASE WHEN l.fib_leg_dir = 'up' THEN b.rolling_high_20 - ((b.rolling_high_20 - b.rolling_low_20) * 0.382)
             ELSE b.rolling_low_20 + ((b.rolling_high_20 - b.rolling_low_20) * 0.382) END AS fib_382,
        CASE WHEN l.fib_leg_dir = 'up' THEN b.rolling_high_20 - ((b.rolling_high_20 - b.rolling_low_20) * 0.500)
             ELSE b.rolling_low_20 + ((b.rolling_high_20 - b.rolling_low_20) * 0.500) END AS fib_500,
        CASE WHEN l.fib_leg_dir = 'up' THEN b.rolling_high_20 - ((b.rolling_high_20 - b.rolling_low_20) * 0.618)
             ELSE b.rolling_low_20 + ((b.rolling_high_20 - b.rolling_low_20) * 0.618) END AS fib_618,
        CASE WHEN l.fib_leg_dir = 'up' THEN b.rolling_high_20 - ((b.rolling_high_20 - b.rolling_low_20) * 0.786)
             ELSE b.rolling_low_20 + ((b.rolling_high_20 - b.rolling_low_20) * 0.786) END AS fib_786,
        CASE WHEN b.close <> 0 AND l.fib_nearest_level_px IS NOT NULL THEN abs(b.close - l.fib_nearest_level_px) / b.close ELSE NULL END AS fib_distance_to_nearest_pct,
        l.hv_poc_px, l.hv_val_px, l.hv_vah_px,
        (b.close BETWEEN l.hv_val_px AND l.hv_vah_px) AS hv_inside_value_area,
        l.hv_poc_px AS hv_nearest_hvn_px,
        CASE WHEN b.close < l.hv_poc_px THEN l.hv_val_px ELSE l.hv_vah_px END AS hv_nearest_lvn_px,
        CASE WHEN b.close <> 0 AND l.hv_poc_px IS NOT NULL THEN abs(b.close - l.hv_poc_px) / b.close ELSE NULL END AS hv_distance_to_poc_pct,
        l.cluster_primary_context,
        COALESCE(v.feature_is_valid, FALSE) AS vv_feature_is_valid,
        v.vv_vol_z, v.vv_delta_z, v.vv_buy_share, v.vv_pressure_to_move_z, v.vv_divergence_3, v.vv_exhaustion_flag,
        COALESCE(r.feature_is_valid, FALSE) AS rsi_feature_is_valid,
        r.rsi_14, r.macd_12_26_9_line, r.macd_12_26_9_signal, r.macd_12_26_9_hist,
        CASE
            WHEN r.rsi_overbought_70_flag THEN 'overbought'
            WHEN r.rsi_oversold_30_flag THEN 'oversold'
            WHEN r.rsi_above_50_flag THEN 'bullish_above_50'
            WHEN r.rsi_below_50_flag THEN 'bearish_below_50'
            ELSE 'neutral'
        END AS rsi_state,
        r.macd_bull_cross_flag AS macd_cross_up,
        r.macd_bear_cross_flag AS macd_cross_down,
        r.macd_hist_slope_3 AS macd_hist_slope,
        r.rsi_macd_bullish_cluster_flag, r.rsi_macd_bearish_cluster_flag, r.rsi_macd_bullish_reversal_flag, r.rsi_macd_bearish_reversal_flag,
        COALESCE(t.feature_is_valid, FALSE) AS trade_speed_feature_is_valid,
        t.trade_speed_now, t.trade_speed_ma, t.trade_speed_ratio,
        CASE
            WHEN b.frame = '1m' THEN b.volume_total / 60.0
            WHEN b.frame = '5m' THEN b.volume_total / 300.0
            ELSE b.volume_total / 3600.0
        END AS volume_per_sec,
        t.avg_trade_size,
        t.aggressive_buy_rate, t.aggressive_sell_rate, t.buy_sell_imbalance,
        t.burst_detected, t.flow_accelerating, t.flow_decelerating, t.flow_absorption_flag, t.flow_exhaustion_flag,
        e.feature_status AS elliott_feature_status,
        e.elliott_direction, e.elliott_pattern_family, e.elliott_candidate_wave,
        e.elliott_position_in_sequence AS elliott_wave_count,
        CONCAT_WS('>', COALESCE(e.elliott_pattern_family, 'unknown'), COALESCE(e.elliott_candidate_wave, 'unknown'), COALESCE(e.elliott_position_in_sequence::text, 'na')) AS elliott_swing_sequence,
        e.feature_status AS elliott_status,
        e.elliott_confidence, e.elliott_invalidation_price,
        e.atr_14, e.atr_pct_14 AS atr_pct, e.vol_regime, e.impulse_efficiency_ratio,
        e.realized_vol_20 AS realized_volatility,
        COALESCE(e.range_expansion_5 >= 1.5, FALSE) OR COALESCE(e.range_expansion_20 >= 1.5, FALSE) AS range_expansion_detected,
        b.feature_status AS data_quality_status,
        b.result_code AS data_quality_result_code,
        b.stale, b.insufficient_history_flag, b.notes
    FROM collector.feature_base_tf b
    LEFT JOIN collector.feature_levels_fib_hvol_tf l USING (symbol, frame, observed_at)
    LEFT JOIN collector.feature_vertical_volume_tf v USING (symbol, frame, observed_at)
    LEFT JOIN collector.feature_rsi_macd_tf r USING (symbol, frame, observed_at)
    LEFT JOIN collector.feature_trade_speed_tf t USING (symbol, frame, observed_at)
    LEFT JOIN collector.feature_elliott_vol_tf e USING (symbol, frame, observed_at)
    WHERE b.symbol = %(symbol)s
      AND b.observed_at >= %(start_at)s
      AND b.observed_at < %(end_at)s
)
SELECT
    symbol,
    frame,
    observed_at,
    CASE
        WHEN base_feature_status = 'ready'
         AND COALESCE(levels_feature_is_valid, FALSE)
         AND COALESCE(rsi_feature_is_valid, FALSE)
         AND COALESCE(trade_speed_feature_is_valid, FALSE)
         AND COALESCE(elliott_feature_status = 'ready', FALSE)
        THEN 'ready'
        ELSE 'partial'
    END AS packet_status,
    CASE
        WHEN base_feature_status = 'ready'
         AND COALESCE(levels_feature_is_valid, FALSE)
         AND COALESCE(rsi_feature_is_valid, FALSE)
         AND COALESCE(trade_speed_feature_is_valid, FALSE)
         AND COALESCE(elliott_feature_status = 'ready', FALSE)
        THEN 'ok'
        ELSE 'partial'
    END AS packet_result_code,
    open, high, low, close, volume_total, buy_volume, sell_volume, delta_volume, trade_count,
    lvl_nearest_support_px, lvl_nearest_resistance_px,
    lvl_distance_to_support_pct, lvl_distance_to_resistance_pct,
    lvl_support_touch_count, lvl_resistance_touch_count,
    lvl_is_breakout, lvl_is_false_breakout,
    fib_leg_dir, fib_nearest_ratio, fib_nearest_level_px,
    fib_swing_low, fib_swing_high, fib_236, fib_382, fib_500, fib_618, fib_786, fib_distance_to_nearest_pct,
    hv_poc_px, hv_val_px, hv_vah_px,
    hv_inside_value_area, hv_nearest_hvn_px, hv_nearest_lvn_px, hv_distance_to_poc_pct,
    cluster_primary_context,
    vv_vol_z, vv_delta_z, vv_buy_share, vv_pressure_to_move_z, vv_divergence_3, vv_exhaustion_flag,
    rsi_14, macd_12_26_9_line, macd_12_26_9_signal, macd_12_26_9_hist,
    rsi_state, macd_cross_up, macd_cross_down, macd_hist_slope,
    rsi_macd_bullish_cluster_flag, rsi_macd_bearish_cluster_flag, rsi_macd_bullish_reversal_flag, rsi_macd_bearish_reversal_flag,
    trade_speed_now, trade_speed_ma, trade_speed_ratio, volume_per_sec, avg_trade_size,
    aggressive_buy_rate, aggressive_sell_rate, buy_sell_imbalance,
    burst_detected, flow_accelerating, flow_decelerating, flow_absorption_flag, flow_exhaustion_flag,
    elliott_direction, elliott_pattern_family, elliott_candidate_wave,
    elliott_wave_count, elliott_swing_sequence, elliott_status,
    elliott_confidence, elliott_invalidation_price,
    atr_14, atr_pct, vol_regime, impulse_efficiency_ratio,
    realized_volatility, range_expansion_detected,
    data_quality_status, data_quality_result_code, stale, insufficient_history_flag, notes,
    NOW()
FROM joined
ON CONFLICT (symbol, frame, observed_at)
DO UPDATE SET
    packet_status = EXCLUDED.packet_status,
    packet_result_code = EXCLUDED.packet_result_code,
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume_total = EXCLUDED.volume_total,
    buy_volume = EXCLUDED.buy_volume,
    sell_volume = EXCLUDED.sell_volume,
    delta_volume = EXCLUDED.delta_volume,
    trade_count = EXCLUDED.trade_count,
    lvl_nearest_support_px = EXCLUDED.lvl_nearest_support_px,
    lvl_nearest_resistance_px = EXCLUDED.lvl_nearest_resistance_px,
    lvl_distance_to_support_pct = EXCLUDED.lvl_distance_to_support_pct,
    lvl_distance_to_resistance_pct = EXCLUDED.lvl_distance_to_resistance_pct,
    lvl_support_touch_count = EXCLUDED.lvl_support_touch_count,
    lvl_resistance_touch_count = EXCLUDED.lvl_resistance_touch_count,
    lvl_is_breakout = EXCLUDED.lvl_is_breakout,
    lvl_is_false_breakout = EXCLUDED.lvl_is_false_breakout,
    fib_leg_dir = EXCLUDED.fib_leg_dir,
    fib_nearest_ratio = EXCLUDED.fib_nearest_ratio,
    fib_nearest_level_px = EXCLUDED.fib_nearest_level_px,
    fib_swing_low = EXCLUDED.fib_swing_low,
    fib_swing_high = EXCLUDED.fib_swing_high,
    fib_236 = EXCLUDED.fib_236,
    fib_382 = EXCLUDED.fib_382,
    fib_500 = EXCLUDED.fib_500,
    fib_618 = EXCLUDED.fib_618,
    fib_786 = EXCLUDED.fib_786,
    fib_distance_to_nearest_pct = EXCLUDED.fib_distance_to_nearest_pct,
    hv_poc_px = EXCLUDED.hv_poc_px,
    hv_val_px = EXCLUDED.hv_val_px,
    hv_vah_px = EXCLUDED.hv_vah_px,
    hv_inside_value_area = EXCLUDED.hv_inside_value_area,
    hv_nearest_hvn_px = EXCLUDED.hv_nearest_hvn_px,
    hv_nearest_lvn_px = EXCLUDED.hv_nearest_lvn_px,
    hv_distance_to_poc_pct = EXCLUDED.hv_distance_to_poc_pct,
    cluster_primary_context = EXCLUDED.cluster_primary_context,
    vv_vol_z = EXCLUDED.vv_vol_z,
    vv_delta_z = EXCLUDED.vv_delta_z,
    vv_buy_share = EXCLUDED.vv_buy_share,
    vv_pressure_to_move_z = EXCLUDED.vv_pressure_to_move_z,
    vv_divergence_3 = EXCLUDED.vv_divergence_3,
    vv_exhaustion_flag = EXCLUDED.vv_exhaustion_flag,
    rsi_14 = EXCLUDED.rsi_14,
    macd_12_26_9_line = EXCLUDED.macd_12_26_9_line,
    macd_12_26_9_signal = EXCLUDED.macd_12_26_9_signal,
    macd_12_26_9_hist = EXCLUDED.macd_12_26_9_hist,
    rsi_state = EXCLUDED.rsi_state,
    macd_cross_up = EXCLUDED.macd_cross_up,
    macd_cross_down = EXCLUDED.macd_cross_down,
    macd_hist_slope = EXCLUDED.macd_hist_slope,
    rsi_macd_bullish_cluster_flag = EXCLUDED.rsi_macd_bullish_cluster_flag,
    rsi_macd_bearish_cluster_flag = EXCLUDED.rsi_macd_bearish_cluster_flag,
    rsi_macd_bullish_reversal_flag = EXCLUDED.rsi_macd_bullish_reversal_flag,
    rsi_macd_bearish_reversal_flag = EXCLUDED.rsi_macd_bearish_reversal_flag,
    trade_speed_now = EXCLUDED.trade_speed_now,
    trade_speed_ma = EXCLUDED.trade_speed_ma,
    trade_speed_ratio = EXCLUDED.trade_speed_ratio,
    volume_per_sec = EXCLUDED.volume_per_sec,
    avg_trade_size = EXCLUDED.avg_trade_size,
    aggressive_buy_rate = EXCLUDED.aggressive_buy_rate,
    aggressive_sell_rate = EXCLUDED.aggressive_sell_rate,
    buy_sell_imbalance = EXCLUDED.buy_sell_imbalance,
    burst_detected = EXCLUDED.burst_detected,
    flow_accelerating = EXCLUDED.flow_accelerating,
    flow_decelerating = EXCLUDED.flow_decelerating,
    flow_absorption_flag = EXCLUDED.flow_absorption_flag,
    flow_exhaustion_flag = EXCLUDED.flow_exhaustion_flag,
    elliott_direction = EXCLUDED.elliott_direction,
    elliott_pattern_family = EXCLUDED.elliott_pattern_family,
    elliott_candidate_wave = EXCLUDED.elliott_candidate_wave,
    elliott_wave_count = EXCLUDED.elliott_wave_count,
    elliott_swing_sequence = EXCLUDED.elliott_swing_sequence,
    elliott_status = EXCLUDED.elliott_status,
    elliott_confidence = EXCLUDED.elliott_confidence,
    elliott_invalidation_price = EXCLUDED.elliott_invalidation_price,
    atr_14 = EXCLUDED.atr_14,
    atr_pct = EXCLUDED.atr_pct,
    vol_regime = EXCLUDED.vol_regime,
    impulse_efficiency_ratio = EXCLUDED.impulse_efficiency_ratio,
    realized_volatility = EXCLUDED.realized_volatility,
    range_expansion_detected = EXCLUDED.range_expansion_detected,
    data_quality_status = EXCLUDED.data_quality_status,
    data_quality_result_code = EXCLUDED.data_quality_result_code,
    stale = EXCLUDED.stale,
    insufficient_history_flag = EXCLUDED.insufficient_history_flag,
    notes = EXCLUDED.notes,
    computed_at_utc = NOW()
"""


class FeaturePacketBuilder:
    def __init__(self, db: Database):
        self.db = db

    def build_window(self, symbol: str, start_at, end_at) -> int:
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(UPSERT_PACKET_SQL, {'symbol': symbol, 'start_at': start_at, 'end_at': end_at})
                affected = cur.rowcount if cur.rowcount != -1 else 0
            conn.commit()
        return affected


def main() -> None:
    parser = argparse.ArgumentParser(description='Build unified feature packet from feature layers')
    parser.add_argument('--symbol', default='BTCUSDC')
    parser.add_argument('--start-at', required=True)
    parser.add_argument('--end-at', required=True)
    parser.add_argument('--apply-schema', action='store_true')
    args = parser.parse_args()

    settings = get_settings()
    db = Database(settings.database_url)
    if args.apply_schema:
        db.apply_sql_file(str(Path(__file__).resolve().parent / 'sql' / '008_feature_packet.sql'))
        db.apply_sql_file(str(Path(__file__).resolve().parent / 'sql' / '011_feature_packet_v2.sql'))

    builder = FeaturePacketBuilder(db)
    affected = builder.build_window(symbol=args.symbol.upper(), start_at=args.start_at, end_at=args.end_at)
    print(f'Affected feature_packet_tf rows: {affected}')


if __name__ == '__main__':
    main()
