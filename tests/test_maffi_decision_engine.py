from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from Maffi.runtime import decide, deterministic_replay, score_grid_candidates, validate_payload
from Maffi.runtime.enums import Decision


class MaffiDecisionEngineTests(unittest.TestCase):
    EXPECTED_STEP_NAMES = ["gate", "direction", "range", "grid_count", "tp_sl", "confidence"]

    def test_validator_rejects_missing_required_field(self) -> None:
        payload = _base_payload()
        del payload["atr"]

        result = validate_payload(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.field == "atr" for issue in result.errors))
        self.assertIn("counts", result.trace)
        self.assertEqual(result.trace["counts"]["failed"], len(result.errors))
        self.assertEqual(result.trace["counts"]["warnings"], len(result.warnings))
        self.assertEqual(result.summary.counts.failed, len(result.errors))

    def test_good_long_scenario(self) -> None:
        payload = _base_payload(long_score=80.0, short_score=35.0, reject_score=10.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.LONG)
        self.assertIsNone(output.reject_reason)
        self.assertGreater(output.confidence, 0)
        self.assertIsNotNone(output.selected_entry)
        self.assertIsNotNone(output.tp)
        self.assertIsNotNone(output.sl)
        self.assertEqual(output.decision_summary["direction"], "long")
        self.assertEqual(output.decision_trace["steps"][4]["name"], "tp_sl")
        self._assert_steps_structure_and_order(output.decision_trace["steps"])
        self.assertTrue(all(step["status"] == "pass" for step in output.decision_trace["steps"]))
        self.assertGreaterEqual(float(output.efficiency_score or 0.0), 0.60)
        self.assertIsNotNone(output.selected_candidate_id)

    def test_good_short_scenario(self) -> None:
        payload = _base_payload(long_score=32.0, short_score=77.0, reject_score=15.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.SHORT)
        self.assertIsNone(output.reject_reason)
        self.assertEqual(output.decision_summary["direction"], "short")
        self.assertEqual(output.decision_summary["tp_sl_logic_digest"]["mode"], "mixed")
        self.assertGreaterEqual(float(output.efficiency_score or 0.0), 0.60)

    def test_bad_data_hard_reject(self) -> None:
        payload = _base_payload(input_quality_status="bad", reject_score=35.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.REJECT)
        self.assertEqual(output.reject_reason, "input_quality_bad")
        self.assertEqual(output.decision_summary["direction"], "reject")
        self.assertEqual(output.decision_summary["tp_sl_logic_digest"]["mode"], "none")

    def test_chaotic_high_reject_score_rejects(self) -> None:
        payload = _base_payload(market_regime="chaotic", reject_score=65.0)

        output = decide(payload)

        self.assertEqual(output.decision, Decision.REJECT)
        self.assertEqual(output.reject_reason, "reject_score_high")
        self._assert_steps_structure_and_order(output.decision_trace["steps"])
        self.assertEqual(output.decision_trace["steps"][0]["status"], "fail")
        self.assertTrue(all(step["status"] in {"fail", "skip"} for step in output.decision_trace["steps"]))
        self.assertTrue(all(isinstance(step["reason"], str) and step["reason"] for step in output.decision_trace["steps"]))

    def test_degraded_input_remains_usable_with_penalty(self) -> None:
        payload = _base_payload(input_quality_status="degraded", confidence_hint=0.8)

        output = decide(payload)

        self.assertIn(output.decision, {Decision.LONG, Decision.SHORT})
        self.assertAlmostEqual(output.confidence, 0.6, places=6)
        self.assertTrue(output.validation_summary["degrade"]["is_degraded"])
        self.assertGreaterEqual(output.validation_summary["degrade"]["degrade_score"], 0.5)
        self.assertTrue(
            any(reason["severity"] == "degrade" for reason in output.validation_summary["top_reasons"]),
        )

    def test_validator_trace_has_severity_distribution_contract(self) -> None:
        payload = _base_payload(input_quality_status="degraded")
        payload["last_price"] = payload["resistance_level"] + 1.0  # type: ignore[operator]
        payload["atr"] = 0.0

        result = validate_payload(payload)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.trace["counts"]["failed"], 1)
        self.assertEqual(result.trace["counts"]["warnings"], 1)
        self.assertEqual(result.trace["severity_distribution"]["error"], 1)
        self.assertEqual(result.trace["severity_distribution"]["warning"], 1)
        self.assertEqual(result.trace["severity_distribution"]["degrade"], 1)
        self.assertTrue(result.trace["is_degraded"])
        self.assertGreater(result.trace["degrade_score"], 0.0)
        self.assertTrue(any(reason["severity"] == "degrade" for reason in result.trace["reasons"]))

    def test_deterministic_replay_same_payload_same_output_payload_fields(self) -> None:
        payload = _base_payload()

        first, second = deterministic_replay(copy.deepcopy(payload))

        self.assertEqual(first, second)

    def test_efficiency_score_floor_from_canonical_payload_fixture(self) -> None:
        payload = json.loads(Path("Maffi/payload_example_ok.json").read_text(encoding="utf-8"))

        output = decide(payload)

        self.assertIn(output.decision, {Decision.LONG, Decision.SHORT})
        self.assertIsNotNone(output.efficiency_score)
        self.assertGreaterEqual(float(output.efficiency_score), 0.60)
        self.assertEqual(
            output.decision_trace["selection"]["selected_candidate_id"],
            output.selected_candidate_id,
        )

    def test_grid_scoring_ranking_is_deterministic_against_fixture(self) -> None:
        fixture = json.loads(Path("Maffi/examples/grid_candidates_scored.json").read_text(encoding="utf-8"))
        payload = fixture["payload"]

        first = score_grid_candidates(payload, Decision.LONG)
        second = score_grid_candidates(payload, Decision.LONG)

        first_ranked = [candidate.candidate_id for candidate in first.ranked]
        second_ranked = [candidate.candidate_id for candidate in second.ranked]
        self.assertEqual(first_ranked, second_ranked)
        self.assertEqual(first_ranked, fixture["expected_ranked_candidate_ids"])
        self.assertEqual(first.selected.candidate_id if first.selected else None, fixture["expected_selected_candidate_id"])
        self.assertGreaterEqual(first.selected.efficiency_score if first.selected else 0.0, 0.60)

    def _assert_steps_structure_and_order(self, steps: list[dict[str, object]]) -> None:
        self.assertEqual(len(steps), 6)
        self.assertEqual([step["name"] for step in steps], self.EXPECTED_STEP_NAMES)
        for step in steps:
            self.assertIn("name", step)
            self.assertIn("status", step)
            self.assertIn("reason", step)
            self.assertIn("inputs", step)
            self.assertIn("outputs", step)
            self.assertIn("metrics", step)
            self.assertIn("warnings", step)
            self.assertIsInstance(step["reason"], str)
            self.assertTrue(step["reason"])


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
