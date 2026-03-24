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
class ValidationCounts:
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int = 0


@dataclass(frozen=True, slots=True)
class ValidationDegrade:
    is_degraded: bool
    degrade_score: float
    sources: tuple[str, ...] = ()
    policy: str = "hard_reject_bad_soft_penalty_degraded"


@dataclass(frozen=True, slots=True)
class ValidationTopReason:
    code: str
    count: int
    severity: str


@dataclass(frozen=True, slots=True)
class ValidationSummary:
    counts: ValidationCounts
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    degrade: ValidationDegrade = field(default_factory=lambda: ValidationDegrade(is_degraded=False, degrade_score=0.0))
    top_reasons: tuple[ValidationTopReason, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": {
                "total_checks": self.counts.total_checks,
                "passed": self.counts.passed,
                "failed": self.counts.failed,
                "warnings": self.counts.warnings,
                "skipped": self.counts.skipped,
            },
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "degrade": {
                "is_degraded": self.degrade.is_degraded,
                "degrade_score": self.degrade.degrade_score,
                "sources": list(self.degrade.sources),
                "policy": self.degrade.policy,
            },
            "top_reasons": [
                {
                    "code": reason.code,
                    "count": reason.count,
                    "severity": reason.severity,
                }
                for reason in self.top_reasons
            ],
        }


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[ValidationIssue, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()
    trace: dict[str, Any] = field(default_factory=dict)
    summary: ValidationSummary = field(
        default_factory=lambda: ValidationSummary(
            counts=ValidationCounts(total_checks=0, passed=0, failed=0, warnings=0),
        )
    )


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
    grid_upper_price: float | None
    grid_lower_price: float | None
    grid_count: int | None
    grid_step: float | None
    efficiency_score: float | None
    selected_candidate_id: str | None
    validation_summary: dict[str, Any]
    decision_summary: dict[str, Any]
    decision_trace: dict[str, Any]


@dataclass(frozen=True, slots=True)
class OhlcvCandle:
    timeframe: str
    bucket_start: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int


@dataclass(frozen=True, slots=True)
class TrendStructure:
    direction: str
    slope: float
    strength: float
    higher_highs: int
    lower_lows: int


@dataclass(frozen=True, slots=True)
class SupportResistanceLevels:
    support: float
    resistance: float
    support_touches: int
    resistance_touches: int


@dataclass(frozen=True, slots=True)
class EntryCandidate:
    price: float
    strategy: str
    quality: float


@dataclass(frozen=True, slots=True)
class RegimeScores:
    trend: float
    ranging: float
    noisy: float


@dataclass(frozen=True, slots=True)
class RegimeClassification:
    label: str
    scores: RegimeScores
    rationale: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreprocessingFeatures:
    tick_count: int
    last_price: float
    realized_vol: float
    price_range: float
    buy_volume: float
    sell_volume: float
    imbalance: float
    dominant_side: str
    trend: TrendStructure
    support_resistance: SupportResistanceLevels
    market_regime: RegimeClassification
    volatility_regime: RegimeClassification
    entry_candidates: tuple[EntryCandidate, ...]
    side_distribution: dict[str, int]
    ohlcv_by_timeframe: dict[str, list[OhlcvCandle]]


@dataclass(frozen=True, slots=True)
class FeatureExtractionResult:
    features: PreprocessingFeatures
    sanitized_ticks: tuple[Any, ...]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
