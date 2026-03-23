from __future__ import annotations

import json
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .machine_registry import MACHINE_REGISTRY, MachineSpec, get_machine_spec
from .runtime_contract import STATUS_ERROR, STATUS_PARTIAL, STATUS_READY, validate_response_payload

OBJECT_STATUS_READY = "ready"
OBJECT_STATUS_PARTIAL = "partial"
OBJECT_STATUS_BLOCKED = "blocked"
OBJECT_READINESS_STATUSES = (
    OBJECT_STATUS_READY,
    OBJECT_STATUS_PARTIAL,
    OBJECT_STATUS_BLOCKED,
)

BATCH_COMPLETENESS_COMPLETE = "complete"
BATCH_COMPLETENESS_INCOMPLETE = "incomplete"
BATCH_ACCEPTANCE_ACCEPTED = "accepted"
BATCH_ACCEPTANCE_DEGRADED = "degraded"
BATCH_ACCEPTANCE_BLOCKED = "blocked"

EXPECTED_BATCH_SIZE = len(MACHINE_REGISTRY)
FROZEN_MACHINE_ORDER: tuple[str, ...] = tuple(MACHINE_REGISTRY)
SYMBOL_OBJECT_REQUIRED_FIELDS: tuple[str, ...] = (
    "symbol",
    "strategy",
    "timeframe",
    "machine_id",
    "agent_id",
    "request_id",
    "requested_at",
    "generated_at",
    "status",
    "object_readiness",
    "response_contract_version",
    "summary",
    "meta",
    "features",
    "errors",
    "input_window",
    "source",
)
STORAGE_READY_ENVELOPE_FIELDS: tuple[str, ...] = (
    "symbol",
    "strategy",
    "timeframe",
    "machine_id",
    "agent_id",
    "request_id",
    "generated_at",
    "status",
    "summary",
    "meta",
    "features",
    "errors",
    "response_contract_version",
)
BATCH_ACCEPTANCE_RULES: Mapping[str, str] = {
    "complete": "A batch is complete only when all 12 frozen-registry machine ids are present exactly once for one symbol.",
    "degraded": "A complete batch may be degraded when one or more objects are partial, but no object is blocked.",
    "blocked": "A batch is blocked when it is incomplete, has duplicate machine ids, mixes symbols or contract versions, or contains blocked objects.",
    "handoff": "Only accepted or degraded complete batches are handoff-ready; blocked batches must not be sent downstream as normal storage handoff.",
}


@dataclass(frozen=True, slots=True)
class ObjectReadinessVerdict:
    status: str
    reasons: tuple[str, ...]
    storage_ready: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "storage_ready": self.storage_ready,
        }


@dataclass(frozen=True, slots=True)
class BenKimSymbolObject:
    symbol: str
    strategy: str
    timeframe: str
    machine_id: str
    agent_id: str
    request_id: str
    requested_at: str
    generated_at: str
    source: str
    status: str
    object_readiness: str
    response_contract_version: str
    input_window: Mapping[str, Any]
    summary: Mapping[str, Any]
    meta: Mapping[str, Any]
    features: Mapping[str, Any]
    errors: tuple[Mapping[str, Any], ...]
    packaging_issues: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "timeframe": self.timeframe,
            "machine_id": self.machine_id,
            "agent_id": self.agent_id,
            "request_id": self.request_id,
            "requested_at": self.requested_at,
            "generated_at": self.generated_at,
            "source": self.source,
            "status": self.status,
            "object_readiness": self.object_readiness,
            "response_contract_version": self.response_contract_version,
            "input_window": dict(self.input_window),
            "summary": dict(self.summary),
            "meta": dict(self.meta),
            "features": dict(self.features),
            "errors": [dict(error) for error in self.errors],
            "packaging_issues": list(self.packaging_issues),
        }


