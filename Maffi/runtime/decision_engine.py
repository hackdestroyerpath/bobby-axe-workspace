from __future__ import annotations

from typing import Any, Callable

from .enums import Decision, QualityStatus
from .grid_scoring import GridCandidateScore, score_grid_candidates
from .models import MaffiOutput, now_utc_iso
from .validator import validate_payload


def decide(
    payload: dict[str, Any],
    *,
    generated_at_override: str | None = None,
    clock: Callable[[], str] | None = None,
) -> MaffiOutput:
    generated_at = generated_at_override if generated_at_override is not None else (clock or now_utc_iso)()

    validation = validate_payload(payload)
    validation_summary = _build_validation_summary(validation, payload)
    if not validation.is_valid:
        return _reject_output(
            payload,
            "validation_failed",
            [f"{issue.field}: {issue.message}" for issue in validation.errors],
            validation_summary=validation_summary,
            generated_at=generated_at,
        )

    if payload["input_quality_status"] == QualityStatus.BAD.value:
        return _reject_output(
            payload,
            "input_quality_bad",
            ["Input data quality is BAD; hard reject policy applied."],
            validation_summary=validation_summary,
            generated_at=generated_at,
        )

    long_score = float(payload["long_score"])
    short_score = float(payload["short_score"])
    reject_score = float(payload["reject_score"])

    if reject_score >= 60:
        return _reject_output(
            payload,
            "reject_score_high",
            [f"reject_score={reject_score:.2f} >= 60.00"],
            validation_summary=validation_summary,
            generated_at=generated_at,
        )

    quality_penalty = 0.20 if payload["input_quality_status"] == QualityStatus.DEGRADED.value else 0.0
    confidence = max(0.0, min(1.0, float(payload["confidence_hint"]) - quality_penalty))

    decision = Decision.LONG if long_score >= short_score else Decision.SHORT
    scoring = score_grid_candidates(payload, decision)
    if scoring.selected is None:
        return _reject_output(
            payload,
            "efficiency_score_low",
            ["No grid candidate met efficiency_score >= 0.60."],
            validation_summary=validation_summary,
            generated_at=generated_at,
            grid_candidate=scoring.ranked[0] if scoring.ranked else None,
            selected_candidate_id=None,
        )
    selected_entry = scoring.selected.entry_price
    tp, sl = _tp_sl(selected_entry, payload["atr"], decision, payload["support_level"], payload["resistance_level"])

    rationale = (
        f"decision={decision.value}",
        f"long_score={long_score:.2f}",
        f"short_score={short_score:.2f}",
        f"quality={payload['input_quality_status']}",
    )
    decision_summary = _build_decision_summary(
        decision=decision,
        selected_entry=selected_entry,
        tp=tp,
        sl=sl,
        atr=float(payload["atr"]),
        selected_candidate_id=scoring.selected.candidate_id,
    )
    trace = _build_decision_trace(
        decision=decision,
        confidence=confidence,
        selected_entry=selected_entry,
        tp=tp,
        sl=sl,
        reject_reason=None,
        reject_score=reject_score,
        grid_candidate=scoring.selected,
        selected_candidate_id=scoring.selected.candidate_id,
    )
    return MaffiOutput(
        schema_version=str(payload["schema_version"]),
        generated_at_utc=generated_at,
        symbol=str(payload["symbol"]),
        decision=decision,
        confidence=confidence,
        selected_entry=selected_entry,
        tp=tp,
        sl=sl,
        input_quality_status=QualityStatus(payload["input_quality_status"]),
        reject_reason=None,
        rationale=rationale,
        grid_upper_price=scoring.selected.grid_upper_price,
        grid_lower_price=scoring.selected.grid_lower_price,
        grid_count=scoring.selected.grid_count,
        grid_step=scoring.selected.grid_step,
        efficiency_score=scoring.selected.efficiency_score,
        selected_candidate_id=scoring.selected.candidate_id,
        validation_summary=validation_summary,
        decision_summary=decision_summary,
        decision_trace=trace,
    )


def _tp_sl(entry: float, atr: float, decision: Decision, support: float, resistance: float) -> tuple[float, float]:
    atr = float(atr)
    if decision == Decision.LONG:
        tp = min(float(resistance), entry + atr * 1.5)
        sl = max(float(support), entry - atr)
        return tp, sl
    tp = max(float(support), entry - atr * 1.5)
    sl = min(float(resistance), entry + atr)
    return tp, sl


