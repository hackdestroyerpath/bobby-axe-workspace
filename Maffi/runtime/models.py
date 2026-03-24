from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import Decision, QualityStatus


# ---------------------------------------------------------------------------
# Validation / compatibility layer
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# New LLM-flow runtime models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TriggerInput:
    ticker: str
    timeframe: str
    request_ts_utc: str
    direction: str
    exchange: str | None = None
    lookback_window_minutes: int | None = None
    payload_version: str = "maffi-llm-v1"


@dataclass(frozen=True, slots=True)
class RequestContextBlock:
    ticker: str
    timeframe: str
    request_ts_utc: str
    direction: str
    exchange: str | None = None
    lookback_window_minutes: int | None = None
    payload_version: str = "maffi-llm-v1"


@dataclass(frozen=True, slots=True)
class MarketSnapshotBlock:
    last_price: float
    mark_price: float | None = None
    index_price: float | None = None
    vwap_1m: float | None = None
    vwap_5m: float | None = None
    vwap_15m: float | None = None
    trade_count_1m: int | None = None
    trade_count_5m: int | None = None
    volume_1m: float | None = None
    volume_5m: float | None = None
    notional_1m: float | None = None
    notional_5m: float | None = None


@dataclass(frozen=True, slots=True)
class PriceStructureBlock:
    open_1m: float | None = None
    high_1m: float | None = None
    low_1m: float | None = None
    close_1m: float | None = None
    open_5m: float | None = None
    high_5m: float | None = None
    low_5m: float | None = None
    close_5m: float | None = None
    local_high_15m: float | None = None
    local_low_15m: float | None = None
    range_width_1m: float | None = None
    range_width_5m: float | None = None
    close_position_in_1m_range: float | None = None
    close_position_in_5m_range: float | None = None
    distance_to_local_high: float | None = None
    distance_to_local_low: float | None = None


@dataclass(frozen=True, slots=True)
class VolatilityBlock:
    atr_like_1m: float | None = None
    atr_like_5m: float | None = None
    realized_vol_1m: float | None = None
    realized_vol_5m: float | None = None
    return_std_1m: float | None = None
    return_std_5m: float | None = None
    volatility_percentile_1h: float | None = None
    volatility_regime: str | None = None
    impulse_size_last_move: float | None = None
    impulse_duration_seconds: float | None = None
    volatility_stability_score: float | None = None


@dataclass(frozen=True, slots=True)
class OrderFlowBlock:
    buy_volume_1m: float | None = None
    sell_volume_1m: float | None = None
    buy_volume_5m: float | None = None
    sell_volume_5m: float | None = None
    delta_1m: float | None = None
    delta_5m: float | None = None
    cumulative_delta_5m: float | None = None
    imbalance_ratio_1m: float | None = None
    imbalance_ratio_5m: float | None = None
    aggression_score_buy: float | None = None
    aggression_score_sell: float | None = None
    dominant_side: str | None = None
    order_flow_confidence: float | None = None


@dataclass(frozen=True, slots=True)
class MarketRegimeBlock:
    market_regime: str
    regime_confidence: float | None = None
    trend_strength_score: float | None = None
    trend_persistence_score: float | None = None
    mean_reversion_score: float | None = None
    chop_score: float | None = None
    noise_score: float | None = None
    reversal_frequency_score: float | None = None


@dataclass(frozen=True, slots=True)
class SupportResistanceBlock:
    support_zone_low: float | None = None
    support_zone_high: float | None = None
    resistance_zone_low: float | None = None
    resistance_zone_high: float | None = None
    nearest_support_distance: float | None = None
    nearest_resistance_distance: float | None = None
    boundary_reaction_score: float | None = None
    bounce_frequency_score: float | None = None
    wick_rejection_score_upper: float | None = None
    wick_rejection_score_lower: float | None = None
    level_respect_score: float | None = None


