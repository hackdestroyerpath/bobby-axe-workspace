from __future__ import annotations

from datetime import datetime, timezone
import unittest

from Maffi.runtime.fallbacks import apply_fallback_policy
from Maffi.runtime.finalize import finalize_response
from Maffi.runtime.llm_router import route_llm
from Maffi.runtime.payload_builder import build_llm_algo_payload
from Maffi.runtime.preprocessing import extract_preprocessing_features
from Maffi.runtime.prompt_builder import build_prompt
from Maffi.runtime.enums import QualityStatus
from Maffi.runtime.models import LLMRawResponse, LLMValidationResult
from tests.fixtures.loader import load_maffi_llm_flow_fixture
from tests.fixtures.maffi_preprocessing_fixtures import sparse_ticks


class MaffiFinalizeTests(unittest.TestCase):
    def _route(self):
        preprocessing = extract_preprocessing_features(sparse_ticks())
        payload = build_llm_algo_payload(
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
            preprocessing_result=preprocessing,
        )
        return route_llm(build_prompt(payload))

    def test_valid_normalize(self) -> None:
        route = self._route()
        valid_payload = load_maffi_llm_flow_fixture("llm_raw_valid.json")
        raw = LLMRawResponse("BTCUSDC", route.model_id, "maffi-prompt-v1", "raw", valid_payload)
        validation = LLMValidationResult(
            is_valid=True,
            normalized_payload=raw.parsed_json,
            summary={"failed_checks": 0},
            trace={"status": "pass"},
        )
        result = finalize_response(validation_result=validation, raw_response=raw, route=route)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.grids, 8)

    def test_nullable_fields_supported(self) -> None:
        route = self._route()
        raw = LLMRawResponse(
            "BTCUSDC",
            route.model_id,
            "maffi-prompt-v1",
            "raw",
            None,
            {"ticker": "BTCUSDC", "timeframe": "1m", "direction": "long"},
        )
        validation = LLMValidationResult(is_valid=False, errors=({"code": "invalid_range"},), summary={}, trace={})
        fallback = apply_fallback_policy(validation, raw)
        result = finalize_response(validation_result=validation, raw_response=raw, route=route, fallback_result=fallback)
        self.assertIsNone(result.tp)
        self.assertIsNone(result.grids)

    def test_fallback_status(self) -> None:
        route = self._route()
        raw = LLMRawResponse(
            "BTCUSDC",
            route.model_id,
            "maffi-prompt-v1",
            "raw",
            None,
            {"ticker": "BTCUSDC", "timeframe": "1m", "direction": "long"},
        )
        validation = LLMValidationResult(is_valid=False, errors=({"code": "invalid_range"},), summary={}, trace={})
        fallback = apply_fallback_policy(validation, raw)
        expected_payload = load_maffi_llm_flow_fixture("fallback_expected.json")["invalid_range"]
        self.assertEqual(fallback.fallback_payload, expected_payload)

        result = finalize_response(validation_result=validation, raw_response=raw, route=route, fallback_result=fallback)
        self.assertEqual(result.status, "fallback")

    def test_model_and_prompt_passthrough(self) -> None:
        route = self._route()
        raw = LLMRawResponse("BTCUSDC", route.model_id, "maffi-prompt-v1", "raw", None, {})
        validation = LLMValidationResult(is_valid=False, errors=({"code": "unknown"},), summary={}, trace={})
        fallback = apply_fallback_policy(validation, raw)
        result = finalize_response(validation_result=validation, raw_response=raw, route=route, fallback_result=fallback)
        self.assertEqual(result.model_id, route.model_id)
        self.assertEqual(result.prompt_version, "maffi-prompt-v1")

    def test_trace_passthrough(self) -> None:
        route = self._route()
        raw = LLMRawResponse("BTCUSDC", route.model_id, "maffi-prompt-v1", "raw", None, {})
        validation = LLMValidationResult(is_valid=False, errors=({"code": "unknown"},), summary={}, trace={"validator": "v"})
        fallback = apply_fallback_policy(validation, raw)
        result = finalize_response(validation_result=validation, raw_response=raw, route=route, fallback_result=fallback)
        self.assertIn("fallback", result.trace)
        self.assertEqual(result.trace["validator"], {"validator": "v"})


if __name__ == "__main__":
    unittest.main()
