from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from .models import MaffiOutput

_OUTPUT_ENVELOPE_KEYS = (
    "schema_version",
    "generated_at_utc",
    "symbol",
    "decision",
    "confidence",
    "selected_entry",
    "tp",
    "sl",
    "input_quality_status",
    "reject_reason",
    "rationale",
    "validation_summary",
    "decision_summary",
    "decision_trace",
)


def normalize_rationale(rationale: Iterable[Any] | None) -> list[str]:
    if rationale is None:
        return []

    normalized: list[str] = []
    for item in rationale:
        text = " ".join(str(item).strip().split())
        if text:
            normalized.append(text)
    return normalized


def normalize_decision_trace(decision_trace: Mapping[str, Any] | None) -> dict[str, Any]:
    if decision_trace is None:
        return {}
    return _normalize_mapping(decision_trace)


def maffi_output_to_dict(output: MaffiOutput) -> dict[str, Any]:
    serialized: dict[str, Any] = {
        "schema_version": output.schema_version,
        "generated_at_utc": output.generated_at_utc,
        "symbol": output.symbol,
        "decision": output.decision.value,
        "confidence": output.confidence,
        "selected_entry": output.selected_entry,
        "tp": output.tp,
        "sl": output.sl,
        "input_quality_status": output.input_quality_status.value,
        "reject_reason": output.reject_reason,
        "rationale": normalize_rationale(output.rationale),
        "validation_summary": _normalize_value(output.validation_summary),
        "decision_summary": _normalize_value(output.decision_summary),
        "decision_trace": normalize_decision_trace(output.decision_trace),
    }
    return {key: serialized[key] for key in _OUTPUT_ENVELOPE_KEYS}


def maffi_output_to_json(output: MaffiOutput, *, indent: int | None = None) -> str:
    return json.dumps(maffi_output_to_dict(output), ensure_ascii=False, separators=(",", ":"), indent=indent)


def _normalize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(k): _normalize_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}


def _normalize_sequence(value: Iterable[Any]) -> list[Any]:
    return [_normalize_value(item) for item in value]


def _normalize_value(value: Any) -> Any:
    if is_dataclass(value):
        return _normalize_value(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return _normalize_mapping(value)
    if isinstance(value, (list, tuple)):
        return _normalize_sequence(value)
    return value
