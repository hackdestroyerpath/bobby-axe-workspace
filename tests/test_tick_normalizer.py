from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from TRADING_ALGOS.common.tick_normalizer import (
    PARTIAL_REASON_EMPTY_WINDOW,
    PARTIAL_REASON_GAP_HEAVY,
    PARTIAL_REASON_PAGINATION,
    PARTIAL_REASON_RETENTION,
    normalize_ticks,
)


class TickNormalizerTests(unittest.TestCase):
    def test_normalize_ticks_deduplicates_sorts_and_casts_decimals(self) -> None:
        result = normalize_ticks(
            [
                {
                    "source": "collector",
                    "symbol": "BTCUSDC",
                    "trade_id": "2",
                    "event_time_utc": "2026-03-23T00:00:10Z",
                    "price": "101.25",
                    "quantity": "0.4",
                },
                {
                    "source": "collector",
                    "symbol": "BTCUSDC",
                    "trade_id": "1",
                    "event_time_utc": "2026-03-23T00:00:00Z",
                    "price": 100,
                    "quantity": 0.2,
                },
                {
                    "source": "collector",
                    "symbol": "BTCUSDC",
                    "trade_id": "2",
                    "event_time_utc": "2026-03-23T00:00:10Z",
                    "price": "101.25",
                    "quantity": "0.4",
                },
            ],
            window_from=datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 0, 1, 0, tzinfo=timezone.utc),
            gap_threshold=timedelta(seconds=15),
        )

        self.assertEqual(result.tick_count, 2)
        self.assertEqual(result.deduplicated_count, 1)
        self.assertEqual([tick.trade_id for tick in result.ticks], ["1", "2"])
        self.assertEqual(result.ticks[0].price, Decimal("100"))
        self.assertEqual(result.ticks[0].quantity, Decimal("0.2"))
        self.assertFalse(result.is_partial)
        self.assertIsNone(result.partial_reason)
        self.assertAlmostEqual(result.coverage_ratio, 10 / 60)

    def test_normalize_ticks_marks_empty_window(self) -> None:
        result = normalize_ticks(
            [],
            window_from=datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 0, 5, 0, tzinfo=timezone.utc),
            gap_threshold=timedelta(seconds=30),
        )

        self.assertTrue(result.empty_window)
        self.assertTrue(result.is_partial)
        self.assertEqual(result.partial_reason, PARTIAL_REASON_EMPTY_WINDOW)
        self.assertEqual(result.coverage_ratio, 0.0)

    def test_normalize_ticks_marks_retention_pagination_and_gap_heavy_windows(self) -> None:
        result = normalize_ticks(
            [
                {
                    "source": "collector",
                    "symbol": "BTCUSDC",
                    "trade_id": "1",
                    "event_time_utc": datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc),
                    "price": "100",
                    "quantity": "1",
                },
                {
                    "source": "collector",
                    "symbol": "BTCUSDC",
                    "trade_id": "2",
                    "event_time_utc": datetime(2026, 3, 23, 0, 2, 0, tzinfo=timezone.utc),
                    "price": "101",
                    "quantity": "1.5",
                },
                {
                    "source": "collector",
                    "symbol": "BTCUSDC",
                    "trade_id": "3",
                    "event_time_utc": datetime(2026, 3, 23, 0, 4, 0, tzinfo=timezone.utc),
                    "price": "102",
                    "quantity": "2",
                },
            ],
            window_from=datetime(2026, 3, 23, 0, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 0, 5, 0, tzinfo=timezone.utc),
            gap_threshold=timedelta(seconds=30),
            retention_floor=datetime(2026, 3, 23, 0, 1, 0, tzinfo=timezone.utc),
            page_complete=False,
            gap_heavy_ratio=0.5,
        )

        self.assertTrue(result.is_partial)
        self.assertEqual(result.partial_reason, PARTIAL_REASON_RETENTION)
        self.assertEqual(
            result.partial_reasons,
            (
                PARTIAL_REASON_RETENTION,
                PARTIAL_REASON_PAGINATION,
                PARTIAL_REASON_GAP_HEAVY,
            ),
        )
        self.assertEqual(result.gap_count, 2)


if __name__ == "__main__":
    unittest.main()
