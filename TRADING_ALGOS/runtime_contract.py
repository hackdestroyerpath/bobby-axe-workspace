from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .common.tick_normalizer import (
    PARTIAL_REASON_EMPTY_WINDOW,
    PARTIAL_REASON_GAP_HEAVY,
    PARTIAL_REASON_PAGINATION,
    PARTIAL_REASON_RETENTION,
    NormalizationResult,
)
from .machine_registry import MACHINE_REGISTRY, MachineSpec, WarmupSpec

STATUS_READY = "ready"
STATUS_PARTIAL = "partial"
STATUS_ERROR = "error"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

PARTIAL_TO_ERROR_REASONS = frozenset({PARTIAL_REASON_EMPTY_WINDOW})
CAN_COMPUTE_ON_PARTIAL_REASONS = frozenset(
    {
        PARTIAL_REASON_RETENTION,
        PARTIAL_REASON_PAGINATION,
        PARTIAL_REASON_GAP_HEAVY,
    }
)

REQUEST_REQUIRED_FIELDS = (
    "request_id",
    "agent_id",
    "strategy",
    "timeframe",
    "symbol",
    "source",
    "requested_at",
    "input_window",
    "response_contract_version",
    "source_contract_version",
)


@dataclass(frozen=True, slots=True)
class RuntimeErrorInfo:
    code: str
    message: str
    severity: str
    scope: str
    retryable: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "scope": self.scope,
            "retryable": self.retryable,
        }


@dataclass(frozen=True, slots=True)
class WarmupAssessment:
    status: str
    has_sufficient_warmup: bool
    available_candles: int
    minimum_required_candles: int
    note: str | None


@dataclass(frozen=True, slots=True)
class SummaryPolicy:
    state_map: Mapping[str, str]
    strength_map: Mapping[str, str]
    default_confidence: str
    quality_confidence_caps: Mapping[str, str]


SUMMARY_POLICIES: Mapping[str, SummaryPolicy] = {
    "RSI_MACD": SummaryPolicy(
        state_map={"bullish": "bullish", "bearish": "bearish", "mixed": "mixed"},
        strength_map={"strong": "strong", "medium": "medium", "weak": "weak"},
        default_confidence=CONFIDENCE_MEDIUM,
        quality_confidence_caps={
            PARTIAL_REASON_RETENTION: CONFIDENCE_LOW,
            PARTIAL_REASON_PAGINATION: CONFIDENCE_LOW,
            PARTIAL_REASON_GAP_HEAVY: CONFIDENCE_LOW,
        },
    ),
    "LEVELS_FIBO_HV": SummaryPolicy(
        state_map={"bullish": "bullish", "bearish": "bearish", "mixed": "mixed", "range": "mixed"},
        strength_map={"strong": "strong", "medium": "medium", "weak": "weak"},
        default_confidence=CONFIDENCE_MEDIUM,
        quality_confidence_caps={
            PARTIAL_REASON_RETENTION: CONFIDENCE_LOW,
            PARTIAL_REASON_PAGINATION: CONFIDENCE_LOW,
            PARTIAL_REASON_GAP_HEAVY: CONFIDENCE_LOW,
        },
    ),
    "VOLUME": SummaryPolicy(
        state_map={"buyers": "bullish", "sellers": "bearish", "mixed": "mixed"},
        strength_map={"strong": "strong", "medium": "medium", "weak": "weak"},
        default_confidence=CONFIDENCE_MEDIUM,
        quality_confidence_caps={
            PARTIAL_REASON_RETENTION: CONFIDENCE_LOW,
            PARTIAL_REASON_PAGINATION: CONFIDENCE_LOW,
            PARTIAL_REASON_GAP_HEAVY: CONFIDENCE_LOW,
        },
    ),
    "ELLIOTT": SummaryPolicy(
        state_map={"up": "bullish", "down": "bearish", "flat": "mixed", "unclear": "mixed"},
        strength_map={"strong": "medium", "medium": "medium", "weak": "weak", "low": "weak"},
        default_confidence=CONFIDENCE_LOW,
        quality_confidence_caps={
            PARTIAL_REASON_RETENTION: CONFIDENCE_LOW,
            PARTIAL_REASON_PAGINATION: CONFIDENCE_LOW,
            PARTIAL_REASON_GAP_HEAVY: CONFIDENCE_LOW,
        },
    ),
}