@dataclass(frozen=True, slots=True)
class GridGeometryHintsBlock:
    recommended_price_down: float | None = None
    recommended_price_up: float | None = None
    recommended_grid_step: float | None = None
    recommended_grid_count_min: int | None = None
    recommended_grid_count_max: int | None = None
    recommended_tp_zone: float | None = None
    recommended_sl_zone: float | None = None
    grid_width_hint: float | None = None
    grid_density_hint: str | None = None


@dataclass(frozen=True, slots=True)
class GridCandidateScore:
    candidate_id: str
    price_down: float
    price_up: float
    grid_count: int
    grid_step: float
    efficiency_score: float
    range_utilization_score: float | None = None
    oscillation_score: float | None = None
    step_quality_score: float | None = None
    stability_score: float | None = None
    boundary_respect_score: float | None = None
    candidate_notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GridCandidatesBlock:
    candidates: tuple[GridCandidateScore, ...] = ()


@dataclass(frozen=True, slots=True)
class QualityTrustBlock:
    input_quality_status: str
    data_quality_score: float | None = None
    coverage_ratio: float | None = None
    largest_gap_seconds: float | None = None
    outlier_ratio: float | None = None
    liquidity_quality_score: float | None = None
    payload_confidence: float | None = None
    degradation_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PromptControlBlock:
    response_mode: str = "grid_generation"
    must_return_fields: tuple[str, ...] = (
        "ticker",
        "timeframe",
        "direction",
        "tp",
        "sl",
        "grids",
        "price_up",
        "price_down",
        "conclusion",
    )
    language: str = "ru"
    max_rationale_sentences: int = 2
    style_hint: str = "short-trading-conclusion"
    risk_mode: str = "normal"
    no_capital_allocation: bool = True


