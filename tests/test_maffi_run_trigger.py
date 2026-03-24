from __future__ import annotations

from datetime import datetime, timezone
import json
import unittest

from Maffi.runtime.enums import QualityStatus
from Maffi.runtime.models import TriggerInput
from Maffi.runtime.payload_builder import build_llm_algo_payload
from Maffi.runtime.preprocessing import extract_preprocessing_features
from Maffi.runtime.run_trigger import run_trigger
from tests.fixtures.loader import load_maffi_llm_flow_fixture
from tests.fixtures.maffi_preprocessing_fixtures import sparse_ticks


class _TransportQueue:
    def __init__(self, responses: list[str]):
        self._responses = responses

    def __call__(self, _request):
        if not self._responses:
            raise RuntimeError("transport queue exhausted")
        return self._responses.pop(0)


class MaffiRunTriggerTests(unittest.TestCase):
    def _trigger(self) -> TriggerInput:
        return TriggerInput(
            ticker="BTCUSDC",
            timeframe="1m",
            request_ts_utc="2026-03-24T10:00:00Z",
            direction="long",
        )

    def _payload(self):
        preprocessing_result = extract_preprocessing_features(sparse_ticks())
        return build_llm_algo_payload(
            symbol="BTCUSDC",
            window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
            window_to=datetime(2026, 3, 23, 1, 0, tzinfo=timezone.utc),
            quality=QualityStatus.OK,
            last_price=101.0,
            support_level=99.0,
            resistance_level=103.0,
            atr=1.0,
            coverage_ratio=0.95,
            reasons=[],
            preprocessing_result=preprocessing_result,
        )

    def test_happy_path(self) -> None:
        response = load_maffi_llm_flow_fixture("llm_raw_valid.json")
        transport = _TransportQueue([json.dumps(response)])
        result = run_trigger(self._trigger(), algo_payload=self._payload(), transport=transport)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.ticker, "BTCUSDC")

    def test_invalid_output_fallback_path(self) -> None:
        response = load_maffi_llm_flow_fixture("llm_raw_invalid.json")
        transport = _TransportQueue([json.dumps(response)])
        result = run_trigger(self._trigger(), algo_payload=self._payload(), transport=transport)
        self.assertEqual(result.status, "fallback")

    def test_retry_then_success(self) -> None:
        good = load_maffi_llm_flow_fixture("llm_raw_valid.json")
        transport = _TransportQueue(["not-json", json.dumps(good)])
        result = run_trigger(self._trigger(), algo_payload=self._payload(), transport=transport)
        self.assertEqual(result.status, "ok")

    def test_reject_path(self) -> None:
        response = {"foo": "bar"}
        transport = _TransportQueue([json.dumps(response), json.dumps(response)])
        result = run_trigger(self._trigger(), algo_payload=self._payload(), transport=transport)
        self.assertEqual(result.status, "reject")

    def test_trace_propagation(self) -> None:
        transport = _TransportQueue(["not-json", "not-json"])
        result = run_trigger(self._trigger(), algo_payload=self._payload(), transport=transport)
        self.assertIn("validator", result.trace)
        self.assertIn("fallback", result.trace)

    def test_ticker_timeframe_mismatch_regression(self) -> None:
        mismatch = load_maffi_llm_flow_fixture("validator_failures.json")["ticker_timeframe_mismatch"]
        expected = load_maffi_llm_flow_fixture("final_expected.json")["ticker_timeframe_mismatch"]
        expected_fallback_payload = load_maffi_llm_flow_fixture("fallback_expected.json")["ticker_mismatch"]

        transport = _TransportQueue([json.dumps(mismatch)])
        result = run_trigger(self._trigger(), algo_payload=self._payload(), transport=transport)

        self.assertEqual(result.status, expected["status"])
        self.assertEqual(result.trace["validator"], expected["trace"]["validator"])
        normalized_fallback_trace = {
            **result.trace["fallback"],
            "error_codes": list(result.trace["fallback"].get("error_codes", ())),
        }
        self.assertEqual(normalized_fallback_trace, expected["trace"]["fallback"])
        self.assertEqual(
            {
                "ticker": result.ticker,
                "timeframe": result.timeframe,
                "direction": result.direction,
                "tp": result.tp,
                "sl": result.sl,
                "grids": result.grids,
                "price_up": result.price_up,
                "price_down": result.price_down,
                "conclusion": result.conclusion,
            },
            expected_fallback_payload,
        )


if __name__ == "__main__":
    unittest.main()