FAILURE_MODE_MATRIX: Mapping[str, tuple[RuntimeErrorInfo, ...]] = {
    machine_id: (
        RuntimeErrorInfo("REQUEST_VALIDATION_FAILED", "Request schema validation failed.", "error", "input", False),
        RuntimeErrorInfo("RETENTION_WINDOW_TOO_SHALLOW", "Requested window exceeds retained history.", "warning", "input", False),
        RuntimeErrorInfo("PAGINATION_DRIFT", "Tick pagination did not produce a complete read.", "warning", "read", True),
        RuntimeErrorInfo("NORMALIZATION_FAILED", "Shared tick normalizer failed.", "error", "normalization", True),
        RuntimeErrorInfo("INSUFFICIENT_WARMUP", "Not enough candles to compute strategy safely.", "warning", "features", False),
        RuntimeErrorInfo("FEATURE_ENGINE_FAILED", "Shared tick-to-features engine failed.", "error", "features", True),
        RuntimeErrorInfo("OUTPUT_SCHEMA_FAILED", "Response did not satisfy the shared contract.", "error", "output", False),
        RuntimeErrorInfo("TRANSPORT_FAILED", "Transport layer failed to deliver the response.", "error", "transport", True),
    )
    for machine_id in MACHINE_REGISTRY
}


BEN_KIM_ORCHESTRATION_EXPECTATIONS = {
    "addressing": "Address machines by machine_id/agent_id from the frozen registry only.",
    "ready_partial_error": "Treat ready as aggregatable, partial as degraded-but-readable, error as non-aggregatable.",
    "retry_policy": "Retry only failures marked retryable=true; do not retry insufficient warmup or empty_window failures.",
    "aggregation": "Aggregate same-strategy 1m/5m/60m outputs only when response_contract_version matches and statuses are ready/partial.",
    "degraded_handling": "Discard or heavily downweight low-confidence Elliott packets and any packet with partial_reason=empty_window.",
    "traceability": "Every response must carry response_contract_version at the top level and source_contract_version/build_version/machine_id/api_key_id in traceability fields.",
    "timeframe_alignment": "Read 60m as context anchor, 5m as intraday confirmation, 1m as tactical timing layer.",
}


def validate_request(request: Mapping[str, Any], machine_spec: MachineSpec) -> list[RuntimeErrorInfo]:
    errors: list[RuntimeErrorInfo] = []
    for field in REQUEST_REQUIRED_FIELDS:
        if field not in request:
            errors.append(
                RuntimeErrorInfo(
                    code="REQUEST_VALIDATION_FAILED",
                    message=f"Missing required field: {field}",
                    severity="error",
                    scope="input",
                    retryable=False,
                )
            )
    if errors:
        return errors

    if request["strategy"] != machine_spec.strategy:
        errors.append(RuntimeErrorInfo("REQUEST_VALIDATION_FAILED", "Request strategy does not match machine strategy.", "error", "input", False))
    if request["timeframe"] != machine_spec.timeframe:
        errors.append(RuntimeErrorInfo("REQUEST_VALIDATION_FAILED", "Request timeframe does not match machine timeframe.", "error", "input", False))
    if request["agent_id"] != machine_spec.agent_id:
        errors.append(RuntimeErrorInfo("REQUEST_VALIDATION_FAILED", "Request agent_id does not match frozen registry.", "error", "input", False))

    input_window = request.get("input_window", {})
    if not isinstance(input_window, Mapping) or "from" not in input_window or "to" not in input_window:
        errors.append(RuntimeErrorInfo("REQUEST_VALIDATION_FAILED", "input_window must contain from/to.", "error", "input", False))
    return errors


