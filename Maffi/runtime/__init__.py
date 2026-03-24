from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .decision_engine import _resolve_direction
from .enums import Decision, QualityStatus
from .models import CandidateScore, CandidateSelection, MaffiOutput, ValidationCounts, ValidationIssue, ValidationResult, ValidationSummaryObj

REQUIRED_FIELDS = (
    "schema_version",
    "symbol",
    "generated_at_utc",
    "source",
    "input_quality_status",
    "market_regime",
    "volatility_regime",
    "dominant_side",
    "long_score",
    "short_score",
    "reject_score",
    "confidence_hint",
    "entry_candidates",
    "support_level",
    "resistance_level",
    "last_price",
    "atr",
    "context",
)


def validate_payload(payload: dict[str, Any]) -> ValidationResult:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    reasons: list[dict[str, Any]] = []

    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(ValidationIssue(field=field, code="required", message="field is required"))

    if "atr" in payload and float(payload["atr"]) <= 0:
        errors.append(ValidationIssue(field="atr", code="invalid", message="atr must be positive"))

    if "last_price" in payload and "resistance_level" in payload and float(payload["last_price"]) > float(payload["resistance_level"]):
        warnings.append(ValidationIssue(field="last_price", code="range_warning", message="last_price above resistance", severity="warning"))

    is_degraded = payload.get("input_quality_status") == QualityStatus.DEGRADED.value
    if is_degraded:
        reasons.append({"code": "input_quality_degraded", "severity": "degrade"})

    total_checks = len(REQUIRED_FIELDS) + 2
    failed = len(errors)
    warning_count = len(warnings)
    passed = total_checks - failed
    degrade_score = 0.5 if is_degraded else 0.0
    reasons.extend({"code": issue.code, "field": issue.field, "severity": issue.severity} for issue in (*errors, *warnings))

    trace = {
        "counts": {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warning_count,
        },
        "severity_distribution": {
            "error": failed,
            "warning": warning_count,
            "degrade": 1 if is_degraded else 0,
        },
        "is_degraded": is_degraded,
        "degrade_score": degrade_score,
        "reasons": reasons,
    }
    summary = ValidationSummaryObj(counts=ValidationCounts(total_checks=total_checks, passed=passed, failed=failed, warnings=warning_count))
    return ValidationResult(is_valid=failed == 0, errors=tuple(errors), warnings=tuple(warnings), trace=trace, summary=summary)


def score_grid_candidates(payload: dict[str, Any], decision: Decision) -> CandidateSelection:
    candidates = payload.get("grid_candidates")
    if not candidates:
        support = float(payload["support_level"])
        resistance = float(payload["resistance_level"])
        width = resistance - support
        candidates = [
            {"candidate_id": "gc-1", "price_down": support, "price_up": resistance, "grid_count": 8, "grid_step": width / 8},
            {"candidate_id": "gc-2", "price_down": support + width * 0.05, "price_up": resistance - width * 0.05, "grid_count": 10, "grid_step": width / 10},
            {"candidate_id": "gc-3", "price_down": support + width * 0.1, "price_up": resistance - width * 0.1, "grid_count": 12, "grid_step": width / 12},
        ]
    scored: list[CandidateScore] = []
    atr = max(float(payload.get("atr", 1.0)), 1.0)
    for item in candidates:
        width = float(item["price_up"]) - float(item["price_down"])
        count = int(item["grid_count"])
        step = float(item["grid_step"])
        efficiency = 0.55 + min(width / (atr * 10), 0.35) + min(count / 100, 0.1)
        if decision == Decision.REJECT:
            efficiency *= 0.8
        scored.append(CandidateScore(candidate_id=str(item["candidate_id"]), price_down=float(item["price_down"]), price_up=float(item["price_up"]), grid_count=count, grid_step=step, efficiency_score=round(min(efficiency, 0.99), 6), notes="deterministic rank"))
    ranked = tuple(sorted(scored, key=lambda c: (-c.efficiency_score, c.candidate_id)))
    return CandidateSelection(ranked=ranked, selected=ranked[0] if ranked else None)


