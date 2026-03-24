from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from Maffi.runtime import decide, deterministic_replay, maffi_output_to_dict, validate_payload
from Maffi.runtime.enums import Decision


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "payload_example_ok.json"


class SuiteFailure(RuntimeError):
    pass


def load_base_payload() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def run_scenarios() -> list[dict[str, Any]]:
    base = load_base_payload()

    scenarios: list[tuple[str, dict[str, Any], Decision, bool]] = []

    healthy_long = dict(base)
    healthy_long["long_score"] = 78.0
    healthy_long["short_score"] = 31.0
    healthy_long["reject_score"] = 10.0
    healthy_long["confidence_hint"] = 0.79
    scenarios.append(("healthy_long", healthy_long, Decision.LONG, True))

    healthy_short = dict(base)
    healthy_short["long_score"] = 35.0
    healthy_short["short_score"] = 74.0
    healthy_short["reject_score"] = 10.0
    healthy_short["confidence_hint"] = 0.74
    scenarios.append(("healthy_short", healthy_short, Decision.SHORT, True))

    weak_confidence = dict(base)
    weak_confidence["confidence_hint"] = 0.33
    scenarios.append(("weak_confidence", weak_confidence, Decision.REJECT, True))

    chaotic_market = dict(base)
    chaotic_market["input_quality_status"] = "degraded"
    chaotic_market["reject_score"] = 63.0
    chaotic_market["confidence_hint"] = 0.58
    scenarios.append(("chaotic_market", chaotic_market, Decision.REJECT, True))

    invalid_payload = dict(base)
    invalid_payload.pop("atr", None)
    scenarios.append(("invalid_payload", invalid_payload, Decision.REJECT, False))

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    for name, payload, expected_decision, expected_validity in scenarios:
        validation = validate_payload(payload)
        decision_output = decide(payload)
        replay_one, replay_two = deterministic_replay(payload)

        replay_equal = maffi_output_to_dict(replay_one) == maffi_output_to_dict(replay_two)
        decision_match = decision_output.decision == expected_decision
        validity_match = validation.is_valid == expected_validity

        passed = replay_equal and decision_match and validity_match
        if not passed:
            failures.append(
                f"{name}: expected decision={expected_decision.value}, valid={expected_validity}; "
                f"got decision={decision_output.decision.value}, valid={validation.is_valid}, replay_equal={replay_equal}"
            )

        results.append(
            {
                "scenario": name,
                "passed": passed,
                "expected": {
                    "decision": expected_decision.value,
                    "is_valid": expected_validity,
                },
                "actual": {
                    "decision": decision_output.decision.value,
                    "is_valid": validation.is_valid,
                    "reject_reason": decision_output.reject_reason,
                    "confidence": decision_output.confidence,
                    "replay_equal": replay_equal,
                },
                "validation": {
                    "errors": [asdict(err) for err in validation.errors],
                    "warnings": [asdict(w) for w in validation.warnings],
                },
            }
        )

    if failures:
        raise SuiteFailure("\n".join(failures))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Maffi acceptance smoke suite")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    try:
        results = run_scenarios()
    except SuiteFailure as exc:
        print("ACCEPTANCE_SUITE_FAILED")
        print(exc)
        return 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("ACCEPTANCE_SUITE_OK")
        for row in results:
            print(f"- {row['scenario']}: decision={row['actual']['decision']}, valid={row['actual']['is_valid']}, replay={row['actual']['replay_equal']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
