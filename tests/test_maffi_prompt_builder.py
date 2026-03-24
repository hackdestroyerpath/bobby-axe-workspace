from __future__ import annotations

from datetime import datetime, timezone
import unittest

from Maffi.runtime.enums import QualityStatus
from Maffi.runtime.payload_builder import build_llm_algo_payload
from Maffi.runtime.prompt_builder import PROMPT_VERSION, build_prompt, serialize_algo_payload_for_prompt
from Maffi.runtime.preprocessing import extract_preprocessing_features
from tests.fixtures.maffi_preprocessing_fixtures import sparse_ticks


class MaffiPromptBuilderTests(unittest.TestCase):
    def test_serialize_algo_payload_for_prompt_reduces_candidates(self) -> None:
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

        serialized = serialize_algo_payload_for_prompt(payload)
        self.assertIn("request_context", serialized)
        self.assertIn("grid_candidates", serialized)
        self.assertLessEqual(len(serialized["grid_candidates"]["candidates"]), 3)
        candidate = serialized["grid_candidates"]["candidates"][0]
        self.assertIn("candidate_id", candidate)
        self.assertIn("efficiency_score", candidate)
        self.assertNotIn("range_utilization_score", candidate)

    def test_build_prompt_returns_structured_result(self) -> None:
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

        result = build_prompt(payload)
        self.assertEqual(result.prompt_version, PROMPT_VERSION)
        self.assertIn("grid-generation assistant", result.system_prompt)
        self.assertIn("ticker=BTCUSDC", result.user_prompt)
        self.assertIn("direction=long", result.user_prompt)
        self.assertIn("Return only one valid JSON object", result.user_prompt)
        self.assertIn("ticker", result.user_prompt)
        self.assertEqual(result.request_meta["ticker"], "BTCUSDC")
        self.assertEqual(result.request_meta["direction"], "long")
        self.assertEqual(result.prompt_meta["section_count"], 5)
        self.assertGreaterEqual(result.prompt_meta["candidate_count"], 1)
        self.assertIn("request_context", result.payload_for_prompt)
        self.assertIn(result.system_prompt, result.combined_prompt)
        self.assertIn(result.user_prompt, result.combined_prompt)


if __name__ == "__main__":
    unittest.main()