def decide(payload: dict[str, Any], *, generated_at_override: str | None = None) -> MaffiOutput:
    validation = validate_payload(payload)
    generated_at = generated_at_override or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    steps = []
    def step(
        name: str,
        status: str,
        reason: str,
        metrics: dict[str, Any] | None = None,
        *,
        reasons: list[dict[str, Any]] | None = None,
    ):
        steps.append(
            {
                "name": name,
                "status": status,
                "reason": reason,
                "reasons": reasons or [{"code": reason, "priority": 100}],
                "inputs": {},
                "outputs": {},
                "metrics": metrics or {},
                "warnings": [],
            },
        )

    if not validation.is_valid:
        reject_reason = "validation_failed"
        decision = Decision.REJECT
        for name in ["gate", "direction", "range", "grid_count", "tp_sl", "confidence"]:
            step(name, "fail" if name == "gate" else "skip", reject_reason)
        selected = None
        confidence = 0.0
    elif payload["input_quality_status"] == QualityStatus.BAD.value:
        reject_reason = "input_quality_bad"
        decision = Decision.REJECT
        for name in ["gate", "direction", "range", "grid_count", "tp_sl", "confidence"]:
            step(name, "fail" if name == "gate" else "skip", reject_reason)
        selected = None
        confidence = 0.0
    elif float(payload["reject_score"]) >= 60:
        reject_reason = "reject_score_high"
        decision = Decision.REJECT
        for name in ["gate", "direction", "range", "grid_count", "tp_sl", "confidence"]:
            step(name, "fail" if name == "gate" else "skip", reject_reason)
        selected = None
        confidence = 0.0
    elif float(payload["confidence_hint"]) < 0.4:
        reject_reason = "confidence_too_low"
        decision = Decision.REJECT
        for name in ["gate", "direction", "range", "grid_count", "tp_sl", "confidence"]:
            step(name, "fail" if name == "gate" else "skip", reject_reason)
        selected = None
        confidence = 0.0
    else:
        confidence_hint = float(payload["confidence_hint"])
        direction_resolution = _resolve_direction(payload)
        conflict_is_too_high = direction_resolution.conflict_intensity >= 0.35
        confidence_is_low = min(confidence_hint, direction_resolution.certainty) < 0.5
        if conflict_is_too_high and confidence_is_low:
            reject_reason = "direction_conflict_policy_reject"
            decision = Decision.REJECT
            for name in ["gate", "direction", "range", "grid_count", "tp_sl", "confidence"]:
                step(
                    name,
                    "fail" if name == "gate" else "skip",
                    reject_reason,
                    metrics={
                        "score_gap": direction_resolution.score_gap,
                        "regime_weight": direction_resolution.regime_weight,
                        "side_bias_contribution": direction_resolution.side_bias_contribution,
                        "conflict_intensity": direction_resolution.conflict_intensity,
                    },
                    reasons=list(direction_resolution.reasons),
                )
            selected = None
            confidence = 0.0
        else:
            decision = direction_resolution.decision
            reject_reason = None
            ranked = score_grid_candidates(payload, decision)
            selected = ranked.selected
            confidence = min(confidence_hint, direction_resolution.certainty)
            if payload["input_quality_status"] == QualityStatus.DEGRADED.value:
                confidence = max(0.0, confidence - 0.2)
            step("gate", "pass", "accepted", {"reject_score": float(payload["reject_score"])})
            step(
                "direction",
                "pass",
                "resolved",
                {
                    "score_gap": direction_resolution.score_gap,
                    "regime_weight": direction_resolution.regime_weight,
                    "side_bias_contribution": direction_resolution.side_bias_contribution,
                    "conflict_intensity": direction_resolution.conflict_intensity,
                },
                reasons=list(direction_resolution.reasons),
            )
            width_to_atr = (float(payload["resistance_level"]) - float(payload["support_level"])) / max(float(payload["atr"]), 1.0)
            step("range", "pass", "range_scored", {"width_to_atr": width_to_atr})
            step("grid_count", "pass", "candidate_selected", {"candidate_id": selected.candidate_id if selected else None})
            step("tp_sl", "pass", "tp_sl_computed")
            step("confidence", "pass", "confidence_adjusted", {"confidence": confidence})

    if decision == Decision.REJECT:
        tp = sl = entry = None
        upper = lower = None
        grid_count = None
        grid_step = None
        efficiency = None
        selected_candidate_id = "reject"
        digest_mode = "none"
    else:
        entry = float(payload["last_price"])
        atr = float(payload["atr"])
        if decision == Decision.LONG:
            tp = entry + atr * 1.5
            sl = entry - atr
        else:
            tp = entry - atr * 1.5
            sl = entry + atr
        upper = selected.price_up if selected else float(payload["resistance_level"])
        lower = selected.price_down if selected else float(payload["support_level"])
        grid_count = selected.grid_count if selected else 8
        grid_step = selected.grid_step if selected else (upper - lower) / grid_count
        efficiency = selected.efficiency_score if selected else 0.6
        selected_candidate_id = selected.candidate_id if selected else "default"
        digest_mode = "mixed"

    top_reasons = validation.trace["reasons"][:5]
    validation_summary = {
        "counts": validation.trace["counts"],
        "errors": [asdict(err) for err in validation.errors],
        "warnings": [asdict(w) for w in validation.warnings],
        "degrade": {"is_degraded": validation.trace["is_degraded"], "degrade_score": validation.trace["degrade_score"]},
        "top_reasons": top_reasons,
    }

    decision_summary = {
        "direction": decision.value,
        "selected_candidate_id": selected_candidate_id,
        "tp_sl_logic_digest": {
            "mode": digest_mode,
            "tp_basis": "atr",
            "sl_basis": "atr",
            "rr_estimate": 1.5 if decision != Decision.REJECT else 0.0,
        },
    }

    return MaffiOutput(
        schema_version=str(payload.get("schema_version", "maffi-v1")),
        generated_at_utc=generated_at,
        symbol=str(payload.get("symbol", "")),
        decision=decision,
        confidence=round(confidence, 6),
        selected_entry=entry,
        tp=tp,
        sl=sl,
        input_quality_status=QualityStatus(str(payload.get("input_quality_status", "bad"))),
        reject_reason=reject_reason,
        rationale=(f"decision={decision.value}",),
        grid_upper_price=upper,
        grid_lower_price=lower,
        grid_count=grid_count,
        grid_step=grid_step,
        efficiency_score=efficiency,
        selected_candidate_id=selected_candidate_id,
        validation_summary=validation_summary,
        decision_summary=decision_summary,
        decision_trace={"selection": {"selected_candidate_id": selected_candidate_id}, "steps": steps},
    )