def assess_partial_window(normalization: NormalizationResult, *, strict_mode: bool = False) -> tuple[str, list[RuntimeErrorInfo]]:
    errors: list[RuntimeErrorInfo] = []
    if not normalization.is_partial:
        return STATUS_READY, errors

    for reason in normalization.partial_reasons:
        if reason == PARTIAL_REASON_RETENTION:
            errors.append(RuntimeErrorInfo("RETENTION_WINDOW_TOO_SHALLOW", "Requested window was truncated by retention.", "warning", "input", False))
        elif reason == PARTIAL_REASON_PAGINATION:
            errors.append(RuntimeErrorInfo("PAGINATION_DRIFT", "Pagination did not complete for the requested window.", "warning", "read", True))
        elif reason == PARTIAL_REASON_GAP_HEAVY:
            errors.append(RuntimeErrorInfo("INPUT_GAP_DETECTED", "Gap-heavy input window detected.", "warning", "input", True))
        elif reason == PARTIAL_REASON_EMPTY_WINDOW:
            errors.append(RuntimeErrorInfo("EMPTY_WINDOW", "No ticks were available inside the requested window.", "warning", "input", False))

    if strict_mode or any(reason in PARTIAL_TO_ERROR_REASONS for reason in normalization.partial_reasons):
        return STATUS_ERROR, errors
    return STATUS_PARTIAL, errors


def assess_warmup(candle_count: int, warmup: WarmupSpec, *, strict_mode: bool = False) -> WarmupAssessment:
    if candle_count >= warmup.minimum_valid_candles:
        return WarmupAssessment(STATUS_READY, True, candle_count, warmup.minimum_valid_candles, None)

    note = (
        f"Only {candle_count} candles available; requires {warmup.minimum_valid_candles} candles for valid output."
    )
    status = STATUS_ERROR if strict_mode or warmup.insufficient_warmup_status == STATUS_ERROR else STATUS_PARTIAL
    return WarmupAssessment(status, False, candle_count, warmup.minimum_valid_candles, note)


def build_summary(strategy: str, feature_payload: Mapping[str, Any], quality_reasons: tuple[str, ...]) -> dict[str, Any]:
    policy = SUMMARY_POLICIES[strategy]
    state_seed = str(feature_payload.get("summary_state") or feature_payload.get("momentum_state") or feature_payload.get("pressure_side") or feature_payload.get("trend_state") or "mixed")
    strength_seed = str(feature_payload.get("summary_strength") or feature_payload.get("momentum_strength") or feature_payload.get("flow_strength") or feature_payload.get("current_leg_strength") or "weak")

    confidence = policy.default_confidence
    confidence_rank = {CONFIDENCE_LOW: 0, CONFIDENCE_MEDIUM: 1, CONFIDENCE_HIGH: 2}
    for reason in quality_reasons:
        cap = policy.quality_confidence_caps.get(reason)
        if cap is not None and confidence_rank[cap] < confidence_rank[confidence]:
            confidence = cap

    note_parts = []
    if feature_payload.get("summary_note"):
        note_parts.append(str(feature_payload["summary_note"]))
    if quality_reasons:
        note_parts.append(f"quality={'/'.join(quality_reasons)}")

    return {
        "state": policy.state_map.get(state_seed, "mixed"),
        "strength": policy.strength_map.get(strength_seed, "weak"),
        "confidence": confidence,
        "note": "; ".join(note_parts) if note_parts else "shared runtime summary",
    }


def build_meta(
    *,
    machine_spec: MachineSpec,
    request: Mapping[str, Any],
    normalization: NormalizationResult,
    build_version: str,
) -> dict[str, Any]:
    return {
        "data_points": normalization.tick_count,
        "coverage_ratio": normalization.coverage_ratio,
        "is_partial": normalization.is_partial,
        "partial_reason": normalization.partial_reason,
        "source_contract_version": request["source_contract_version"],
        "build_version": build_version,
        "api_key_id": machine_spec.api_key_id,
        "machine_id": machine_spec.machine_id,
    }


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def recommended_window_by_machine() -> Mapping[str, timedelta]:
    return {machine_id: spec.warmup.recommended_window for machine_id, spec in MACHINE_REGISTRY.items()}
