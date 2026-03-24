from __future__ import annotations

from datetime import datetime, timezone
import unittest

from Maffi.runtime.enums import QualityStatus
from Maffi.runtime.llm_client import build_llm_request, call_llm
from Maffi.runtime.llm_router import route_llm
from Maffi.runtime.payload_builder import build_llm_algo_payload
from Maffi.runtime.prompt_builder import build_prompt
from Maffi.runtime.preprocessing import extract_preprocessing_features
from tests.fixtures.maffi_preprocessing_fixtures import sparse_ticks


class MaffiLLMClientTests(unittest.TestCase):
    def _prompt_and_route(self):
        preprocessing_result = extract_preprocessing_features(sparse_ticks())
        payload = build_llm_algo_payload(
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
        prompt_result = build_prompt(payload)
        route = route_llm(prompt_result)
        return prompt_result, route

    def test_build_llm_request_contains_expected_fields(self) -> None:
        prompt_result, route = self._prompt_and_route()
        request = build_llm_request(prompt_result, route)
        self.assertEqual(request["provider"], route.provider)
        self.assertEqual(request["model_id"], route.model_id)
        self.assertEqual(request["prompt_version"], prompt_result.prompt_version)
        self.assertIn("system_prompt", request)
        self.assertIn("user_prompt", request)

    def test_call_llm_parses_valid_json(self) -> None:
        prompt_result, route = self._prompt_and_route()

        def transport(_: dict[str, object]) -> str:
            return '{"ticker":"BTCUSDC","timeframe":"1m","direction":"long","tp":102.0,"sl":99.0,"grids":8,"price_up":101.5,"price_down":100.2,"conclusion":"ok"}'

        response = call_llm(prompt_result, route, transport=transport)
        self.assertEqual(response.ticker, "BTCUSDC")
        self.assertEqual(response.model_id, route.model_id)
        self.assertEqual(response.prompt_version, prompt_result.prompt_version)
        self.assertIsNotNone(response.parsed_json)
        self.assertEqual(response.parsed_json["ticker"], "BTCUSDC")

    def test_call_llm_handles_invalid_json(self) -> None:
        prompt_result, route = self._prompt_and_route()

        def transport(_: dict[str, object]) -> str:
            return 'not-json'

        response = call_llm(prompt_result, route, transport=transport)
        self.assertIsNone(response.parsed_json)
        self.assertEqual(response.raw_text, 'not-json')

    def test_call_llm_preserves_request_meta(self) -> None:
        prompt_result, route = self._prompt_and_route()

        def transport(_: dict[str, object]) -> str:
            return '{"ticker":"BTCUSDC"}'

        response = call_llm(prompt_result, route, transport=transport)
        self.assertEqual(response.request_meta["ticker"], "BTCUSDC")
        self.assertEqual(response.request_meta["prompt_version"], prompt_result.prompt_version)


if __name__ == "__main__":
    unittest.main()
