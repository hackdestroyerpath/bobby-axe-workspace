from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .enums import Decision, DominantSide, MarketRegime, QualityStatus, VolatilityRegime


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field: str
    message: str
    severity: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[ValidationIssue, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class MaffiInputPayload:
    schema_version: str
    symbol: str
    generated_at_utc: str
    source: str
    input_quality_status: QualityStatus
    market_regime: MarketRegime
    volatility_regime: VolatilityRegime
    dominant_side: DominantSide
    long_score: float
    short_score: float
    reject_score: float
    confidence_hint: float
    entry_candidates: tuple[float, ...]
    support_level: float
    resistance_level: float
    last_price: float
    atr: float
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MaffiOutput:
    schema_version: str
    generated_at_utc: str
    symbol: str
    decision: Decision
    confidence: float
    selected_entry: float | None
    tp: float | None
    sl: float | None
    input_quality_status: QualityStatus
    reject_reason: str | None
    rationale: tuple[str, ...]
    decision_trace: dict[str, Any]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
