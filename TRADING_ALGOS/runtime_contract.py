from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
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

ERROR_SCOPE_INPUT = "input"
ERROR_SCOPE_READ = "read"
ERROR_SCOPE_NORMALIZATION = "normalization"
ERROR_SCOPE_FEATURES = "features"
ERROR_SCOPE_OUTPUT = "output"
ERROR_SCOPE_TRANSPORT = "transport"
ERROR_SCOPES = (
    ERROR_SCOPE_INPUT,
    ERROR_SCOPE_READ,
    ERROR_SCOPE_NORMALIZATION,
    ERROR_SCOPE_FEATURES,
    ERROR_SCOPE_OUTPUT,
    ERROR_SCOPE_TRANSPORT,
)

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


SANCTIONED_FAILURE_TEMPLATES: tuple[RuntimeErrorInfo, ...] = (
    RuntimeErrorInfo("REQUEST_VALIDATION_FAILED", "Request schema validation failed.", "error", ERROR_SCOPE_INPUT, False),
    RuntimeErrorInfo("RETENTION_WINDOW_TOO_SHALLOW", "Requested window exceeds retained history.", "warning", ERROR_SCOPE_READ, False),
    RuntimeErrorInfo("PAGINATION_DRIFT", "Tick pagination did not produce a complete read.", "warning", ERROR_SCOPE_READ, True),
    RuntimeErrorInfo("READ_TIMEOUT", "Upstream read timed out before the requested window was fetched.", "warning", ERROR_SCOPE_READ, True),
    RuntimeErrorInfo("INPUT_GAP_DETECTED", "Gap-heavy input window detected.", "warning", ERROR_SCOPE_READ, True),
    RuntimeErrorInfo("EMPTY_WINDOW", "No ticks were available inside the requested window.", "warning", ERROR_SCOPE_READ, False),
    RuntimeErrorInfo("NORMALIZATION_FAILED", "Shared tick normalizer failed.", "error", ERROR_SCOPE_NORMALIZATION, True),
    RuntimeErrorInfo("INSUFFICIENT_WARMUP", "Not enough candles to compute strategy safely.", "warning", ERROR_SCOPE_FEATURES, False),
    RuntimeErrorInfo("FEATURE_ENGINE_FAILED", "Shared tick-to-features engine or strategy compute failed.", "error", ERROR_SCOPE_FEATURES, True),
    RuntimeErrorInfo("OUTPUT_SCHEMA_FAILED", "Response did not satisfy the shared contract.", "error", ERROR_SCOPE_OUTPUT, False),
    RuntimeErrorInfo("TRANSPORT_FAILED", "Transport layer failed to deliver the response.", "error", ERROR_SCOPE_TRANSPORT, True),
)

SHARED_FAILURE_LOOKUP: Mapping[str, RuntimeErrorInfo] = {error.code: error for error in SANCTIONED_FAILURE_TEMPLATES}

FAILURE_MODE_MATRIX: Mapping[str, tuple[RuntimeErrorInfo, ...]] = {
    machine_id: SANCTIONED_FAILURE_TEMPLATES
    for machine_id in MACHINE_REGISTRY
}

FAILURE_MODE_LOOKUP: Mapping[str, Mapping[str, RuntimeErrorInfo]] = {
    machine_id: {error.code: error for error in errors}
    for machine_id, errors in FAILURE_MODE_MATRIX.items()
}


@lru_cache(maxsize=1)
def load_response_schema() -> dict[str, Any]:
    schema_path = Path(__file__).with_name("SUBAGENT_RESPONSE_FORMAT.json")
    return json.loads(schema_path.read_text())


def build_shared_error(code: str, *, message: str | None = None) -> RuntimeErrorInfo:
    template = SHARED_FAILURE_LOOKUP[code]
    if message is None:
        return template
    return RuntimeErrorInfo(code=template.code, message=message, severity=template.severity, scope=template.scope, retryable=template.retryable)


def build_failure_error(machine_id: str, code: str, *, message: str | None = None) -> RuntimeErrorInfo:
    FAILURE_MODE_LOOKUP[machine_id][code]
    return build_shared_error(code, message=message)


