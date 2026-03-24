from __future__ import annotations

import copy
import unittest

from Maffi.runtime import decide, deterministic_replay, validate_payload
from Maffi.runtime.enums import Decision


class MaffiDecisionEngineTests(unittest.TestCase):
    def test_validator_rejects_missing_required_field(self) -> None:
        payload = _base_payload()
        del payload["atr"]

        result = validate_payload(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.field == "atr" for issue in result.errors))

    def test_good_long_scenario(self) -> None:
        payload = _base_payload(long_score=80.0, short_score=35.0, reject_score=10.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.LONG)
        self.assertIsNone(output.reject_reason)
        self.assertGreater(output.confidence, 0)
        self.assertIsNotNone(output.selected_entry)
        self.assertIsNotNone(output.tp)
        self.assertIsNotNone(output.sl)

    def test_good_short_scenario(self) -> None:
        payload = _base_payload(long_score=32.0, short_score=77.0, reject_score=15.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.SHORT)
        self.assertIsNone(output.reject_reason)

    def test_bad_data_hard_reject(self) -> None:
        payload = _base_payload(input_quality_status="bad", reject_score=35.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.REJECT)
        self.assertEqual(output.reject_reason, "input_quality_bad")

    def test_chaotic_high_reject_score_rejects(self) -> None:
        payload = _base_payload(market_regime="chaotic", reject_score=65.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.REJECT)
        self.assertEqual(output.reject_reason, "reject_score_high")

    def test_degraded_input_remains_usable_with_penalty(self) -> None:
        payload = _base_payload(input_quality_status="degraded", confidence_hint=0.8)

        output = decide(payload)

        self.assertIn(output.decision, {Decision.LONG, Decision.SHORT})
        self.assertAlmostEqual(output.confidence, 0.6, places=6)

    def test_deterministic_replay_same_payload_same_output_payload_fields(self) -> None:
        payload = _base_payload()

        first, second = deterministic_replay(copy.deepcopy(payload))

        self.assertEqual(first, second)


def _base_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "maffi-v0.1",
        "symbol": "BTCUSDC",
        "generated_at_utc": "2026-03-24T12:00:00Z",
        "source": "Data_collector",
        "input_quality_status": "ok",
        "market_regime": "trend",
        "volatility_regime": "normal",
        "dominant_side": "buyers",
        "long_score": 72.0,
        "short_score": 41.0,
        "reject_score": 12.0,
        "confidence_hint": 0.75,
        "entry_candidates": [87210.0, 87240.0, 87290.0],
        "support_level": 86980.0,
        "resistance_level": 87640.0,
        "last_price": 87260.0,
        "atr": 120.0,
        "context": {"fixture": True},
    }
    payload.update(overrides)
    return payload


if __name__ == "__main__":
    unittest.main()
