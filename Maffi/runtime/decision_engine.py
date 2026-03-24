from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from .enums import Decision, QualityStatus
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
    if not validation.is_valid:
        return _reject_output(
            payload,
            "validation_failed",
            [f"{issue.field}: {issue.message}" for issue in validation.errors],
            generated_at=generated_at,
        )

    if payload["input_quality_status"] == QualityStatus.BAD.value:
        return _reject_output(
            payload,
            "input_quality_bad",
            ["Input data quality is BAD; hard reject policy applied."],
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
            generated_at=generated_at,
        )

    quality_penalty = 0.20 if payload["input_quality_status"] == QualityStatus.DEGRADED.value else 0.0
    confidence = max(0.0, min(1.0, float(payload["confidence_hint"]) - quality_penalty))

    decision = Decision.LONG if long_score >= short_score else Decision.SHORT
    selected_entry = _select_entry(payload["entry_candidates"], decision, payload["last_price"])
    tp, sl = _tp_sl(selected_entry, payload["atr"], decision, payload["support_level"], payload["resistance_level"])

    rationale = (
        f"decision={decision.value}",
        f"long_score={long_score:.2f}",
        f"short_score={short_score:.2f}",
        f"quality={payload['input_quality_status']}",
    )
    trace = {
        "scoring": {
            "long_score": long_score,
            "short_score": short_score,
            "reject_score": reject_score,
        },
        "validation": {
            "is_valid": validation.is_valid,
            "warnings": [asdict(w) for w in validation.warnings],
        },
        "selection": {
            "selected_entry": selected_entry,
            "tp": tp,
            "sl": sl,
        },
    }
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
        decision_trace=trace,
    )


def _select_entry(candidates: list[float], decision: Decision, last_price: float) -> float:
    if decision == Decision.LONG:
        viable = [float(c) for c in candidates if float(c) <= float(last_price)]
        return max(viable) if viable else float(min(candidates))
    viable = [float(c) for c in candidates if float(c) >= float(last_price)]
    return min(viable) if viable else float(max(candidates))


def _tp_sl(entry: float, atr: float, decision: Decision, support: float, resistance: float) -> tuple[float, float]:
    atr = float(atr)
    if decision == Decision.LONG:
        tp = min(float(resistance), entry + atr * 1.5)
        sl = max(float(support), entry - atr)
        return tp, sl
    tp = max(float(support), entry - atr * 1.5)
    sl = min(float(resistance), entry + atr)
    return tp, sl


def _reject_output(payload: dict[str, Any], reason: str, rationale: list[str], *, generated_at: str) -> MaffiOutput:
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
        decision_trace={"reject_reason": reason},
    )