def validate_response_payload(payload: Mapping[str, Any]) -> list[str]:
    schema = load_response_schema()
    return _validate_schema_node(payload, schema, schema, path="$")



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
                build_shared_error(
                    "REQUEST_VALIDATION_FAILED",
                    message=f"Missing required field: {field}",
                )
            )
    if errors:
        return errors

    if request["strategy"] != machine_spec.strategy:
        errors.append(build_shared_error("REQUEST_VALIDATION_FAILED", message="Request strategy does not match machine strategy."))
    if request["timeframe"] != machine_spec.timeframe:
        errors.append(build_shared_error("REQUEST_VALIDATION_FAILED", message="Request timeframe does not match machine timeframe."))
    if request["agent_id"] != machine_spec.agent_id:
        errors.append(build_shared_error("REQUEST_VALIDATION_FAILED", message="Request agent_id does not match frozen registry."))

    input_window = request.get("input_window", {})
    if not isinstance(input_window, Mapping) or "from" not in input_window or "to" not in input_window:
        errors.append(build_shared_error("REQUEST_VALIDATION_FAILED", message="input_window must contain from/to."))
    return errors


def assess_partial_window(normalization: NormalizationResult, *, strict_mode: bool = False) -> tuple[str, list[RuntimeErrorInfo]]:
    errors: list[RuntimeErrorInfo] = []
    if not normalization.is_partial:
        return STATUS_READY, errors

    for reason in normalization.partial_reasons:
        if reason == PARTIAL_REASON_RETENTION:
            errors.append(build_shared_error("RETENTION_WINDOW_TOO_SHALLOW", message="Requested window was truncated by retention."))
        elif reason == PARTIAL_REASON_PAGINATION:
            errors.append(build_shared_error("PAGINATION_DRIFT", message="Pagination did not complete for the requested window."))
        elif reason == PARTIAL_REASON_GAP_HEAVY:
            errors.append(build_shared_error("INPUT_GAP_DETECTED", message="Gap-heavy input window detected."))
        elif reason == PARTIAL_REASON_EMPTY_WINDOW:
            errors.append(build_shared_error("EMPTY_WINDOW", message="No ticks were available inside the requested window."))

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


def _validate_schema_node(value: Any, schema: Mapping[str, Any], root_schema: Mapping[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []

    if "$ref" in schema:
        ref = str(schema["$ref"])
        resolved = _resolve_ref(root_schema, ref)
        return _validate_schema_node(value, resolved, root_schema, path=path)

    schema_type = schema.get("type")
    allowed_types = schema_type if isinstance(schema_type, list) else ([schema_type] if schema_type else [])
    if allowed_types and not _matches_any_type(value, allowed_types):
        expected = "/".join(str(item) for item in allowed_types)
        return [f"{path}: expected type {expected}"]

    if value is None:
        return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value {value!r} does not match const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} is not in enum {schema['enum']!r}")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path}: string is shorter than minLength={min_length}")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: invalid date-time format")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            errors.append(f"{path}: value {value} is below minimum={minimum}")
        if maximum is not None and value > maximum:
            errors.append(f"{path}: value {value} is above maximum={maximum}")

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                errors.append(f"{path}: missing required property {field!r}")
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            for field in sorted(extra):
                errors.append(f"{path}: unexpected property {field!r}")
        for field, field_value in value.items():
            child_schema = properties.get(field)
            if child_schema is None:
                if isinstance(schema.get("additionalProperties"), Mapping):
                    child_schema = schema["additionalProperties"]
                else:
                    continue
            errors.extend(_validate_schema_node(field_value, child_schema, root_schema, path=f"{path}.{field}"))

    if isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                errors.extend(_validate_schema_node(item, item_schema, root_schema, path=f"{path}[{index}]"))
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: array has fewer than minItems={min_items}")

    for branch in schema.get("allOf", []):
        condition = branch.get("if")
        consequence = branch.get("then")
        if isinstance(condition, Mapping) and isinstance(consequence, Mapping):
            if not _validate_schema_node(value, condition, root_schema, path=path):
                errors.extend(_validate_schema_node(value, consequence, root_schema, path=path))

    return errors


def _matches_any_type(value: Any, allowed_types: list[Any]) -> bool:
    return any(_matches_type(value, allowed_type) for allowed_type in allowed_types)


def _matches_type(value: Any, allowed_type: Any) -> bool:
    return {
        "object": lambda candidate: isinstance(candidate, Mapping),
        "array": lambda candidate: isinstance(candidate, list),
        "string": lambda candidate: isinstance(candidate, str),
        "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
        "number": lambda candidate: isinstance(candidate, (int, float)) and not isinstance(candidate, bool),
        "boolean": lambda candidate: isinstance(candidate, bool),
        "null": lambda candidate: candidate is None,
    }.get(allowed_type, lambda candidate: True)(value)


def _resolve_ref(root_schema: Mapping[str, Any], ref: str) -> Mapping[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Unsupported schema ref: {ref}")
    node: Any = root_schema
    for part in ref[2:].split("/"):
        node = node[part]
    if not isinstance(node, Mapping):
        raise TypeError(f"Schema ref {ref} did not resolve to a mapping")
    return node
