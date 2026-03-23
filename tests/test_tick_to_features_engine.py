from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from TRADING_ALGOS.common.tick_normalizer import NormalizedTick
from TRADING_ALGOS.common.tick_to_features_engine import (
    BUCKET_ALIGNMENT_POLICY,
    EMPTY_BUCKET_POLICY,
    INCOMPLETE_LAST_CANDLE_POLICY,
    RELATIVE_VOLUME_BASELINE_BUCKETS,
    build_tick_feature_candles,
    floor_bucket_start,
    minimum_warmup_window,
)


class TickToFeaturesEngineTests(unittest.TestCase):
    def test_build_tick_feature_candles_computes_ohlcv_and_microstructure(self) -> None:
        result = build_tick_feature_candles(
            [
                self._tick("w0", "2026-03-23T00:00:10Z", "100", "1", side="buy"),
                self._tick("w1", "2026-03-23T00:01:15Z", "101", "1", side="buy"),
                self._tick("w2", "2026-03-23T00:02:20Z", "102", "1", side="sell"),
                self._tick("w3", "2026-03-23T00:03:25Z", "103", "1", side="buy"),
                self._tick("w4", "2026-03-23T00:04:30Z", "104", "1", side="buy"),
                self._tick("w5", "2026-03-23T00:05:35Z", "105", "1", side="sell"),
                self._tick("w6", "2026-03-23T00:06:40Z", "106", "1", side="buy"),
                self._tick("w7", "2026-03-23T00:07:45Z", "107", "1", side="sell"),
                self._tick("w8", "2026-03-23T00:08:10Z", "108", "1", side="buy"),
                self._tick("w9", "2026-03-23T00:09:10Z", "109", "1", side="sell"),
                self._tick("w10", "2026-03-23T00:10:10Z", "110", "1", side="buy"),
                self._tick("w11", "2026-03-23T00:11:10Z", "111", "1", side="sell"),
                self._tick("w12", "2026-03-23T00:12:10Z", "112", "1", side="buy"),
                self._tick("w13", "2026-03-23T00:13:10Z", "113", "1", side="sell"),
                self._tick("w14", "2026-03-23T00:14:10Z", "114", "1", side="buy"),
                self._tick("w15", "2026-03-23T00:15:10Z", "115", "1", side="sell"),
                self._tick("w16", "2026-03-23T00:16:10Z", "116", "1", side="buy"),
                self._tick("w17", "2026-03-23T00:17:10Z", "117", "1", side="sell"),
                self._tick("w18", "2026-03-23T00:18:10Z", "118", "1", side="buy"),
                self._tick("w19", "2026-03-23T00:19:10Z", "119", "1", side="sell"),
                self._tick("a", "2026-03-23T00:20:05Z", "120", "0.7", side="buy"),
                self._tick("b", "2026-03-23T00:20:40Z", "125", "0.5", side="sell"),
                self._tick("c", "2026-03-23T00:21:10Z", "123", "0.3", side="buy"),
            ],
            window_from=datetime(2026, 3, 23, 0, 20, 5, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 0, 21, 20, tzinfo=timezone.utc),
            timeframes=("1m",),
        )

        candles = result.candles_by_timeframe["1m"]
        first = candles[0]
        second = candles[1]

        self.assertEqual(first.bucket_start_utc, datetime(2026, 3, 23, 0, 20, 0, tzinfo=timezone.utc))
        self.assertEqual(first.open, Decimal("120"))
        self.assertEqual(first.high, Decimal("125"))
        self.assertEqual(first.low, Decimal("120"))
        self.assertEqual(first.close, Decimal("125"))
        self.assertEqual(first.volume, Decimal("1.2"))
        self.assertEqual(first.trade_count, 2)
        self.assertEqual(first.buy_volume, Decimal("0.7"))
        self.assertEqual(first.sell_volume, Decimal("0.5"))
        self.assertEqual(first.delta, Decimal("0.2"))
        self.assertEqual(first.imbalance, Decimal("0.2") / Decimal("1.2"))
        self.assertEqual(first.trade_speed, Decimal("2") / Decimal("60"))
        self.assertEqual(first.relative_volume_baseline, Decimal("1"))
        self.assertFalse(first.is_empty)
        self.assertFalse(first.is_incomplete)

        self.assertTrue(second.is_incomplete)
        self.assertEqual(second.open, Decimal("123"))
        self.assertEqual(second.close, Decimal("123"))
        self.assertEqual(second.relative_volume_baseline, Decimal("1.01"))

        self.assertEqual(result.metadata.bucket_alignment_policy, BUCKET_ALIGNMENT_POLICY)
        self.assertEqual(result.metadata.empty_bucket_policy, EMPTY_BUCKET_POLICY)
        self.assertEqual(result.metadata.incomplete_last_candle_policy, INCOMPLETE_LAST_CANDLE_POLICY)
        self.assertEqual(
            result.metadata.minimum_warmup_window_by_timeframe["1m"],
            timedelta(minutes=RELATIVE_VOLUME_BASELINE_BUCKETS),
        )

    def test_engine_keeps_empty_bucket_and_forward_fills_prices(self) -> None:
        result = build_tick_feature_candles(
            [
                self._tick("seed", "2026-03-23T00:00:40Z", "100", "1", side="buy"),
                self._tick("later", "2026-03-23T00:02:10Z", "102", "0.4", side="sell"),
            ],
            window_from=datetime(2026, 3, 23, 0, 1, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 0, 3, 0, tzinfo=timezone.utc),
            timeframes=("1m",),
        )

        first, second = result.candles_by_timeframe["1m"]
        self.assertTrue(first.is_empty)
        self.assertEqual(first.open, Decimal("100"))
        self.assertEqual(first.high, Decimal("100"))
        self.assertEqual(first.low, Decimal("100"))
        self.assertEqual(first.close, Decimal("100"))
        self.assertEqual(first.volume, Decimal("0"))
        self.assertEqual(first.trade_count, 0)
        self.assertEqual(first.buy_volume, Decimal("0"))
        self.assertEqual(first.sell_volume, Decimal("0"))
        self.assertEqual(first.delta, Decimal("0"))
        self.assertEqual(first.imbalance, Decimal("0"))

        self.assertFalse(second.is_empty)
        self.assertEqual(second.open, Decimal("102"))

    def test_alignment_and_minimum_warmup_helpers(self) -> None:
        self.assertEqual(
            floor_bucket_start(datetime(2026, 3, 23, 12, 7, 59, tzinfo=timezone.utc), "5m"),
            datetime(2026, 3, 23, 12, 5, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(minimum_warmup_window("60m"), timedelta(hours=20))

    @staticmethod
    def _tick(trade_id: str, event_time_utc: str, price: str, quantity: str, *, side: str) -> NormalizedTick:
        return NormalizedTick(
            source="collector",
            symbol="BTCUSDC",
            trade_id=trade_id,
            event_time_utc=datetime.fromisoformat(event_time_utc.replace("Z", "+00:00")),
            price=Decimal(price),
            quantity=Decimal(quantity),
            side=side,
        )


if __name__ == "__main__":
    unittest.main()
