from __future__ import annotations

from datetime import datetime, timezone
import unittest

from Maffi.runtime.enums import QualityStatus
from Maffi.runtime.llm_router import DEFAULT_MODEL_ID, DEFAULT_ROUTE_NAME, route_llm
from Maffi.runtime.payload_builder import build_llm_algo_payload
from Maffi.runtime.prompt_builder import build_prompt
from Maffi.runtime.preprocessing import extract_preprocessing_features
from tests.fixtures.maffi_preprocessing_fixtures import sparse_ticks


class MaffiLLMRouterTests(unittest.TestCase):
    def _prompt_result(self, ticker: str):
        preprocessing_result = extract_preprocessing_features(sparse_ticks())
        payload = build_llm_algo_payload(
            symbol=ticker,
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
        return build_prompt(payload)

    def test_router_uses_btc_override(self) -> None:
        route = route_llm(self._prompt_result("BTCUSDC"))
        self.assertEqual(route.route_name, "btc-primary")
        self.assertEqual(route.provider, "openai")
        self.assertEqual(route.system_style, "macro-liquid-major")
        self.assertEqual(route.ticker, "BTCUSDC")

    def test_router_falls_back_to_default(self) -> None:
        route = route_llm(self._prompt_result("XRPUSDC"))
        self.assertEqual(route.route_name, DEFAULT_ROUTE_NAME)
        self.assertEqual(route.model_id, DEFAULT_MODEL_ID)
        self.assertEqual(route.system_style, "general-grid")
        self.assertEqual(route.ticker, "XRPUSDC")

    def test_router_preserves_prompt_metadata(self) -> None:
        route = route_llm(self._prompt_result("ETHUSDC"))
        self.assertIn("prompt_version", route.request_meta)
        self.assertIn("candidate_count", route.request_meta)
        self.assertEqual(route.request_meta["ticker"], "ETHUSDC")


if __name__ == "__main__":
    unittest.main()
