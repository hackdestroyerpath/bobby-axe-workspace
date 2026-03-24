from __future__ import annotations

import unittest

from Maffi.runtime.models import LLMRawResponse
from Maffi.runtime.output_validator import validate_llm_output


class MaffiOutputValidatorTests(unittest.TestCase):
    def _validate(self, parsed_json):
        raw_response = LLMRawResponse(
            ticker="BTCUSDC",
            model_id="openai:gpt-4.1",
            prompt_version="maffi-prompt-v1",
            raw_text="raw",
            parsed_json=parsed_json,
            request_meta={"ticker": "BTCUSDC", "timeframe": "1m", "direction": "long"},
        )
        return validate_llm_output(
            raw_response,
            expected_direction="long",
            expected_ticker="BTCUSDC",
            expected_timeframe="1m",
        )

    def test_invalid_json_result_fails(self) -> None:
        raw_response = LLMRawResponse(
            ticker="BTCUSDC",
            model_id="openai:gpt-4.1",
            prompt_version="maffi-prompt-v1",
            raw_text="not-json",
            parsed_json=None,
            request_meta={"ticker": "BTCUSDC", "timeframe": "1m", "direction": "long"},
        )
        result = validate_llm_output(
            raw_response,
            expected_direction="long",
            expected_ticker="BTCUSDC",
            expected_timeframe="1m",
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0]["code"], "json_parse_failed")

    def test_missing_required_field_fails(self) -> None:
        result = self._validate(
            {
                "ticker": "BTCUSDC",
                "timeframe": "1m",
                "direction": "long",
                "tp": 102.0,
                "sl": 99.0,
                "grids": 8,
                "price_up": 101.5,
                "price_down": 100.2,
            }
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0]["code"], "required_field_missing")

    def test_wrong_type_fails(self) -> None:
        result = self._validate(
            {
                "ticker": "BTCUSDC",
                "timeframe": "1m",
                "direction": "long",
                "tp": "102.0",
                "sl": 99.0,
                "grids": 8,
                "price_up": 101.5,
                "price_down": 100.2,
                "conclusion": "ok",
            }
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0]["code"], "invalid_type")

    def test_invalid_range_fails(self) -> None:
        result = self._validate(
            {
                "ticker": "BTCUSDC",
                "timeframe": "1m",
                "direction": "long",
                "tp": 102.0,
                "sl": 99.0,
                "grids": 8,
                "price_up": 100.0,
                "price_down": 101.0,
                "conclusion": "ok",
            }
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0]["code"], "invalid_range")

    def test_wrong_direction_fails(self) -> None:
        result = self._validate(
            {
                "ticker": "BTCUSDC",
                "timeframe": "1m",
                "direction": "short",
                "tp": 102.0,
                "sl": 99.0,
                "grids": 8,
                "price_up": 101.5,
                "price_down": 100.2,
                "conclusion": "ok",
            }
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0]["code"], "direction_mismatch")

    def test_wrong_ticker_or_timeframe_fails(self) -> None:
        result = self._validate(
            {
                "ticker": "ETHUSDC",
                "timeframe": "5m",
                "direction": "long",
                "tp": 102.0,
                "sl": 99.0,
                "grids": 8,
                "price_up": 101.5,
                "price_down": 100.2,
                "conclusion": "ok",
            }
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors[0]["code"], "ticker_mismatch")

    def test_valid_output_passes(self) -> None:
        result = self._validate(
            {
                "ticker": "BTCUSDC",
                "timeframe": "1m",
                "direction": "long",
                "tp": 102.0,
                "sl": 99.0,
                "grids": 8,
                "price_up": 101.5,
                "price_down": 100.2,
                "conclusion": "ok",
            }
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.trace["status"], "pass")
        self.assertEqual(result.summary["failed_checks"], 0)


if __name__ == "__main__":
    unittest.main()
