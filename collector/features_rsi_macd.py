from __future__ import annotations

import argparse
from pathlib import Path

from collector.config import get_settings
from collector.db import Database

UPSERT_RSI_MACD_SQL = """
WITH base AS (
    SELECT
        symbol,
        frame,
        observed_at,
        close,
        LAG(close) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AS prev_close
    FROM collector.feature_base_tf
    WHERE symbol = %(symbol)s
      AND observed_at >= %(start_at)s
      AND observed_at < %(end_at)s
),
deltas AS (
    SELECT
        symbol,
        frame,
        observed_at,
        close,
        prev_close,
        CASE WHEN prev_close IS NOT NULL THEN GREATEST(close - prev_close, 0) ELSE NULL END AS gain,
        CASE WHEN prev_close IS NOT NULL THEN GREATEST(prev_close - close, 0) ELSE NULL END AS loss
    FROM base
),
rsi_seed AS (
    SELECT
        symbol,
        frame,
        observed_at,
        close,
        AVG(gain) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain_14,
        AVG(loss) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss_14
    FROM deltas
),
rsi_calc AS (
    SELECT
        symbol,
        frame,
        observed_at,
        close,
        CASE
            WHEN avg_loss_14 = 0 AND avg_gain_14 > 0 THEN 100
            WHEN avg_gain_14 = 0 AND avg_loss_14 > 0 THEN 0
            WHEN avg_gain_14 = 0 AND avg_loss_14 = 0 THEN 50
            WHEN avg_loss_14 IS NULL THEN NULL
            ELSE 100 - (100 / (1 + (avg_gain_14 / NULLIF(avg_loss_14, 0))))
        END AS rsi_14
    FROM rsi_seed
),
ema_seed AS (
    SELECT
        symbol,
        frame,
        observed_at,
        close,
        AVG(close) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema12_proxy,
        AVG(close) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema26_proxy
    FROM base
),
macd_calc AS (
    SELECT
        symbol,
        frame,
        observed_at,
        (ema12_proxy - ema26_proxy) AS macd_line,
        AVG(ema12_proxy - ema26_proxy) OVER (PARTITION BY symbol, frame ORDER BY observed_at ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS macd_signal
    FROM ema_seed
),
joined AS (
    SELECT
        r.symbol,
        r.frame,
        r.observed_at,
        r.rsi_14,
        LAG(r.rsi_14) OVER (PARTITION BY r.symbol, r.frame ORDER BY r.observed_at) AS rsi_14_prev1,
        m.macd_line,
        m.macd_signal,
        (m.macd_line - m.macd_signal) AS macd_hist
    FROM rsi_calc r
    JOIN macd_calc m USING (symbol, frame, observed_at)
),
calc AS (
    SELECT
        symbol,
        frame,
        observed_at,
        CASE WHEN rsi_14 IS NOT NULL AND macd_line IS NOT NULL AND macd_signal IS NOT NULL THEN TRUE ELSE FALSE END AS feature_is_valid,
        rsi_14,
        rsi_14_prev1,
        (rsi_14 - rsi_14_prev1) AS rsi_14_delta_1,
        (rsi_14 - LAG(rsi_14, 3) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) / 3.0 AS rsi_14_slope_3,
        (rsi_14 - LAG(rsi_14, 5) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) / 5.0 AS rsi_14_slope_5,
        (rsi_14 > 50) AS rsi_above_50_flag,
        (rsi_14 < 50) AS rsi_below_50_flag,
        (rsi_14 >= 70) AS rsi_overbought_70_flag,
        (rsi_14 <= 30) AS rsi_oversold_30_flag,
        (rsi_14_prev1 <= 30 AND rsi_14 > 30) AS rsi_cross_up_30_flag,
        (rsi_14_prev1 >= 70 AND rsi_14 < 70) AS rsi_cross_down_70_flag,
        (rsi_14_prev1 <= 50 AND rsi_14 > 50) AS rsi_cross_up_50_flag,
        (rsi_14_prev1 >= 50 AND rsi_14 < 50) AS rsi_cross_down_50_flag,
        macd_line AS macd_12_26_9_line,
        macd_signal AS macd_12_26_9_signal,
        macd_hist AS macd_12_26_9_hist,
        (macd_hist - LAG(macd_hist) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) AS macd_hist_delta_1,
        (macd_hist - LAG(macd_hist, 3) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) / 3.0 AS macd_hist_slope_3,
        (macd_hist - LAG(macd_hist, 5) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) / 5.0 AS macd_hist_slope_5,
        (LAG(macd_line) OVER (PARTITION BY symbol, frame ORDER BY observed_at) <= LAG(macd_signal) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AND macd_line > macd_signal) AS macd_bull_cross_flag,
        (LAG(macd_line) OVER (PARTITION BY symbol, frame ORDER BY observed_at) >= LAG(macd_signal) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AND macd_line < macd_signal) AS macd_bear_cross_flag,
        (LAG(macd_hist) OVER (PARTITION BY symbol, frame ORDER BY observed_at) <= 0 AND macd_hist > 0) AS macd_hist_cross_up_0_flag,
        (LAG(macd_hist) OVER (PARTITION BY symbol, frame ORDER BY observed_at) >= 0 AND macd_hist < 0) AS macd_hist_cross_down_0_flag,
        (rsi_14 > 50 AND macd_line > macd_signal AND macd_hist > 0) AS rsi_macd_bullish_cluster_flag,
        (rsi_14 < 50 AND macd_line < macd_signal AND macd_hist < 0) AS rsi_macd_bearish_cluster_flag,
        ((rsi_14_prev1 <= 30 AND rsi_14 > 30) OR (rsi_14_prev1 <= 50 AND rsi_14 > 50)) AND ((LAG(macd_line) OVER (PARTITION BY symbol, frame ORDER BY observed_at) <= LAG(macd_signal) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AND macd_line > macd_signal) OR (LAG(macd_hist) OVER (PARTITION BY symbol, frame ORDER BY observed_at) <= 0 AND macd_hist > 0)) AS rsi_macd_bullish_reversal_flag,
        ((rsi_14_prev1 >= 70 AND rsi_14 < 70) OR (rsi_14_prev1 >= 50 AND rsi_14 < 50)) AND ((LAG(macd_line) OVER (PARTITION BY symbol, frame ORDER BY observed_at) >= LAG(macd_signal) OVER (PARTITION BY symbol, frame ORDER BY observed_at) AND macd_line < macd_signal) OR (LAG(macd_hist) OVER (PARTITION BY symbol, frame ORDER BY observed_at) >= 0 AND macd_hist < 0)) AS rsi_macd_bearish_reversal_flag,
        ((rsi_14 - LAG(rsi_14, 3) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) > 0 AND (macd_hist - LAG(macd_hist, 3) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) > 0 AND (macd_hist - LAG(macd_hist) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) > 0) AS rsi_macd_momentum_accel_up_flag,
        ((rsi_14 - LAG(rsi_14, 3) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) < 0 AND (macd_hist - LAG(macd_hist, 3) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) < 0 AND (macd_hist - LAG(macd_hist) OVER (PARTITION BY symbol, frame ORDER BY observed_at)) < 0) AS rsi_macd_momentum_accel_down_flag
    FROM joined
)
INSERT INTO collector.feature_rsi_macd_tf (
    symbol, frame, observed_at, feature_is_valid,
    rsi_14, rsi_14_prev1, rsi_14_delta_1, rsi_14_slope_3, rsi_14_slope_5,
    rsi_above_50_flag, rsi_below_50_flag, rsi_overbought_70_flag, rsi_oversold_30_flag,
    rsi_cross_up_30_flag, rsi_cross_down_70_flag, rsi_cross_up_50_flag, rsi_cross_down_50_flag,
    macd_12_26_9_line, macd_12_26_9_signal, macd_12_26_9_hist,
    macd_hist_delta_1, macd_hist_slope_3, macd_hist_slope_5,
    macd_bull_cross_flag, macd_bear_cross_flag, macd_hist_cross_up_0_flag, macd_hist_cross_down_0_flag,
    rsi_macd_bullish_cluster_flag, rsi_macd_bearish_cluster_flag,
    rsi_macd_bullish_reversal_flag, rsi_macd_bearish_reversal_flag,
    rsi_macd_momentum_accel_up_flag, rsi_macd_momentum_accel_down_flag,
    computed_at_utc
)
SELECT
    symbol, frame, observed_at, feature_is_valid,
    rsi_14, rsi_14_prev1, rsi_14_delta_1, rsi_14_slope_3, rsi_14_slope_5,
    rsi_above_50_flag, rsi_below_50_flag, rsi_overbought_70_flag, rsi_oversold_30_flag,
    rsi_cross_up_30_flag, rsi_cross_down_70_flag, rsi_cross_up_50_flag, rsi_cross_down_50_flag,
    macd_12_26_9_line, macd_12_26_9_signal, macd_12_26_9_hist,
    macd_hist_delta_1, macd_hist_slope_3, macd_hist_slope_5,
    macd_bull_cross_flag, macd_bear_cross_flag, macd_hist_cross_up_0_flag, macd_hist_cross_down_0_flag,
    rsi_macd_bullish_cluster_flag, rsi_macd_bearish_cluster_flag,
    rsi_macd_bullish_reversal_flag, rsi_macd_bearish_reversal_flag,
    rsi_macd_momentum_accel_up_flag, rsi_macd_momentum_accel_down_flag,
    NOW()
FROM calc
ON CONFLICT (symbol, frame, observed_at)
DO UPDATE SET
    feature_is_valid = EXCLUDED.feature_is_valid,
    rsi_14 = EXCLUDED.rsi_14,
    rsi_14_prev1 = EXCLUDED.rsi_14_prev1,
    rsi_14_delta_1 = EXCLUDED.rsi_14_delta_1,
    rsi_14_slope_3 = EXCLUDED.rsi_14_slope_3,
    rsi_14_slope_5 = EXCLUDED.rsi_14_slope_5,
    rsi_above_50_flag = EXCLUDED.rsi_above_50_flag,
    rsi_below_50_flag = EXCLUDED.rsi_below_50_flag,
    rsi_overbought_70_flag = EXCLUDED.rsi_overbought_70_flag,
    rsi_oversold_30_flag = EXCLUDED.rsi_oversold_30_flag,
    rsi_cross_up_30_flag = EXCLUDED.rsi_cross_up_30_flag,
    rsi_cross_down_70_flag = EXCLUDED.rsi_cross_down_70_flag,
    rsi_cross_up_50_flag = EXCLUDED.rsi_cross_up_50_flag,
    rsi_cross_down_50_flag = EXCLUDED.rsi_cross_down_50_flag,
    macd_12_26_9_line = EXCLUDED.macd_12_26_9_line,
    macd_12_26_9_signal = EXCLUDED.macd_12_26_9_signal,
    macd_12_26_9_hist = EXCLUDED.macd_12_26_9_hist,
    macd_hist_delta_1 = EXCLUDED.macd_hist_delta_1,
    macd_hist_slope_3 = EXCLUDED.macd_hist_slope_3,
    macd_hist_slope_5 = EXCLUDED.macd_hist_slope_5,
    macd_bull_cross_flag = EXCLUDED.macd_bull_cross_flag,
    macd_bear_cross_flag = EXCLUDED.macd_bear_cross_flag,
    macd_hist_cross_up_0_flag = EXCLUDED.macd_hist_cross_up_0_flag,
    macd_hist_cross_down_0_flag = EXCLUDED.macd_hist_cross_down_0_flag,
    rsi_macd_bullish_cluster_flag = EXCLUDED.rsi_macd_bullish_cluster_flag,
    rsi_macd_bearish_cluster_flag = EXCLUDED.rsi_macd_bearish_cluster_flag,
    rsi_macd_bullish_reversal_flag = EXCLUDED.rsi_macd_bullish_reversal_flag,
    rsi_macd_bearish_reversal_flag = EXCLUDED.rsi_macd_bearish_reversal_flag,
    rsi_macd_momentum_accel_up_flag = EXCLUDED.rsi_macd_momentum_accel_up_flag,
    rsi_macd_momentum_accel_down_flag = EXCLUDED.rsi_macd_momentum_accel_down_flag,
    computed_at_utc = NOW()
"""


class FeatureRsiMacdBuilder:
    def __init__(self, db: Database):
        self.db = db

    def build_window(self, symbol: str, start_at, end_at) -> int:
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(UPSERT_RSI_MACD_SQL, {'symbol': symbol, 'start_at': start_at, 'end_at': end_at})
                affected = cur.rowcount if cur.rowcount != -1 else 0
            conn.commit()
        return affected


def main() -> None:
    parser = argparse.ArgumentParser(description='Build RSI+MACD features from feature_base_tf')
    parser.add_argument('--symbol', default='BTCUSDC')
    parser.add_argument('--start-at', required=True)
    parser.add_argument('--end-at', required=True)
    parser.add_argument('--apply-schema', action='store_true')
    args = parser.parse_args()

    settings = get_settings()
    db = Database(settings.database_url)
    if args.apply_schema:
        db.apply_sql_file(str(Path(__file__).resolve().parent / 'sql' / '003_feature_rsi_macd.sql'))

    builder = FeatureRsiMacdBuilder(db)
    affected = builder.build_window(symbol=args.symbol.upper(), start_at=args.start_at, end_at=args.end_at)
    print(f'Affected feature_rsi_macd_tf rows: {affected}')


if __name__ == '__main__':
    main()
