from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .enums import Decision, QualityStatus


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field: str
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True, slots=True)
class ValidationCounts:
    total_checks: int
    passed: int
    failed: int
    warnings: int


@dataclass(frozen=True, slots=True)
class ValidationSummaryObj:
    counts: ValidationCounts


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[ValidationIssue, ...]
    warnings: tuple[ValidationIssue, ...]
    trace: dict[str, Any]
    summary: ValidationSummaryObj


@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate_id: str
    price_down: float
    price_up: float
    grid_count: int
    grid_step: float
    efficiency_score: float
    notes: str


@dataclass(frozen=True, slots=True)
class CandidateSelection:
    ranked: tuple[CandidateScore, ...]
    selected: CandidateScore | None


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
    grid_upper_price: float | None
    grid_lower_price: float | None
    grid_count: int | None
    grid_step: float | None
    efficiency_score: float | None
    selected_candidate_id: str
    validation_summary: dict[str, Any]
    decision_summary: dict[str, Any]
    decision_trace: dict[str, Any]


@dataclass(frozen=True, slots=True)
class MaffiPayload:
    schema_version: str
    symbol: str
    generated_at_utc: str
    source: str
    input_quality_status: QualityStatus
    market_regime: str
    volatility_regime: str
    dominant_side: str
    long_score: float
    short_score: float
    reject_score: float
    confidence_hint: float
    entry_candidates: tuple[float, ...]
    support_level: float
    resistance_level: float
    last_price: float
    atr: float
    context: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Tick:
    ts: datetime
    price: float
    volume: float
    side: str


@dataclass(frozen=True, slots=True)
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True, slots=True)
class TrendStructure:
    direction: str
    strength: float


@dataclass(frozen=True, slots=True)
class MarketRegimeScores:
    trend: float
    ranging: float
    noisy: float


@dataclass(frozen=True, slots=True)
class MarketRegime:
    label: str
    scores: MarketRegimeScores


@dataclass(frozen=True, slots=True)
class VolatilityRegime:
    label: str


@dataclass(frozen=True, slots=True)
class SupportResistance:
    support: float
    resistance: float
    support_touches: int
    resistance_touches: int


@dataclass(frozen=True, slots=True)
class EntryCandidate:
    price: float
    quality: float


@dataclass(frozen=True, slots=True)
class PreprocessingFeatures:
    tick_count: int
    ohlcv_by_timeframe: dict[str, tuple[Candle, ...]]
    market_regime: MarketRegime
    volatility_regime: VolatilityRegime
    realized_vol: float
    support_resistance: SupportResistance
    entry_candidates: tuple[EntryCandidate, ...]


@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    sanitized_ticks: tuple[Tick, ...]
    features: PreprocessingFeatures
