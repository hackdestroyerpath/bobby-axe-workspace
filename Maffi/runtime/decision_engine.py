from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .enums import Decision

_NEAR_EQUAL_GAP = 3.0
_LOW_SIGNAL_REGIME_WEIGHTS = {
    "ranging": 0.72,
    "noisy": 0.68,
}
_REGIME_WEIGHTS = {
    "trend": 1.0,
    "breakout": 0.95,
    "normal": 0.9,
    "ranging": _LOW_SIGNAL_REGIME_WEIGHTS["ranging"],
    "noisy": _LOW_SIGNAL_REGIME_WEIGHTS["noisy"],
    "chaotic": 0.55,
}


@dataclass(frozen=True)
class DirectionResolution:
    decision: Decision
    certainty: float
    score_gap: float
    regime_weight: float
    side_bias_contribution: float
    conflict_intensity: float
    reasons: tuple[dict[str, Any], ...]



def _resolve_direction(payload: dict[str, Any]) -> DirectionResolution:
    long_score = float(payload["long_score"])
    short_score = float(payload["short_score"])
    score_gap = abs(long_score - short_score)
    score_side = Decision.LONG if long_score >= short_score else Decision.SHORT

    market_regime = str(payload.get("market_regime", "normal"))
    volatility_regime = str(payload.get("volatility_regime", "normal"))
    regime_weight = _REGIME_WEIGHTS.get(market_regime, 0.85)
    if volatility_regime in {"high", "elevated"}:
        regime_weight *= 0.9

    dominant_side = str(payload.get("dominant_side", "")).lower()
    dominant_side_map = {"buyers": Decision.LONG, "sellers": Decision.SHORT}
    dominant_decision = dominant_side_map.get(dominant_side)

    reasons: list[dict[str, Any]] = []
    near_equal_scores = score_gap < _NEAR_EQUAL_GAP
    if near_equal_scores:
        reasons.append({"code": "near_equal_scores", "priority": 10, "value": score_gap})

    side_conflict = dominant_decision is not None and dominant_decision != score_side
    if side_conflict:
        reasons.append({"code": "dominant_side_conflict", "priority": 20, "dominant_side": dominant_side})

    decision = score_side
    side_bias_contribution = 0.0

    if near_equal_scores and dominant_decision is not None:
        decision = dominant_decision
        side_bias_contribution = 0.12 * regime_weight if dominant_decision == Decision.LONG else -0.12 * regime_weight
        reasons.append({"code": "near_equal_bias_applied", "priority": 30, "selected": decision.value})

    if side_conflict and not near_equal_scores:
        # Keep score-dominance as primary signal and expose the conflict explicitly.
        reasons.append({"code": "score_dominance_kept", "priority": 40, "selected": decision.value})

    certainty = min(1.0, max(0.0, (score_gap / 20.0) * regime_weight))

    if near_equal_scores:
        certainty *= 0.55

    if market_regime in _LOW_SIGNAL_REGIME_WEIGHTS:
        certainty *= _LOW_SIGNAL_REGIME_WEIGHTS[market_regime]
        reasons.append({"code": "low_signal_regime", "priority": 50, "regime": market_regime})

    if side_conflict:
        certainty *= 0.65

    conflict_intensity = min(1.0, (score_gap / 20.0) * (1.0 if side_conflict else 0.0) * regime_weight)

    reasons.append({"code": "final_direction", "priority": 100, "selected": decision.value})

    return DirectionResolution(
        decision=decision,
        certainty=round(certainty, 6),
        score_gap=round(score_gap, 6),
        regime_weight=round(regime_weight, 6),
        side_bias_contribution=round(side_bias_contribution, 6),
        conflict_intensity=round(conflict_intensity, 6),
        reasons=tuple(sorted(reasons, key=lambda item: int(item.get("priority", 999)))),
    )