def _reject_output(
    payload: dict[str, Any],
    reason: str,
    rationale: list[str],
    *,
    validation_summary: dict[str, Any],
    generated_at: str,
    grid_candidate: GridCandidateScore | None = None,
    selected_candidate_id: str | None = None,
) -> MaffiOutput:
    reject_score = float(payload.get("reject_score", 0.0)) if isinstance(payload.get("reject_score"), (int, float)) else 0.0
    decision_summary = _build_decision_summary(
        decision=Decision.REJECT,
        selected_entry=None,
        tp=None,
        sl=None,
        atr=float(payload.get("atr", 0.0)) if isinstance(payload.get("atr"), (int, float)) else 0.0,
        reject_reason=reason,
        selected_candidate_id=selected_candidate_id,
    )
    return MaffiOutput(
        schema_version=str(payload.get("schema_version", "maffi-v0.1")),
        generated_at_utc=generated_at,
        symbol=str(payload.get("symbol", "UNKNOWN")),
        decision=Decision.REJECT,
        confidence=0.0,
        selected_entry=None,
        tp=None,
        sl=None,
        input_quality_status=QualityStatus(payload.get("input_quality_status", QualityStatus.BAD.value)),
        reject_reason=reason,
        rationale=tuple(rationale),
        grid_upper_price=grid_candidate.grid_upper_price if grid_candidate is not None else None,
        grid_lower_price=grid_candidate.grid_lower_price if grid_candidate is not None else None,
        grid_count=grid_candidate.grid_count if grid_candidate is not None else None,
        grid_step=grid_candidate.grid_step if grid_candidate is not None else None,
        efficiency_score=grid_candidate.efficiency_score if grid_candidate is not None else None,
        selected_candidate_id=selected_candidate_id,
        validation_summary=validation_summary,
        decision_summary=decision_summary,
        decision_trace=_build_decision_trace(
            decision=Decision.REJECT,
            confidence=0.0,
            selected_entry=None,
            tp=None,
            sl=None,
            reject_reason=reason,
            reject_score=reject_score,
            grid_candidate=grid_candidate,
            selected_candidate_id=selected_candidate_id,
        ),
    )


def _build_validation_summary(validation: Any, payload: dict[str, Any]) -> dict[str, Any]:
    errors = [f"{issue.field}: {issue.message}" for issue in validation.errors]
    warnings = [f"{issue.field}: {issue.message}" for issue in validation.warnings]
    failed = len(errors)
    warnings_count = len(warnings)
    passed = 1 if validation.is_valid else 0
    total_checks = passed + failed + warnings_count
    quality_status = str(payload.get("input_quality_status", "bad"))
    is_degraded = quality_status == QualityStatus.DEGRADED.value
    top_reasons: list[dict[str, Any]] = []
    issue_counter: dict[tuple[str, str], int] = {}
    for issue in tuple(validation.errors) + tuple(validation.warnings):
        code = str(issue.field)
        severity = "error" if issue.severity == "error" else "warning"
        issue_counter[(code, severity)] = issue_counter.get((code, severity), 0) + 1
    for (code, severity), count in sorted(issue_counter.items(), key=lambda item: (-item[1], item[0][0], item[0][1])):
        top_reasons.append({"code": code, "count": count, "severity": severity})

    return {
        "counts": {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warnings_count,
            "skipped": 0,
        },
        "errors": errors,
        "warnings": warnings,
        "degrade": {
            "is_degraded": is_degraded,
            "degrade_score": 1.0 if is_degraded else 0.0,
            "sources": ["input_quality_status"] if is_degraded else [],
            "policy": "hard_reject_bad_soft_penalty_degraded",
        },
        "top_reasons": top_reasons,
    }


def _build_decision_summary(
    *,
    decision: Decision,
    selected_entry: float | None,
    tp: float | None,
    sl: float | None,
    atr: float,
    reject_reason: str | None = None,
    selected_candidate_id: str | None = None,
) -> dict[str, Any]:
    direction = decision.value
    resolved_candidate_id = (
        selected_candidate_id
        if selected_candidate_id is not None
        else (f"{direction}-{selected_entry:.2f}" if selected_entry is not None else "reject-none")
    )
    if decision == Decision.REJECT:
        tp_sl_logic_digest = {
            "mode": "none",
            "tp_basis": "none",
            "sl_basis": "none",
            "rr_estimate": 0.0,
            "constraints": ["decision_reject"],
            "rejected_by": reject_reason or "unspecified",
            "notes": ["No TP/SL for reject decision."],
        }
    else:
        rr_estimate = 0.0
        if selected_entry is not None and tp is not None and sl is not None:
            reward = abs(tp - selected_entry)
            risk = abs(selected_entry - sl)
            rr_estimate = reward / risk if risk > 0 else 0.0
        tp_sl_logic_digest = {
            "mode": "mixed",
            "tp_basis": "minmax_structure_with_atr_extension",
            "sl_basis": "support_resistance_with_atr_buffer",
            "rr_estimate": rr_estimate,
            "constraints": [f"atr={atr:.6f}"],
            "notes": ["TP/SL computed from ATR and S/R corridor."],
        }
    return {
        "direction": direction,
        "selected_candidate_id": resolved_candidate_id,
        "tp_sl_logic_digest": tp_sl_logic_digest,
    }