@dataclass(frozen=True, slots=True)
class BatchAcceptanceVerdict:
    symbol: str
    completeness: str
    acceptance_status: str
    expected_count: int
    actual_count: int
    missing_machine_ids: tuple[str, ...]
    duplicate_machine_ids: tuple[str, ...]
    partial_machine_ids: tuple[str, ...]
    blocked_machine_ids: tuple[str, ...]
    degraded_reasons: tuple[str, ...]

    @property
    def is_handoff_ready(self) -> bool:
        return self.completeness == BATCH_COMPLETENESS_COMPLETE and self.acceptance_status in {
            BATCH_ACCEPTANCE_ACCEPTED,
            BATCH_ACCEPTANCE_DEGRADED,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "completeness": self.completeness,
            "acceptance_status": self.acceptance_status,
            "expected_count": self.expected_count,
            "actual_count": self.actual_count,
            "missing_machine_ids": list(self.missing_machine_ids),
            "duplicate_machine_ids": list(self.duplicate_machine_ids),
            "partial_machine_ids": list(self.partial_machine_ids),
            "blocked_machine_ids": list(self.blocked_machine_ids),
            "degraded_reasons": list(self.degraded_reasons),
            "is_handoff_ready": self.is_handoff_ready,
        }


@dataclass(frozen=True, slots=True)
class BenKimBatch:
    symbol: str
    objects: tuple[BenKimSymbolObject, ...]
    acceptance: BatchAcceptanceVerdict

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "objects": [symbol_object.as_dict() for symbol_object in self.objects],
            "batch_acceptance": self.acceptance.as_dict(),
        }


@lru_cache(maxsize=1)
def load_symbol_object_schema() -> dict[str, Any]:
    schema_path = Path(__file__).with_name("BEN_KIM_SYMBOL_OBJECT_SCHEMA.json")
    return json.loads(schema_path.read_text())


def project_machine_response_to_symbol_object(machine_response: Mapping[str, Any]) -> BenKimSymbolObject:
    strategy = _required_string(machine_response, "strategy")
    timeframe = _required_string(machine_response, "timeframe")
    machine_spec = get_machine_spec(strategy, timeframe)
    machine_id = _extract_machine_id(machine_response, machine_spec)

    packaging_issues = [
        *validate_response_payload(machine_response),
        *validate_machine_response_identity(machine_response, machine_spec),
    ]

    symbol_object = BenKimSymbolObject(
        symbol=_required_string(machine_response, "symbol"),
        strategy=strategy,
        timeframe=timeframe,
        machine_id=machine_id,
        agent_id=_required_string(machine_response, "agent_id"),
        request_id=_required_string(machine_response, "request_id"),
        requested_at=_required_string(machine_response, "requested_at"),
        generated_at=_required_string(machine_response, "generated_at"),
        source=_required_string(machine_response, "source"),
        status=_required_string(machine_response, "status"),
        object_readiness=OBJECT_STATUS_BLOCKED,
        response_contract_version=_required_string(machine_response, "response_contract_version"),
        input_window=_required_mapping(machine_response, "input_window"),
        summary=_required_mapping(machine_response, "summary"),
        meta=_required_mapping(machine_response, "meta"),
        features=_required_mapping(machine_response, "features"),
        errors=_coerce_errors(machine_response.get("errors", ())),
        packaging_issues=tuple(packaging_issues),
    )
    verdict = evaluate_object_readiness(symbol_object)
    return replace(symbol_object, object_readiness=verdict.status)


def assemble_symbol_batch(symbol: str, machine_responses: Iterable[Mapping[str, Any]]) -> BenKimBatch:
    objects = tuple(project_machine_response_to_symbol_object(response) for response in machine_responses)
    acceptance = evaluate_batch_acceptance(symbol, objects)
    ordered_objects = _order_symbol_objects(objects)
    return BenKimBatch(symbol=symbol, objects=ordered_objects, acceptance=acceptance)


