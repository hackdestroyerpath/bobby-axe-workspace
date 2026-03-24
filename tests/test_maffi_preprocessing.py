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
        result = extract_preprocessing_features(sparse)
        self.assertEqual(result.features.tick_count, 3)
        self.assertEqual(len(result.features.ohlcv_by_timeframe["15m"]), 2)
        self.assertTrue(result.feature_extraction.degradation.sparse_input)
        self.assertIn("sparse_input", result.feature_extraction.degradation.triggered_flags)
        self.assertGreaterEqual(result.features.market_snapshot.trade_count_1m, 1)
        self.assertIsNotNone(result.features.market_snapshot.vwap_1m)

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
        self.assertIsNotNone(result.feature_extraction.degradation.thresholds.max_gap_ratio)
        self.assertGreater(result.features.market_snapshot.last_price, 0)
        self.assertGreater(result.features.market_snapshot.volume_1m, 0)
        self.assertGreater(result.features.market_snapshot.notional_5m, 0)
        self.assertIsNotNone(result.features.price_structure.open_1m)
        self.assertIsNotNone(result.features.price_structure.high_5m)
        self.assertIsNotNone(result.features.price_structure.local_high_15m)
        self.assertGreaterEqual(result.features.price_structure.range_width_1m, 0)
        self.assertIsNotNone(result.features.volatility.atr_like_1m)
        self.assertIsNotNone(result.features.volatility.atr_like_5m)
        self.assertEqual(result.features.volatility.volatility_regime_label, result.features.volatility_regime.label)
        self.assertIsNotNone(result.features.volatility.volatility_stability_score)
        self.assertGreaterEqual(result.features.order_flow.buy_volume_1m, 0)
        self.assertGreaterEqual(result.features.order_flow.sell_volume_5m, 0)
        self.assertIn(result.features.order_flow.dominant_side, {"buyers", "sellers"})
        self.assertGreaterEqual(result.features.order_flow.order_flow_confidence, 0)
        self.assertIn(result.features.regime.market_regime_label, {"trend", "ranging", "noisy"})
        self.assertGreaterEqual(result.features.regime.regime_confidence, 0)
        self.assertGreaterEqual(result.features.regime.trend_strength_score, 0)
        self.assertLessEqual(result.features.support_resistance_features.support_zone_low, result.features.support_resistance_features.support_zone_high)
        self.assertLessEqual(result.features.support_resistance_features.resistance_zone_low, result.features.support_resistance_features.resistance_zone_high)
        self.assertGreaterEqual(result.features.support_resistance_features.level_respect_score, 0)
        self.assertGreaterEqual(result.features.quality_trust.coverage_ratio, 0)
        self.assertGreaterEqual(result.features.quality_trust.liquidity_quality_score, 0)
        self.assertGreaterEqual(result.features.quality_trust.payload_confidence, 0)

    def test_sparse_input_quality_trust_degrades_confidence(self) -> None:
        result = extract_preprocessing_features(sparse_ticks())
        self.assertLess(result.features.quality_trust.payload_confidence, 1.0)
        self.assertIn("sparse_input", result.features.quality_trust.degradation_flags)


if __name__ == "__main__":
    unittest.main()
