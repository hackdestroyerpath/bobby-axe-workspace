from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .enums import Decision, QualityStatus
from .grid_scoring import GridCandidateScore, score_grid_candidates
from .models import MaffiOutput, now_utc_iso
from .validator import validate_payload

_REJECT_SCORE_THRESHOLD = 60.0
_MIN_CONFIDENCE_THRESHOLD = 0.35
_DIRECTION_CONFLICT_GAP = 4.0


@dataclass(frozen=True, slots=True)
class DirectionResolution:
    decision: Decision
    reason: str
    metrics: dict[str, Any]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RangeResolution:
    grid_lower_price: float
    grid_upper_price: float
    reason: str
    metrics: dict[str, Any]
    warnings: tuple[str, ...] = ()


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

    long_score = float(payload["long_score"])
    short_score = float(payload["short_score"])
    reject_score = float(payload["reject_score"])
    confidence_hint = float(payload["confidence_hint"])
    score_gap = abs(long_score - short_score)
    reject_reason, reject_rationale = _apply_reject_policy(
        input_quality_status=str(payload["input_quality_status"]),
        reject_score=reject_score,
        confidence_hint=confidence_hint,
        score_gap=score_gap,
    )
    if reject_reason is not None:
        return _reject_output(
            payload,
            reject_reason,
            reject_rationale,
            validation_summary=validation_summary,
            generated_at=generated_at,
        )

    quality_penalty = 0.20 if payload["input_quality_status"] == QualityStatus.DEGRADED.value else 0.0
    confidence = max(0.0, min(1.0, confidence_hint - quality_penalty))

    direction = _resolve_direction(payload)
    range_resolution = _resolve_range(payload, direction.decision)
    scoring = score_grid_candidates(payload, direction.decision)
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
    tp, sl = _tp_sl(
        selected_entry,
        payload["atr"],
        direction.decision,
        range_resolution.grid_lower_price,
        range_resolution.grid_upper_price,
    )

    rationale = (
        f"decision={direction.decision.value}",
        f"long_score={long_score:.2f}",
        f"short_score={short_score:.2f}",
        f"quality={payload['input_quality_status']}",
        f"direction_reason={direction.reason}",
    )
    decision_summary = _build_decision_summary(
        decision=direction.decision,
        selected_entry=selected_entry,
        tp=tp,
        sl=sl,
        atr=float(payload["atr"]),
        selected_candidate_id=scoring.selected.candidate_id,
    )
    trace = _build_decision_trace(
        decision=direction.decision,
        confidence=confidence,
        selected_entry=selected_entry,
        tp=tp,
        sl=sl,
        reject_reason=None,
        reject_score=reject_score,
        grid_candidate=scoring.selected,
        selected_candidate_id=scoring.selected.candidate_id,
        direction_resolution=direction,
        range_resolution=range_resolution,
    )
    return MaffiOutput(
        schema_version=str(payload["schema_version"]),
        generated_at_utc=generated_at,
        symbol=str(payload["symbol"]),
        decision=direction.decision,
        confidence=confidence,
        selected_entry=selected_entry,
        tp=tp,
        sl=sl,
        input_quality_status=QualityStatus(payload["input_quality_status"]),
        reject_reason=None,
        rationale=rationale,
        grid_upper_price=range_resolution.grid_upper_price,
        grid_lower_price=range_resolution.grid_lower_price,
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


def _apply_reject_policy(
    *,
    input_quality_status: str,
    reject_score: float,
    confidence_hint: float,
    score_gap: float,
) -> tuple[str | None, list[str]]:
    if input_quality_status == QualityStatus.BAD.value:
        return "input_quality_bad", ["Input data quality is BAD; hard reject policy applied."]
    if reject_score >= _REJECT_SCORE_THRESHOLD:
        return "reject_score_high", [f"reject_score={reject_score:.2f} >= {_REJECT_SCORE_THRESHOLD:.2f}"]
    if confidence_hint < _MIN_CONFIDENCE_THRESHOLD:
        return "confidence_too_low", [f"confidence_hint={confidence_hint:.2f} < {_MIN_CONFIDENCE_THRESHOLD:.2f}"]
    if score_gap < _DIRECTION_CONFLICT_GAP and confidence_hint < 0.50:
        return "direction_conflict", [f"score_gap={score_gap:.2f} < {_DIRECTION_CONFLICT_GAP:.2f} under low confidence"]
    return None, []


def _resolve_direction(payload: dict[str, Any]) -> DirectionResolution:
    long_score = float(payload["long_score"])
    short_score = float(payload["short_score"])
    market_regime = str(payload["market_regime"])
    dominant_side = str(payload["dominant_side"])
    confidence_hint = float(payload["confidence_hint"])
    score_gap = abs(long_score - short_score)

    direction = Decision.LONG if long_score >= short_score else Decision.SHORT
    reasons: list[str] = ["score_dominance"]
    warnings: list[str] = []

    if score_gap < _DIRECTION_CONFLICT_GAP:
        reasons.append("near_balanced_scores")
        if dominant_side == "buyers":
            direction = Decision.LONG
            reasons.append("dominant_side_buyers_bias")
        elif dominant_side == "sellers":
            direction = Decision.SHORT
            reasons.append("dominant_side_sellers_bias")
        if market_regime == "ranging":
            warnings.append("market_regime_ranging_conflict_risk")
    if market_regime == "trend":
        reasons.append("trend_following")
    if confidence_hint < 0.55:
        warnings.append("confidence_soft")

    return DirectionResolution(
        decision=direction,
        reason="; ".join(reasons),
        metrics={
            "long_score": long_score,
            "short_score": short_score,
            "score_gap": score_gap,
            "market_regime": market_regime,
            "dominant_side": dominant_side,
        },
        warnings=tuple(warnings),
    )


def _resolve_range(payload: dict[str, Any], decision: Decision) -> RangeResolution:
    support = float(payload["support_level"])
    resistance = float(payload["resistance_level"])
    last_price = float(payload["last_price"])
    atr = max(float(payload["atr"]), 1e-9)
    lower = min(support, resistance)
    upper = max(support, resistance)
    width = max(upper - lower, 1e-9)
    width_to_atr = width / atr

    warnings: list[str] = []
    if width_to_atr < 1.2:
        warnings.append("range_too_narrow_vs_atr")
    if width_to_atr > 15.0:
        warnings.append("range_too_wide_vs_atr")
    if last_price < lower or last_price > upper:
        warnings.append("last_price_outside_range")

    reason = "range_aligned_with_direction"
    if decision == Decision.LONG and last_price <= lower:
        reason = "long_range_rebound_context"
    elif decision == Decision.SHORT and last_price >= upper:
        reason = "short_range_reversal_context"

    return RangeResolution(
        grid_lower_price=lower,
        grid_upper_price=upper,
        reason=reason,
        metrics={
            "support_level": support,
            "resistance_level": resistance,
            "last_price": last_price,
            "width": width,
            "width_to_atr": width_to_atr,
        },
        warnings=tuple(warnings),
    )


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
        schema_version=str(payload.get("schema_version", "maffi-v1")),
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
    if getattr(validation, "summary", None) is not None:
        return validation.summary.to_dict()
    errors = [f"{issue.field}: {issue.message}" for issue in validation.errors]
    warnings = [f"{issue.field}: {issue.message}" for issue in validation.warnings]
    quality_status = str(payload.get("input_quality_status", "bad"))
    is_degraded = quality_status in {QualityStatus.DEGRADED.value, QualityStatus.BAD.value}
    return {
        "counts": {
            "total_checks": len(errors) + len(warnings),
            "passed": 0,
            "failed": len(errors),
            "warnings": len(warnings),
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
        "top_reasons": [],
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
    direction_resolution: DirectionResolution | None = None,
    range_resolution: RangeResolution | None = None,
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
        direction_reason = direction_resolution.reason if direction_resolution is not None else "direction selected from score comparison"
        range_status = "pass"
        range_reason = range_resolution.reason if range_resolution is not None else "entry within corridor"
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
            metrics=direction_resolution.metrics if direction_resolution is not None else {},
            warnings=list(direction_resolution.warnings) if direction_resolution is not None else [],
        ),
        _step(
            name="range",
            status=range_status,
            reason=range_reason,
            outputs={
                "selected_entry": selected_entry,
                "grid_lower_price": range_resolution.grid_lower_price if range_resolution is not None else None,
                "grid_upper_price": range_resolution.grid_upper_price if range_resolution is not None else None,
            },
            metrics=range_resolution.metrics if range_resolution is not None else {},
            warnings=list(range_resolution.warnings) if range_resolution is not None else [],
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
