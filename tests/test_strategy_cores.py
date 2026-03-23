from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from TRADING_ALGOS.common.tick_to_features_engine import CandleFeatureRow
from TRADING_ALGOS.strategy_cores import (
    compute_elliott,
    compute_levels_fibo_hv,
    compute_rsi_macd,
    compute_volume,
)


class StrategyCoreTests(unittest.TestCase):
    def test_compute_rsi_macd_returns_required_fields(self) -> None:
        result = compute_rsi_macd(self._candles(40))
        self.assertEqual(result.features["timeframe"], "1m")
        self.assertIn(result.features["momentum_state"], {"bullish", "bearish", "mixed"})
        self.assertIn(result.features["momentum_strength"], {"weak", "medium", "strong"})

    def test_compute_levels_fibo_hv_returns_required_fields(self) -> None:
        result = compute_levels_fibo_hv(self._candles(25))
        self.assertIn("nearest_support", result.features)
        self.assertIn(result.features["structure_state"], {"bullish", "bearish", "range"})

    def test_compute_volume_returns_required_fields(self) -> None:
        result = compute_volume(self._candles(25))
        self.assertIn("relative_volume", result.features)
        self.assertIn(result.features["pressure_side"], {"buyers", "sellers", "mixed"})

    def test_compute_elliott_defaults_to_candidate_language(self) -> None:
        result = compute_elliott(self._candles(20))
        self.assertIn(result.features["pattern_state"], {"candidate", "unclear"})
        self.assertIn(result.features["elliott_confidence_state"], {"low", "medium"})

    @staticmethod
    def _candles(count: int) -> list[CandleFeatureRow]:
        candles: list[CandleFeatureRow] = []
        start = datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc)
        for index in range(count):
            open_price = Decimal("100") + Decimal(index)
            close_price = open_price + Decimal("0.5")
            candles.append(
                CandleFeatureRow(
                    timeframe="1m",
                    bucket_start_utc=start + timedelta(minutes=index),
                    bucket_end_utc=start + timedelta(minutes=index + 1),
                    open=open_price,
                    high=close_price + Decimal("0.5"),
                    low=open_price - Decimal("0.5"),
                    close=close_price,
                    volume=Decimal("10") + Decimal(index % 3),
                    trade_count=10 + index,
                    buy_volume=Decimal("6") + Decimal(index % 2),
                    sell_volume=Decimal("4"),
                    delta=Decimal("2") + Decimal(index % 2),
                    imbalance=Decimal("0.2"),
                    trade_speed=Decimal("0.2"),
                    relative_volume_baseline=Decimal("10"),
                    is_empty=False,
                    is_incomplete=False,
                )
            )
        return candles


if __name__ == "__main__":
    unittest.main()
