from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from TRADING_ALGOS.common.tick_normalizer import normalize_ticks
from TRADING_ALGOS.common.tick_to_features_engine import build_tick_feature_candles
from Maffi.runtime.enums import QualityStatus
from Maffi.runtime.payload_builder import build_llm_algo_payload, build_maffi_payload
from Maffi.runtime.preprocessing import extract_preprocessing_features
from tests.fixtures.maffi_preprocessing_fixtures import sparse_ticks


class MaffiPayloadBuilderIntegrationTests(unittest.TestCase):
    def test_healthy_input(self) -> None:
        normalization = normalize_ticks(
            self._series(step_seconds=50, count=90),
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 15, tzinfo=timezone.utc),
            gap_threshold=timedelta(minutes=4),
        )
        features = build_tick_feature_candles(
            normalization.ticks,
            window_from=normalization.window_from,
            window_to=normalization.window_to,
            include_incomplete_candle=True,
        )

        payload = build_maffi_payload(
            symbol="BTCUSDC",
            source="Data_collector",
            window_from=normalization.window_from,
            window_to=normalization.window_to,
            normalization_result=normalization,
            feature_result=features,
        )

        self.assertEqual(payload.input_quality_status, QualityStatus.OK)
        self.assertLess(payload.reject_score, 60)
        self.assertEqual(len(payload.entry_candidates), 3)
        self.assertGreater(payload.atr, 0)

    def test_degraded_but_usable_input(self) -> None:
        normalization = normalize_ticks(
            self._series(step_seconds=95, count=45),
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 15, tzinfo=timezone.utc),
            gap_threshold=timedelta(seconds=70),
            page_complete=False,
        )
        features = build_tick_feature_candles(
            normalization.ticks,
            window_from=normalization.window_from,
            window_to=normalization.window_to,
            include_incomplete_candle=True,
        )

        payload = build_maffi_payload(
            symbol="BTCUSDC",
            source="Data_collector",
            window_from=normalization.window_from,
            window_to=normalization.window_to,
            normalization_result=normalization,
            feature_result=features,
        )

        self.assertEqual(payload.input_quality_status, QualityStatus.DEGRADED)
        self.assertLess(payload.reject_score, 60)
        reasons = payload.context["payload_builder"]["degradation_reasons"]
        self.assertTrue(any(reason["code"] in {"heavy_gaps", "truncation", "low_coverage"} for reason in reasons))

    def test_hard_reject_input(self) -> None:
        normalization = normalize_ticks(
            [],
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 15, tzinfo=timezone.utc),
            gap_threshold=timedelta(minutes=2),
        )

        payload = build_maffi_payload(
            symbol="BTCUSDC",
            source="Data_collector",
            window_from=normalization.window_from,
            window_to=normalization.window_to,
            normalization_result=normalization,
        )

        self.assertEqual(payload.input_quality_status, QualityStatus.BAD)
        self.assertGreaterEqual(payload.reject_score, 60)
        reasons = payload.context["payload_builder"]["degradation_reasons"]
        self.assertTrue(any(reason["code"] == "empty_window" for reason in reasons))

    def test_payload_contains_structured_degradation_trace_when_preprocessing_is_provided(self) -> None:
        normalization = normalize_ticks(
            self._series(step_seconds=50, count=45),
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 15, tzinfo=timezone.utc),
            gap_threshold=timedelta(minutes=4),
        )
        preprocessing_result = extract_preprocessing_features(sparse_ticks())

        payload = build_maffi_payload(
            symbol="BTCUSDC",
            source="Data_collector",
            window_from=normalization.window_from,
            window_to=normalization.window_to,
            normalization_result=normalization,
            preprocessing_result=preprocessing_result,
        )

        degradation_trace = payload.context["payload_builder"]["degradation_trace"]
        self.assertIsInstance(degradation_trace, dict)
        self.assertTrue(degradation_trace["sparse_input"])
        self.assertIn("sparse_input", degradation_trace["triggered_flags"])

    def test_payload_contains_new_algo_payload_blocks(self) -> None:
        normalization = normalize_ticks(
            self._series(step_seconds=50, count=60),
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 0, tzinfo=timezone.utc),
            gap_threshold=timedelta(minutes=4),
        )
        preprocessing_result = extract_preprocessing_features(sparse_ticks())

        payload = build_maffi_payload(
            symbol="BTCUSDC",
            source="Data_collector",
            window_from=normalization.window_from,
            window_to=normalization.window_to,
            normalization_result=normalization,
            preprocessing_result=preprocessing_result,
        )

        algo_payload = payload.context["payload_builder"]["algo_payload"]
        self.assertIn("request_context", algo_payload)
        self.assertIn("market_snapshot", algo_payload)
        self.assertIn("price_structure", algo_payload)
        self.assertIn("open_1m", algo_payload["price_structure"])
        self.assertIn("range_width_5m", algo_payload["price_structure"])
        self.assertIn("volatility", algo_payload)
        self.assertIn("atr_like_5m", algo_payload["volatility"])
        self.assertIn("order_flow", algo_payload)
        self.assertIn("delta_5m", algo_payload["order_flow"])
        self.assertIn("market_regime", algo_payload)
        self.assertIn("trend_strength_score", algo_payload["market_regime"])
        self.assertIn("support_resistance", algo_payload)
        self.assertIn("support_zone_low", algo_payload["support_resistance"])
        self.assertIn("quality_trust", algo_payload)
        self.assertIn("payload_confidence", algo_payload["quality_trust"])
        self.assertIn("volatility", algo_payload)
        self.assertIn("order_flow", algo_payload)
        self.assertIn("market_regime", algo_payload)
        self.assertIn("support_resistance", algo_payload)
        self.assertIn("grid_geometry_hints", algo_payload)
        self.assertIn("grid_candidates", algo_payload)
        self.assertIn("quality_trust", algo_payload)
        self.assertIn("prompt_control", algo_payload)
        self.assertEqual(algo_payload["request_context"]["ticker"], "BTCUSDC")
        self.assertEqual(algo_payload["market_snapshot"]["last_price"], preprocessing_result.features.market_snapshot.last_price)
        self.assertEqual(algo_payload["support_resistance"]["support_zone_low"], preprocessing_result.features.support_resistance_features.support_zone_low)
        self.assertEqual(algo_payload["quality_trust"]["payload_confidence"], preprocessing_result.features.quality_trust.payload_confidence)

    def test_build_llm_algo_payload_returns_structured_blocks(self) -> None:
        algo_payload = build_llm_algo_payload(
            symbol="BTCUSDC",
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 0, tzinfo=timezone.utc),
            quality=QualityStatus.OK,
            last_price=87260.0,
            support_level=86980.0,
            resistance_level=87640.0,
            atr=120.0,
            coverage_ratio=0.98,
            reasons=[],
        )

        self.assertEqual(algo_payload.request_context.ticker, "BTCUSDC")
        self.assertEqual(algo_payload.request_context.direction, "long")
        self.assertEqual(algo_payload.market_snapshot.last_price, 87260.0)
        self.assertGreaterEqual(len(algo_payload.grid_candidates.candidates), 3)
        self.assertEqual(algo_payload.quality_trust.input_quality_status, "ok")

    def test_geometry_hints_are_anchored_to_preprocessing_zones(self) -> None:
        preprocessing_result = extract_preprocessing_features(sparse_ticks())
        algo_payload = build_llm_algo_payload(
            symbol="BTCUSDC",
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 0, tzinfo=timezone.utc),
            quality=QualityStatus.DEGRADED,
            last_price=101.0,
            support_level=99.0,
            resistance_level=103.0,
            atr=1.0,
            coverage_ratio=0.8,
            reasons=[],
            preprocessing_result=preprocessing_result,
        )
        self.assertEqual(
            algo_payload.grid_geometry_hints.recommended_price_down,
            preprocessing_result.features.support_resistance_features.support_zone_low,
        )
        self.assertEqual(
            algo_payload.grid_geometry_hints.recommended_price_up,
            preprocessing_result.features.support_resistance_features.resistance_zone_high,
        )

    @staticmethod
    def _series(*, step_seconds: int, count: int) -> list[dict[str, object]]:
        base = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)
        rows: list[dict[str, object]] = []
        for index in range(count):
            rows.append(
                {
                    "source": "Data_collector",
                    "symbol": "BTCUSDC",
                    "trade_id": f"t-{index}",
                    "event_time_utc": base + timedelta(seconds=index * step_seconds),
                    "price": Decimal("86000") + Decimal(index),
                    "quantity": Decimal("0.1") + Decimal(index % 3) / Decimal("10"),
                    "side": "buy" if index % 2 == 0 else "sell",
                }
            )
        return rows


if __name__ == "__main__":
    unittest.main()
