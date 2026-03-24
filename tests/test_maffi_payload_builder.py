from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from TRADING_ALGOS.common.tick_normalizer import normalize_ticks
from TRADING_ALGOS.common.tick_to_features_engine import build_tick_feature_candles
from Maffi.runtime.enums import QualityStatus
from Maffi.runtime.payload_builder import build_maffi_payload


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
