from __future__ import annotations

import unittest

from Maffi.runtime.preprocessing import (
    aggregate_ohlcv,
    classify_market_regime,
    classify_volatility_regime,
    compute_support_resistance,
    compute_trend_structure,
    extract_preprocessing_features,
    sanitize_ticks,
)
from tests.fixtures.maffi_preprocessing_fixtures import (
    noisy_input_ticks,
    ranging_noisy_ticks,
    sparse_ticks,
    trending_ticks,
)


class MaffiPreprocessingTests(unittest.TestCase):
    def test_ohlcv_aggregation_for_1m_5m_15m(self) -> None:
        ticks = trending_ticks()

        candles_1m = aggregate_ohlcv(ticks, "1m")
        candles_5m = aggregate_ohlcv(ticks, "5m")
        candles_15m = aggregate_ohlcv(ticks, "15m")

        self.assertEqual(len(candles_1m), 45)
        self.assertEqual(len(candles_5m), 9)
        self.assertEqual(len(candles_15m), 3)
        self.assertAlmostEqual(candles_5m[0].open, 100.0)
        self.assertAlmostEqual(candles_5m[0].close, 101.4)

    def test_trend_structure_and_market_regime_on_trending_fixture(self) -> None:
        ticks = trending_ticks()
        candles = aggregate_ohlcv(ticks, "5m")
        trend = compute_trend_structure(candles)

        self.assertEqual(trend.direction, "up")
        self.assertGreater(trend.strength, 0.2)

        market_regime = classify_market_regime(trend=trend, volatility=0.002)
        self.assertEqual(market_regime.label, "trend")
        self.assertGreaterEqual(market_regime.scores.trend, market_regime.scores.ranging)

    def test_support_resistance_and_ranging_regime_for_noisy_input(self) -> None:
        ticks = ranging_noisy_ticks()
        candles = aggregate_ohlcv(ticks, "1m")
        sr = compute_support_resistance(candles)

        self.assertAlmostEqual(sr.support, 99.2)
        self.assertAlmostEqual(sr.resistance, 101.0)
        self.assertGreaterEqual(sr.support_touches, 1)
        self.assertGreaterEqual(sr.resistance_touches, 1)

        trend = compute_trend_structure(candles)
        regime = classify_market_regime(trend=trend, volatility=0.01)
        self.assertIn(regime.label, {"ranging", "noisy", "trend"})

    def test_sanitize_noisy_and_sparse_inputs(self) -> None:
        cleaned = sanitize_ticks(noisy_input_ticks())
        self.assertEqual(len(cleaned), 3)
        self.assertLessEqual(cleaned[0].ts, cleaned[-1].ts)

        sparse = sparse_ticks()
        features = extract_preprocessing_features(sparse)
        self.assertEqual(features.features.tick_count, 3)
        self.assertEqual(len(features.features.ohlcv_by_timeframe["15m"]), 2)

    def test_feature_extraction_builds_entry_candidates_and_quality(self) -> None:
        result = extract_preprocessing_features(trending_ticks())
        entries = result.features.entry_candidates

        self.assertEqual(len(entries), 3)
        for candidate in entries:
            self.assertGreaterEqual(candidate.quality, 0.0)
            self.assertLessEqual(candidate.quality, 1.0)

        self.assertEqual(result.features.market_regime.label, "trend")
        volatility_regime = classify_volatility_regime(result.features.realized_vol)
        self.assertEqual(volatility_regime.label, result.features.volatility_regime.label)


if __name__ == "__main__":
    unittest.main()
