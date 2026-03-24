from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .enums import Decision, QualityStatus


@dataclass(frozen=True, slots=True)
class GridCandidateScore:
    candidate_id: str
    grid_lower_price: float
    grid_upper_price: float
    grid_width: float
    grid_count: int
    grid_step: float
    efficiency_score: float
    candidate_notes: tuple[str, ...]
    utilization_subscore: float
    oscillation_subscore: float
    step_subscore: float
    stability_subscore: float
    boundary_subscore: float
    entry_price: float


@dataclass(frozen=True, slots=True)
class GridScoringResult:
    selected: GridCandidateScore | None
    ranked: tuple[GridCandidateScore, ...]


def score_grid_candidates(payload: dict[str, Any], decision: Decision) -> GridScoringResult:
    support = float(payload["support_level"])
    resistance = float(payload["resistance_level"])
    lower = min(support, resistance)
    upper = max(support, resistance)
    width = max(upper - lower, 1e-9)
    atr = max(float(payload["atr"]), 1e-9)

    scored: list[GridCandidateScore] = []
    for index, raw_entry in enumerate(payload["entry_candidates"], start=1):
        entry = float(raw_entry)
        grid_count = _derive_grid_count(width=width, atr=atr, index=index, decision=decision)
        grid_step = width / float(grid_count)

        utilization = _utilization_subscore(entry=entry, lower=lower, upper=upper)
        oscillation = _oscillation_subscore(payload)
        step = _step_subscore(step=grid_step, atr=atr)
        stability = _stability_subscore(payload)
        boundary = _boundary_subscore(entry=entry, lower=lower, upper=upper, width=width)

        efficiency = _clamp01(
            0.25 * utilization
            + 0.20 * oscillation
            + 0.20 * step
            + 0.20 * stability
            + 0.15 * boundary
        )
        notes = _candidate_notes(entry=entry, lower=lower, upper=upper, efficiency=efficiency)
        scored.append(
            GridCandidateScore(
                candidate_id=f"grid_{index}",
                grid_lower_price=lower,
                grid_upper_price=upper,
                grid_width=width,
                grid_count=grid_count,
                grid_step=grid_step,
                efficiency_score=efficiency,
                candidate_notes=notes,
                utilization_subscore=utilization,
                oscillation_subscore=oscillation,
                step_subscore=step,
                stability_subscore=stability,
                boundary_subscore=boundary,
                entry_price=entry,
            )
        )

    ranked = tuple(
        sorted(
            scored,
            key=lambda item: (-item.efficiency_score, abs(item.entry_price - float(payload["last_price"])), item.candidate_id),
        )
    )
    selected = ranked[0] if ranked and ranked[0].efficiency_score >= 0.60 else None
    return GridScoringResult(selected=selected, ranked=ranked)


def _derive_grid_count(*, width: float, atr: float, index: int, decision: Decision) -> int:
    base = round(width / max(atr * 0.45, 1e-9))
    bias = 1 if decision == Decision.LONG else 0
    return max(3, min(12, base + index - 2 + bias))


def _utilization_subscore(*, entry: float, lower: float, upper: float) -> float:
    midpoint = (lower + upper) / 2.0
    half_width = max((upper - lower) / 2.0, 1e-9)
    return _clamp01(1.0 - abs(entry - midpoint) / half_width)


def _oscillation_subscore(payload: dict[str, Any]) -> float:
    market = str(payload.get("market_regime", "trend"))
    volatility = str(payload.get("volatility_regime", "normal"))
    market_factor = {
        "ranging": 0.82,
        "trend": 0.68,
        "chaotic": 0.42,
    }.get(market, 0.60)
    volatility_factor = {
        "normal": 0.72,
        "low": 0.66,
        "high": 0.50,
    }.get(volatility, 0.62)
    return _clamp01((market_factor + volatility_factor) / 2.0)


def _step_subscore(*, step: float, atr: float) -> float:
    target_step = atr * 0.35
    if target_step <= 0:
        return 0.0
    return _clamp01(1.0 - abs(step - target_step) / target_step)


def _stability_subscore(payload: dict[str, Any]) -> float:
    confidence = _clamp01(float(payload.get("confidence_hint", 0.0)))
    quality = str(payload.get("input_quality_status", QualityStatus.BAD.value))
    quality_factor = {
        QualityStatus.OK.value: 1.0,
        QualityStatus.DEGRADED.value: 0.78,
        QualityStatus.BAD.value: 0.0,
    }.get(quality, 0.5)
    return _clamp01(confidence * quality_factor)


def _boundary_subscore(*, entry: float, lower: float, upper: float, width: float) -> float:
    if lower <= entry <= upper:
        return 1.0
    drift = min(abs(entry - lower), abs(entry - upper))
    return _clamp01(1.0 - drift / max(width, 1e-9))


def _candidate_notes(*, entry: float, lower: float, upper: float, efficiency: float) -> tuple[str, ...]:
    location = "inside" if lower <= entry <= upper else "outside"
    quality = "acceptable" if efficiency >= 0.60 else "weak"
    return (f"entry_{location}_corridor", f"efficiency_{quality}")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
