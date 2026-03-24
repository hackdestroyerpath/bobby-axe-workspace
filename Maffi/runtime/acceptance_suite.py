from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from Maffi.runtime import decide, deterministic_replay, maffi_output_to_dict, run_trigger, validate_payload
from Maffi.runtime.enums import Decision, QualityStatus
from Maffi.runtime.models import AlgoPayload, FinalNormalizedResponse, TriggerInput
from Maffi.runtime.payload_builder import build_llm_algo_payload
from Maffi.runtime.preprocessing import extract_preprocessing_features
from tests.fixtures.maffi_preprocessing_fixtures import sparse_ticks


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "payload_example_ok.json"

REQUIRED_FINAL_FIELDS = (
    "status",
    "ticker",
    "timeframe",
    "direction",
    "model_id",
    "prompt_version",
    "validator_summary",
    "trace",
)


class SuiteFailure(RuntimeError):
    pass


def load_base_payload() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_trigger() -> TriggerInput:
    return TriggerInput(
        ticker="BTCUSDC",
        timeframe="1m",
        request_ts_utc="2026-03-24T10:00:00Z",
        direction="long",
    )


def _build_algo_payload() -> AlgoPayload:
    preprocessing_result = extract_preprocessing_features(sparse_ticks())
    return build_llm_algo_payload(
        symbol="BTCUSDC",
        window_from=datetime(2026, 3, 23, 0, 0, tzinfo=timezone.utc),
        window_to=datetime(2026, 3, 23, 1, 0, tzinfo=timezone.utc),
        quality=QualityStatus.OK,
        last_price=101.0,
        support_level=99.0,
        resistance_level=103.0,
        atr=1.0,
        coverage_ratio=0.95,
        reasons=[],
        preprocessing_result=preprocessing_result,
    )


def _queue_transport(responses: list[str]) -> Callable[[dict[str, Any]], str]:
    queue = list(responses)

    def transport(_request: dict[str, Any]) -> str:
        if not queue:
            raise RuntimeError("transport queue exhausted")
        return queue.pop(0)

    return transport


