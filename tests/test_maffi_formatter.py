from __future__ import annotations

import json
import unittest

from Maffi.runtime import decide, maffi_output_to_dict, maffi_output_to_json


class MaffiFormatterTests(unittest.TestCase):
    def test_output_envelope_shape(self) -> None:
        payload = _base_payload()

        output = decide(payload)
        serialized = maffi_output_to_dict(output)

        expected_keys = [
            "schema_version",
            "generated_at_utc",
            "symbol",
            "decision",
            "confidence",
            "selected_entry",
            "tp",
            "sl",
            "input_quality_status",
            "reject_reason",
            "rationale",
            "grid_upper_price",
            "grid_lower_price",
            "grid_count",
            "grid_step",
            "efficiency_score",
            "selected_candidate_id",
            "validation_summary",
            "decision_summary",
            "decision_trace",
        ]
        self.assertEqual(list(serialized.keys()), expected_keys)
        self.assertIsInstance(serialized["rationale"], list)
        self.assertIsInstance(serialized["validation_summary"], dict)
        self.assertIsInstance(serialized["decision_summary"], dict)
        self.assertIsInstance(serialized["decision_trace"], dict)

    def test_stable_top_level_keys_and_trace_normalization(self) -> None:
        payload = _base_payload()

        output = decide(payload)
        first = maffi_output_to_dict(output)
        second = maffi_output_to_dict(output)

        self.assertEqual(first, second)
        self.assertEqual(list(first.keys()), list(second.keys()))
        self.assertEqual(list(first["decision_trace"].keys()), ["selection", "steps"])

    def test_json_serialization_round_trip(self) -> None:
        payload = _base_payload()

        output = decide(payload)
        encoded = maffi_output_to_json(output)
        decoded = json.loads(encoded)

        self.assertEqual(decoded, maffi_output_to_dict(output))


def _base_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "maffi-v1",
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