def evaluate_object_readiness(symbol_object: BenKimSymbolObject) -> ObjectReadinessVerdict:
    issues = list(symbol_object.packaging_issues)
    meta = symbol_object.meta

    if symbol_object.status not in {STATUS_READY, STATUS_PARTIAL, STATUS_ERROR}:
        issues.append(f"Unsupported runtime status: {symbol_object.status}")
    if symbol_object.object_readiness not in OBJECT_READINESS_STATUSES:
        # projection initializes as blocked, so this branch matters only for external objects.
        pass
    if meta.get("machine_id") != symbol_object.machine_id:
        issues.append("meta.machine_id does not match top-level machine_id")
    if meta.get("is_partial") is True and symbol_object.status != STATUS_PARTIAL:
        issues.append("meta.is_partial=true requires status=partial")
    if symbol_object.status == STATUS_PARTIAL and not meta.get("partial_reason"):
        issues.append("partial response requires meta.partial_reason")
    if symbol_object.status == STATUS_READY and meta.get("is_partial"):
        issues.append("ready response cannot carry meta.is_partial=true")
    if symbol_object.status == STATUS_ERROR and not symbol_object.errors:
        issues.append("error response requires at least one error entry")

    missing_storage_fields = [
        field for field in STORAGE_READY_ENVELOPE_FIELDS if _is_missing_storage_field(field, symbol_object)
    ]
    if missing_storage_fields:
        issues.append(f"Missing storage envelope fields: {', '.join(missing_storage_fields)}")

    if issues:
        return ObjectReadinessVerdict(
            status=OBJECT_STATUS_BLOCKED,
            reasons=tuple(issues),
            storage_ready=False,
        )
    if symbol_object.status == STATUS_PARTIAL:
        return ObjectReadinessVerdict(
            status=OBJECT_STATUS_PARTIAL,
            reasons=("runtime_status_partial",),
            storage_ready=True,
        )
    if symbol_object.status == STATUS_ERROR:
        return ObjectReadinessVerdict(
            status=OBJECT_STATUS_BLOCKED,
            reasons=("runtime_status_error",),
            storage_ready=False,
        )
    return ObjectReadinessVerdict(
        status=OBJECT_STATUS_READY,
        reasons=(),
        storage_ready=True,
    )


def evaluate_batch_acceptance(symbol: str, symbol_objects: Sequence[BenKimSymbolObject]) -> BatchAcceptanceVerdict:
    actual_count = len(symbol_objects)
    machine_ids = [symbol_object.machine_id for symbol_object in symbol_objects]
    duplicate_machine_ids = tuple(sorted({machine_id for machine_id in machine_ids if machine_ids.count(machine_id) > 1}))
    present_machine_ids = set(machine_ids)
    missing_machine_ids = tuple(machine_id for machine_id in FROZEN_MACHINE_ORDER if machine_id not in present_machine_ids)

    degraded_reasons: list[str] = []
    blocked_machine_ids = tuple(
        symbol_object.machine_id
        for symbol_object in symbol_objects
        if evaluate_object_readiness(symbol_object).status == OBJECT_STATUS_BLOCKED
    )
    partial_machine_ids = tuple(
        symbol_object.machine_id
        for symbol_object in symbol_objects
        if evaluate_object_readiness(symbol_object).status == OBJECT_STATUS_PARTIAL
    )

    symbol_mismatch_ids = tuple(
        symbol_object.machine_id for symbol_object in symbol_objects if symbol_object.symbol != symbol
    )
    if symbol_mismatch_ids:
        degraded_reasons.append("batch_contains_foreign_symbol_objects")

    response_versions = {symbol_object.response_contract_version for symbol_object in symbol_objects}
    if len(response_versions) > 1:
        degraded_reasons.append("response_contract_version_mismatch")

    source_versions = {symbol_object.meta.get("source_contract_version") for symbol_object in symbol_objects}
    if len(source_versions) > 1:
        degraded_reasons.append("source_contract_version_mismatch")

    completeness = (
        BATCH_COMPLETENESS_COMPLETE
        if actual_count == EXPECTED_BATCH_SIZE and not missing_machine_ids and not duplicate_machine_ids
        else BATCH_COMPLETENESS_INCOMPLETE
    )

    if completeness == BATCH_COMPLETENESS_INCOMPLETE:
        degraded_reasons.append("incomplete_12_object_batch")
    if duplicate_machine_ids:
        degraded_reasons.append("duplicate_machine_ids")

    if blocked_machine_ids or symbol_mismatch_ids or len(response_versions) > 1 or len(source_versions) > 1:
        acceptance_status = BATCH_ACCEPTANCE_BLOCKED
    elif partial_machine_ids:
        acceptance_status = BATCH_ACCEPTANCE_DEGRADED
        degraded_reasons.append("contains_partial_objects")
    elif completeness == BATCH_COMPLETENESS_INCOMPLETE:
        acceptance_status = BATCH_ACCEPTANCE_BLOCKED
    else:
        acceptance_status = BATCH_ACCEPTANCE_ACCEPTED

    return BatchAcceptanceVerdict(
        symbol=symbol,
        completeness=completeness,
        acceptance_status=acceptance_status,
        expected_count=EXPECTED_BATCH_SIZE,
        actual_count=actual_count,
        missing_machine_ids=missing_machine_ids,
        duplicate_machine_ids=duplicate_machine_ids,
        partial_machine_ids=partial_machine_ids,
        blocked_machine_ids=blocked_machine_ids,
        degraded_reasons=tuple(dict.fromkeys(degraded_reasons)),
    )