def _check_final_response(
    *,
    scenario: str,
    response: FinalNormalizedResponse,
    expected_status: str,
    expected_ticker: str,
    expected_timeframe: str,
    expected_direction: str,
    expect_fallback_trace: bool,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if response.status != expected_status:
        errors.append(f"status expected={expected_status} actual={response.status}")
    if response.ticker != expected_ticker:
        errors.append(f"ticker expected={expected_ticker} actual={response.ticker}")
    if response.timeframe != expected_timeframe:
        errors.append(f"timeframe expected={expected_timeframe} actual={response.timeframe}")
    if response.direction != expected_direction:
        errors.append(f"direction expected={expected_direction} actual={response.direction}")

    for field in REQUIRED_FINAL_FIELDS:
        value = getattr(response, field)
        if value is None:
            errors.append(f"{field} must be set")

    if not isinstance(response.validator_summary, dict) or not response.validator_summary:
        errors.append("validator_summary must be a non-empty dict")
    else:
        for summary_key in ("total_checks", "failed_checks", "warning_checks"):
            if summary_key not in response.validator_summary:
                errors.append(f"validator_summary missing key={summary_key}")

    if not isinstance(response.trace, dict):
        errors.append("trace must be a dict")
    else:
        for trace_key in ("validator", "route", "raw", "fallback"):
            if trace_key not in response.trace:
                errors.append(f"trace missing key={trace_key}")

        fallback_trace = response.trace.get("fallback")
        if expect_fallback_trace and fallback_trace is None:
            errors.append("fallback trace must be present")
        if not expect_fallback_trace and fallback_trace is not None:
            errors.append("fallback trace must be absent")

    passed = not errors
    if not passed:
        errors = [f"{scenario}: {error}" for error in errors]
    return passed, errors


def run_llm_flow_primary() -> dict[str, Any]:
    trigger = _build_trigger()
    payload = _build_algo_payload()

    happy_transport = _queue_transport(
        [
            json.dumps(
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
        ]
    )
    fallback_transport = _queue_transport(
        [
            json.dumps(
                {
                    "ticker": "BTCUSDC",
                    "timeframe": "1m",
                    "direction": "short",
                    "tp": 102.0,
                    "sl": 99.0,
                    "grids": 8,
                    "price_up": 101.5,
                    "price_down": 100.2,
                    "conclusion": "direction mismatch for fallback",
                }
            )
        ]
    )
    reject_transport = _queue_transport(["not-json", "still-not-json"])

    scenarios = [
        (
            "llm_happy_path",
            run_trigger(trigger, algo_payload=payload, transport=happy_transport),
            "ok",
            False,
        ),
        (
            "llm_fallback_path",
            run_trigger(trigger, algo_payload=payload, transport=fallback_transport),
            "fallback",
            True,
        ),
        (
            "llm_reject_path",
            run_trigger(trigger, algo_payload=payload, transport=reject_transport),
            "reject",
            True,
        ),
    ]

    failures: list[str] = []
    rows: list[dict[str, Any]] = []
    for scenario, response, expected_status, expect_fallback_trace in scenarios:
        passed, errors = _check_final_response(
            scenario=scenario,
            response=response,
            expected_status=expected_status,
            expected_ticker="BTCUSDC",
            expected_timeframe="1m",
            expected_direction="long",
            expect_fallback_trace=expect_fallback_trace,
        )
        failures.extend(errors)
        rows.append(
            {
                "scenario": scenario,
                "passed": passed,
                "expected": {
                    "status": expected_status,
                    "ticker": "BTCUSDC",
                    "timeframe": "1m",
                    "direction": "long",
                    "required_fields": REQUIRED_FINAL_FIELDS,
                },
                "actual": {
                    "status": response.status,
                    "ticker": response.ticker,
                    "timeframe": response.timeframe,
                    "direction": response.direction,
                    "model_id": response.model_id,
                    "prompt_version": response.prompt_version,
                    "validator_summary": response.validator_summary,
                    "trace": response.trace,
                },
            }
        )

    if failures:
        raise SuiteFailure("\n".join(failures))

    return {
        "primary": True,
        "scenarios": rows,
    }


def run_legacy_compatibility_smoke() -> dict[str, Any]:
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

    for name, payload, expected_decision, expected_validity in scenarios:
        validation = validate_payload(payload)
        decision_output = decide(payload)
        replay_one, replay_two = deterministic_replay(payload)

        replay_equal = maffi_output_to_dict(replay_one) == maffi_output_to_dict(replay_two)
        decision_match = decision_output.decision == expected_decision
        validity_match = validation.is_valid == expected_validity

        passed = replay_equal and decision_match and validity_match

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

    return {
        "primary": False,
        "optional": True,
        "scenarios": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Maffi acceptance smoke suite")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "--with-legacy",
        action="store_true",
        help="Run optional legacy compatibility smoke (decide + deterministic_replay)",
    )
    args = parser.parse_args()

    try:
        llm_flow = run_llm_flow_primary()
    except SuiteFailure as exc:
        print("ACCEPTANCE_SUITE_FAILED")
        print(exc)
        return 1

    legacy_compat = {
        "primary": False,
        "optional": True,
        "skipped": not args.with_legacy,
        "scenarios": [],
    }
    if args.with_legacy:
        legacy_compat = run_legacy_compatibility_smoke()

    report = {
        "llm_flow": llm_flow,
        "legacy_compat": legacy_compat,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("ACCEPTANCE_SUITE_OK")
        print("[llm_flow]")
        for row in llm_flow["scenarios"]:
            actual = row["actual"]
            print(
                f"- {row['scenario']}: status={actual['status']}, ticker={actual['ticker']}, "
                f"timeframe={actual['timeframe']}, direction={actual['direction']}"
            )

        print("[legacy_compat]")
        if legacy_compat.get("skipped"):
            print("- skipped (run with --with-legacy)")
        else:
            for row in legacy_compat["scenarios"]:
                print(
                    f"- {row['scenario']}: decision={row['actual']['decision']}, "
                    f"valid={row['actual']['is_valid']}, replay={row['actual']['replay_equal']}"
                )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
