from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from Maffi.runtime import decide, maffi_output_to_dict


class MaffiContractV1Tests(unittest.TestCase):
    def test_long_short_reject_outputs_follow_contract_v1_shape(self) -> None:
        outputs = [
            maffi_output_to_dict(decide(_base_payload(long_score=80.0, short_score=35.0, reject_score=10.0))),
            maffi_output_to_dict(decide(_base_payload(long_score=30.0, short_score=78.0, reject_score=10.0))),
            maffi_output_to_dict(decide(_base_payload(input_quality_status="bad", reject_score=35.0))),
        ]

        for payload in outputs:
            _assert_contract_v1_shape(payload)

    def test_final_output_fixture_matches_contract_v1_shape(self) -> None:
        fixture_path = Path("Maffi/examples/final_output_v1.json")
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

        _assert_contract_v1_shape(fixture)

    def test_contract_snapshot_payload_and_output_enforce_v1_schema_version(self) -> None:
        snapshot_path = Path("Maffi/examples/contract_snapshot_v1.json")
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

        expected_version = snapshot["schema_version_assertion"]
        payload = snapshot["payload"]
        expected_output = snapshot["output"]

        assert payload["schema_version"] == expected_version
        assert expected_output["schema_version"] == expected_version

        actual_output = maffi_output_to_dict(decide(payload, generated_at_override=expected_output["generated_at_utc"]))
        assert actual_output == expected_output



def _assert_contract_v1_shape(data: dict[str, Any]) -> None:
    for field in ("validation_summary", "decision_summary", "decision_trace"):
        assert field in data

    validation = data["validation_summary"]
    assert isinstance(validation, dict)
    for field in ("counts", "errors", "warnings", "degrade", "top_reasons"):
        assert field in validation

    counts = validation["counts"]
    for field in ("total_checks", "passed", "failed", "warnings"):
        assert isinstance(counts[field], int)
        assert counts[field] >= 0

    degrade = validation["degrade"]
    assert isinstance(degrade["is_degraded"], bool)
    assert isinstance(degrade["degrade_score"], (int, float))
    assert 0 <= float(degrade["degrade_score"]) <= 1

    decision_summary = data["decision_summary"]
    assert decision_summary["direction"] in {"long", "short", "reject"}
    assert isinstance(decision_summary["selected_candidate_id"], str)
    assert len(decision_summary["selected_candidate_id"]) >= 1

    digest = decision_summary["tp_sl_logic_digest"]
    assert digest["mode"] in {"atr_buffered", "structure_based", "mixed", "none"}
    assert isinstance(digest["tp_basis"], str)
    assert isinstance(digest["sl_basis"], str)
    assert isinstance(digest["rr_estimate"], (int, float))
    assert float(digest["rr_estimate"]) >= 0

    steps = data["decision_trace"]["steps"]
    assert isinstance(steps, list)
    assert len(steps) == 6
    assert [step["name"] for step in steps] == ["gate", "direction", "range", "grid_count", "tp_sl", "confidence"]
    for step in steps:
        assert step["status"] in {"pass", "fail", "skip"}
        assert isinstance(step["reason"], str)
        assert len(step["reason"]) >= 1


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