def _build_decision_trace(
    *,
    decision: Decision,
    confidence: float,
    selected_entry: float | None,
    tp: float | None,
    sl: float | None,
    reject_reason: str | None,
    reject_score: float,
    grid_candidate: GridCandidateScore | None,
    selected_candidate_id: str | None,
) -> dict[str, Any]:
    rejected = decision == Decision.REJECT

    def _step(
        *,
        name: str,
        status: str,
        reason: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "status": status,
            "reason": reason,
            "inputs": inputs if inputs is not None else {},
            "outputs": outputs if outputs is not None else {},
            "metrics": metrics if metrics is not None else {},
            "warnings": warnings if warnings is not None else [],
        }

    if rejected:
        gate_status = "fail"
        gate_reason = f"reject policy triggered: {reject_reason or 'unspecified'}"
        direction_status = "skip"
        direction_reason = "direction selection skipped on reject path"
        range_status = "skip"
        range_reason = "range evaluation skipped on reject path"
        grid_status = "skip"
        grid_reason = "grid_count selection skipped on reject path"
        tp_sl_status = "skip"
        tp_sl_reason = "tp/sl calculation skipped on reject path"
        confidence_status = "skip"
        confidence_reason = "confidence forced to 0.0 on reject path"
    else:
        gate_status = "pass"
        gate_reason = "payload passed validation and policy gates"
        direction_status = "pass"
        direction_reason = "direction selected from score comparison"
        range_status = "pass"
        range_reason = "entry within corridor"
        grid_status = "pass"
        grid_reason = "entry candidate resolved"
        tp_sl_status = "pass"
        tp_sl_reason = "tp/sl computed"
        confidence_status = "pass"
        confidence_reason = "confidence finalized"

    steps = [
        _step(
            name="gate",
            status=gate_status,
            reason=gate_reason,
            metrics={"reject_score": reject_score},
        ),
        _step(
            name="direction",
            status=direction_status,
            reason=direction_reason,
            outputs={"direction": decision.value},
        ),
        _step(
            name="range",
            status=range_status,
            reason=range_reason,
            outputs={"selected_entry": selected_entry},
        ),
        _step(
            name="grid_count",
            status=grid_status,
            reason=grid_reason,
            outputs={
                "selected_candidate_id": selected_candidate_id,
                "grid_count": grid_candidate.grid_count if grid_candidate is not None else None,
                "grid_lower_price": grid_candidate.grid_lower_price if grid_candidate is not None else None,
                "grid_upper_price": grid_candidate.grid_upper_price if grid_candidate is not None else None,
                "grid_step": grid_candidate.grid_step if grid_candidate is not None else None,
            },
            metrics={
                "selected_candidates": 1 if selected_entry is not None else 0,
                "efficiency_score": grid_candidate.efficiency_score if grid_candidate is not None else None,
            },
        ),
        _step(
            name="tp_sl",
            status=tp_sl_status,
            reason=tp_sl_reason,
            outputs={"tp": tp, "sl": sl},
        ),
        _step(
            name="confidence",
            status=confidence_status,
            reason=confidence_reason,
            metrics={"confidence": confidence},
        ),
    ]
    selection = {
        "selected_candidate_id": selected_candidate_id,
        "grid_upper_price": grid_candidate.grid_upper_price if grid_candidate is not None else None,
        "grid_lower_price": grid_candidate.grid_lower_price if grid_candidate is not None else None,
        "grid_count": grid_candidate.grid_count if grid_candidate is not None else None,
        "grid_step": grid_candidate.grid_step if grid_candidate is not None else None,
        "efficiency_score": grid_candidate.efficiency_score if grid_candidate is not None else None,
    }
    return {"steps": steps, "selection": selection}
