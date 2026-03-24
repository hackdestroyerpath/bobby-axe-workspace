from __future__ import annotations

import unittest

from Maffi.runtime.fallbacks import apply_fallback_policy
from Maffi.runtime.models import LLMRawResponse, LLMValidationResult


class MaffiFallbacksTests(unittest.TestCase):
    def _raw(self) -> LLMRawResponse:
        return LLMRawResponse(
            ticker="BTCUSDC",
            model_id="openai:gpt-4.1",
            prompt_version="maffi-prompt-v1",
            raw_text="{}",
            parsed_json=None,
            request_meta={"ticker": "BTCUSDC", "timeframe": "1m", "direction": "long"},
        )

    def _validation(self, code: str) -> LLMValidationResult:
        return LLMValidationResult(
            is_valid=False,
            errors=({"code": code, "field": "x", "message": "bad"},),
            normalized_payload=None,
            summary={"failed_checks": 1},
            trace={"status": "fail"},
        )

    def test_broken_json_recommends_retry(self) -> None:
        result = apply_fallback_policy(self._validation("json_parse_failed"), self._raw(), retry_attempt=0, max_retry_count=1)
        self.assertEqual(result.action, "retry")
        self.assertTrue(result.retry_recommended)

    def test_missing_field_recommends_retry(self) -> None:
        result = apply_fallback_policy(self._validation("required_field_missing"), self._raw(), retry_attempt=0, max_retry_count=1)
        self.assertEqual(result.action, "retry")

    def test_invalid_range_falls_back(self) -> None:
        result = apply_fallback_policy(self._validation("invalid_range"), self._raw(), retry_attempt=0, max_retry_count=1)
        self.assertEqual(result.action, "fallback")
        self.assertEqual(result.reason, "invalid_range")

    def test_wrong_direction_falls_back(self) -> None:
        result = apply_fallback_policy(self._validation("direction_mismatch"), self._raw(), retry_attempt=0, max_retry_count=1)
        self.assertEqual(result.action, "fallback")

    def test_hard_reject_for_unknown_code(self) -> None:
        result = apply_fallback_policy(self._validation("something_new"), self._raw(), retry_attempt=0, max_retry_count=1)
        self.assertEqual(result.action, "reject")

    def test_fallback_envelope_shape(self) -> None:
        result = apply_fallback_policy(self._validation("invalid_tp_sl"), self._raw(), retry_attempt=0, max_retry_count=1)
        self.assertEqual(
            set(result.fallback_payload.keys()),
            {"ticker", "timeframe", "direction", "tp", "sl", "grids", "price_up", "price_down", "conclusion"},
        )


if __name__ == "__main__":
    unittest.main()