def validate_machine_response_identity(machine_response: Mapping[str, Any], machine_spec: MachineSpec) -> list[str]:
    issues: list[str] = []
    if machine_response.get("agent_id") != machine_spec.agent_id:
        issues.append("agent_id does not match frozen registry")
    if machine_response.get("strategy") != machine_spec.strategy:
        issues.append("strategy does not match frozen registry")
    if machine_response.get("timeframe") != machine_spec.timeframe:
        issues.append("timeframe does not match frozen registry")
    if _extract_machine_id(machine_response, machine_spec) != machine_spec.machine_id:
        issues.append("machine_id does not match frozen registry")
    if not isinstance(machine_response.get("meta"), Mapping):
        issues.append("meta must be an object")
        return issues
    if machine_response["meta"].get("api_key_id") != machine_spec.api_key_id:
        issues.append("meta.api_key_id does not match frozen registry")
    return issues


def validate_symbol_object_payload(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in SYMBOL_OBJECT_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    if payload.get("object_readiness") not in OBJECT_READINESS_STATUSES:
        errors.append("object_readiness must be ready, partial, or blocked")
    if payload.get("status") == STATUS_PARTIAL and not payload.get("meta", {}).get("partial_reason"):
        errors.append("partial object requires meta.partial_reason")
    if payload.get("status") == STATUS_ERROR and not payload.get("errors"):
        errors.append("error object requires non-empty errors")
    return errors


def _order_symbol_objects(symbol_objects: Sequence[BenKimSymbolObject]) -> tuple[BenKimSymbolObject, ...]:
    object_lookup = {symbol_object.machine_id: symbol_object for symbol_object in symbol_objects}
    ordered = [object_lookup[machine_id] for machine_id in FROZEN_MACHINE_ORDER if machine_id in object_lookup]
    leftovers = [symbol_object for symbol_object in symbol_objects if symbol_object.machine_id not in FROZEN_MACHINE_ORDER]
    ordered.extend(sorted(leftovers, key=lambda symbol_object: symbol_object.machine_id))
    return tuple(ordered)


def _extract_machine_id(machine_response: Mapping[str, Any], machine_spec: MachineSpec) -> str:
    meta = machine_response.get("meta")
    if isinstance(meta, Mapping) and isinstance(meta.get("machine_id"), str) and meta["machine_id"]:
        return meta["machine_id"]
    return machine_spec.machine_id


def _coerce_errors(errors: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(errors, Sequence) or isinstance(errors, (str, bytes, bytearray)):
        return ()
    normalized_errors: list[Mapping[str, Any]] = []
    for error in errors:
        if isinstance(error, Mapping):
            normalized_errors.append(dict(error))
    return tuple(normalized_errors)


def _required_mapping(payload: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return dict(value)


def _required_string(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _is_missing_storage_field(field: str, symbol_object: BenKimSymbolObject) -> bool:
    value = getattr(symbol_object, field, None)
    if isinstance(value, str):
        return value == ""
    return value is None


__all__ = [
    "BATCH_ACCEPTANCE_ACCEPTED",
    "BATCH_ACCEPTANCE_BLOCKED",
    "BATCH_ACCEPTANCE_DEGRADED",
    "BATCH_ACCEPTANCE_RULES",
    "BATCH_COMPLETENESS_COMPLETE",
    "BATCH_COMPLETENESS_INCOMPLETE",
    "BenKimBatch",
    "BenKimSymbolObject",
    "BatchAcceptanceVerdict",
    "EXPECTED_BATCH_SIZE",
    "FROZEN_MACHINE_ORDER",
    "OBJECT_STATUS_BLOCKED",
    "OBJECT_STATUS_PARTIAL",
    "OBJECT_STATUS_READY",
    "ObjectReadinessVerdict",
    "STORAGE_READY_ENVELOPE_FIELDS",
    "SYMBOL_OBJECT_REQUIRED_FIELDS",
    "assemble_symbol_batch",
    "evaluate_batch_acceptance",
    "evaluate_object_readiness",
    "load_symbol_object_schema",
    "project_machine_response_to_symbol_object",
    "validate_machine_response_identity",
    "validate_symbol_object_payload",
]