def deterministic_replay(payload: dict[str, Any]) -> tuple[MaffiOutput, MaffiOutput]:
    fixed_ts = "2026-03-24T12:00:00Z"
    return decide(payload, generated_at_override=fixed_ts), decide(payload, generated_at_override=fixed_ts)


def maffi_output_to_dict(output: MaffiOutput) -> dict[str, Any]:
    return {
        "schema_version": output.schema_version,
        "generated_at_utc": output.generated_at_utc,
        "symbol": output.symbol,
        "decision": output.decision.value,
        "confidence": output.confidence,
        "selected_entry": output.selected_entry,
        "tp": output.tp,
        "sl": output.sl,
        "input_quality_status": output.input_quality_status.value,
        "reject_reason": output.reject_reason,
        "rationale": list(output.rationale),
        "grid_upper_price": output.grid_upper_price,
        "grid_lower_price": output.grid_lower_price,
        "grid_count": output.grid_count,
        "grid_step": output.grid_step,
        "efficiency_score": output.efficiency_score,
        "selected_candidate_id": output.selected_candidate_id,
        "validation_summary": output.validation_summary,
        "decision_summary": output.decision_summary,
        "decision_trace": output.decision_trace,
    }


def maffi_output_to_json(output: MaffiOutput) -> str:
    return json.dumps(maffi_output_to_dict(output), ensure_ascii=False, sort_keys=False)