@dataclass(frozen=True, slots=True)
class AlgoPayload:
    request_context: RequestContextBlock
    market_snapshot: MarketSnapshotBlock
    price_structure: PriceStructureBlock
    volatility: VolatilityBlock
    order_flow: OrderFlowBlock
    market_regime: MarketRegimeBlock
    support_resistance: SupportResistanceBlock
    grid_geometry_hints: GridGeometryHintsBlock
    grid_candidates: GridCandidatesBlock
    quality_trust: QualityTrustBlock
    prompt_control: PromptControlBlock = field(default_factory=PromptControlBlock)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PromptBuildResult:
    system_prompt: str
    user_prompt: str
    combined_prompt: str
    prompt_version: str
    payload_for_prompt: dict[str, Any]
    request_meta: dict[str, Any] = field(default_factory=dict)
    prompt_meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMRawResponse:
    ticker: str
    model_id: str
    prompt_version: str
    raw_text: str
    parsed_json: dict[str, Any] | None = None
    request_meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMValidationResult:
    is_valid: bool
    errors: tuple[dict[str, Any], ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()
    normalized_payload: dict[str, Any] | None = None
    summary: dict[str, Any] = field(default_factory=dict)
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FinalNormalizedResponse:
    ticker: str
    timeframe: str
    direction: str
    tp: float | None
    sl: float | None
    grids: int | None
    price_up: float | None
    price_down: float | None
    conclusion: str
    status: str
    confidence: float | None = None
    model_id: str | None = None
    prompt_version: str | None = None
    validator_summary: dict[str, Any] = field(default_factory=dict)
    trace: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Transitional / compatibility models from legacy deterministic runtime
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Tick preprocessing models
# ---------------------------------------------------------------------------


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
class PreprocessingDegradationThresholds:
    min_tick_count: int
    max_gap_ratio: float
    max_outlier_ratio: float
    min_side_quality_ratio: float


@dataclass(frozen=True, slots=True)
class PreprocessingDegradation:
    sparse_input: bool
    gap_heavy_sequence: bool
    outlier_noise_flags: bool
    low_side_quality: bool
    triggered_flags: tuple[str, ...]
    tick_count: int
    gap_ratio: float
    outlier_ratio: float
    side_quality_ratio: float
    thresholds: PreprocessingDegradationThresholds


@dataclass(frozen=True, slots=True)
class MarketSnapshotFeatures:
    last_price: float
    vwap_1m: float | None
    vwap_5m: float | None
    vwap_15m: float | None
    trade_count_1m: int
    trade_count_5m: int
    volume_1m: float
    volume_5m: float
    notional_1m: float
    notional_5m: float


@dataclass(frozen=True, slots=True)
class PriceStructureFeatures:
    open_1m: float | None
    high_1m: float | None
    low_1m: float | None
    close_1m: float | None
    open_5m: float | None
    high_5m: float | None
    low_5m: float | None
    close_5m: float | None
    local_high_15m: float | None
    local_low_15m: float | None
    range_width_1m: float | None
    range_width_5m: float | None
    close_position_in_1m_range: float | None
    close_position_in_5m_range: float | None
    distance_to_local_high: float | None
    distance_to_local_low: float | None


@dataclass(frozen=True, slots=True)
class VolatilityFeatures:
    atr_like_1m: float | None
    atr_like_5m: float | None
    realized_vol_1m: float | None
    realized_vol_5m: float | None
    return_std_1m: float | None
    return_std_5m: float | None
    volatility_regime_label: str
    volatility_percentile_1h: float | None
    impulse_size_last_move: float | None
    impulse_duration_seconds: float | None
    volatility_stability_score: float | None


@dataclass(frozen=True, slots=True)
class SupportResistanceFeatures:
    support_zone_low: float
    support_zone_high: float
    resistance_zone_low: float
    resistance_zone_high: float
    nearest_support_distance: float
    nearest_resistance_distance: float
    boundary_reaction_score: float
    bounce_frequency_score: float
    wick_rejection_score_upper: float
    wick_rejection_score_lower: float
    level_respect_score: float


@dataclass(frozen=True, slots=True)
class RegimeFeatures:
    market_regime_label: str
    regime_confidence: float
    trend_strength_score: float
    trend_persistence_score: float
    mean_reversion_score: float
    chop_score: float
    noise_score: float
    reversal_frequency_score: float


@dataclass(frozen=True, slots=True)
class OrderFlowFeatures:
    buy_volume_1m: float
    sell_volume_1m: float
    buy_volume_5m: float
    sell_volume_5m: float
    delta_1m: float
    delta_5m: float
    cumulative_delta_5m: float
    imbalance_ratio_1m: float | None
    imbalance_ratio_5m: float | None
    aggression_score_buy: float | None
    aggression_score_sell: float | None
    dominant_side: str
    order_flow_confidence: float


@dataclass(frozen=True, slots=True)
class QualityTrustFeatures:
    coverage_ratio: float
    largest_gap_seconds: float
    outlier_ratio: float
    liquidity_quality_score: float
    payload_confidence: float
    degradation_flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreprocessingFeatures:
    tick_count: int
    ohlcv_by_timeframe: dict[str, tuple[Candle, ...]]
    market_snapshot: MarketSnapshotFeatures
    price_structure: PriceStructureFeatures
    volatility: VolatilityFeatures
    order_flow: OrderFlowFeatures
    regime: RegimeFeatures
    support_resistance_features: SupportResistanceFeatures
    quality_trust: QualityTrustFeatures
    market_regime: MarketRegime
    volatility_regime: VolatilityRegime
    realized_vol: float
    support_resistance: SupportResistance
    entry_candidates: tuple[EntryCandidate, ...]


@dataclass(frozen=True, slots=True)
class FeatureExtractionResult:
    features: PreprocessingFeatures
    degradation: PreprocessingDegradation


@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    sanitized_ticks: tuple[Tick, ...]
    feature_extraction: FeatureExtractionResult

    @property
    def features(self) -> PreprocessingFeatures:
        return self.feature_extraction.features
