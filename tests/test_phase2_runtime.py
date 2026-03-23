from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from TRADING_ALGOS.machine_registry import MACHINE_REGISTRY, get_machine_spec
from TRADING_ALGOS.machines import execute_rsi_macd_machine, execute_volume_machine
from TRADING_ALGOS.runtime_contract import FAILURE_MODE_MATRIX, STATUS_ERROR, STATUS_PARTIAL, STATUS_READY


class Phase2RuntimeTests(unittest.TestCase):
    def test_machine_registry_contains_all_12_machines(self) -> None:
        self.assertEqual(len(MACHINE_REGISTRY), 12)
        self.assertEqual(get_machine_spec("RSI_MACD", "1m").machine_id, "rsi_macd_1m")
        self.assertEqual(get_machine_spec("ELLIOTT", "60m").warmup.minimum_valid_candles, 60)

    def test_rsi_machine_returns_ready_response_with_features(self) -> None:
        request = self._request(strategy="RSI_MACD", timeframe="1m", agent_id="rsi_macd_1m")
        response = execute_rsi_macd_machine(request, self._ticks(35), gap_threshold=timedelta(minutes=1))

        self.assertEqual(response["status"], STATUS_READY)
        self.assertFalse(response["meta"]["is_partial"])
        self.assertIn("rsi_value", response["features"])
        self.assertIn(response["summary"]["confidence"], {"low", "medium", "high"})

    def test_volume_machine_returns_partial_on_pagination_drift(self) -> None:
        request = self._request(strategy="VOLUME", timeframe="1m", agent_id="volume_1m")
        response = execute_volume_machine(
            request,
            self._ticks(25),
            gap_threshold=timedelta(minutes=1),
            page_complete=False,
        )

        self.assertEqual(response["status"], STATUS_PARTIAL)
        self.assertTrue(response["meta"]["is_partial"])
        self.assertEqual(response["meta"]["partial_reason"], "pagination_truncation")
        self.assertTrue(any(error["code"] == "PAGINATION_DRIFT" for error in response["errors"]))

    def test_machine_returns_error_on_empty_window(self) -> None:
        request = self._request(strategy="RSI_MACD", timeframe="1m", agent_id="rsi_macd_1m")
        response = execute_rsi_macd_machine(request, [], gap_threshold=timedelta(minutes=1))

        self.assertEqual(response["status"], STATUS_ERROR)
        self.assertEqual(response["features"], {})
        self.assertTrue(any(error["code"] == "EMPTY_WINDOW" for error in response["errors"]))

    def test_failure_mode_matrix_is_defined_for_every_machine(self) -> None:
        self.assertEqual(set(FAILURE_MODE_MATRIX), set(MACHINE_REGISTRY))
        self.assertTrue(any(mode.code == "INSUFFICIENT_WARMUP" for mode in FAILURE_MODE_MATRIX["rsi_macd_1m"]))

    @staticmethod
    def _request(*, strategy: str, timeframe: str, agent_id: str) -> dict[str, object]:
        return {
            "request_id": f"req-{strategy}-{timeframe}",
            "agent_id": agent_id,
            "strategy": strategy,
            "timeframe": timeframe,
            "symbol": "BTCUSDC",
            "source": "Data_collector",
            "requested_at": "2026-03-23T10:15:00Z",
            "input_window": {
                "from": "2026-03-23T09:00:00Z",
                "to": "2026-03-23T09:35:00Z",
            },
            "response_contract_version": "v1",
            "source_contract_version": "tick-source-v1",
            "options": {
                "strict_mode": False,
                "include_incomplete_candle": False,
            },
        }

    @staticmethod
    def _ticks(count: int) -> list[dict[str, object]]:
        start = datetime(2026, 3, 23, 9, 0, 10, tzinfo=timezone.utc)
        ticks: list[dict[str, object]] = []
        price = Decimal("100")
        for index in range(count):
            ticks.append(
                {
                    "source": "collector",
                    "symbol": "BTCUSDC",
                    "trade_id": str(index),
                    "event_time_utc": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
                    "price": str(price + Decimal(index)),
                    "quantity": "1",
                    "side": "buy" if index % 2 == 0 else "sell",
                }
            )
        return ticks


if __name__ == "__main__":
    unittest.main()
