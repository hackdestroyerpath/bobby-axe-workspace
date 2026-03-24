from __future__ import annotations

from datetime import datetime
from typing import Any

from .enums import DominantSide, MarketRegime, QualityStatus, VolatilityRegime
from .models import ValidationIssue, ValidationResult

_REQUIRED_FIELDS = {
    "schema_version",
    "symbol",
    "generated_at_utc",
    "source",
    "input_quality_status",
    "market_regime",
    "volatility_regime",
    "dominant_side",
    "long_score",
    "short_score",
    "reject_score",
    "confidence_hint",
    "entry_candidates",
    "support_level",
    "resistance_level",
    "last_price",
    "atr",
}


def validate_payload(payload: dict[str, Any]) -> ValidationResult:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    for field in sorted(_REQUIRED_FIELDS):
        if field not in payload:
            errors.append(ValidationIssue(field=field, message="missing required field", severity="error"))

    if errors:
        return ValidationResult(is_valid=False, errors=tuple(errors), warnings=tuple(warnings))

    _validate_iso(payload, "generated_at_utc", errors)
    _validate_enum(payload, "input_quality_status", QualityStatus, errors)
    _validate_enum(payload, "market_regime", MarketRegime, errors)
    _validate_enum(payload, "volatility_regime", VolatilityRegime, errors)
    _validate_enum(payload, "dominant_side", DominantSide, errors)

    for field in ("long_score", "short_score", "reject_score"):
        _validate_range(payload, field, 0.0, 100.0, errors)

    _validate_range(payload, "confidence_hint", 0.0, 1.0, errors)

    candidates = payload["entry_candidates"]
    if not isinstance(candidates, (list, tuple)) or not candidates:
        errors.append(ValidationIssue(field="entry_candidates", message="must be non-empty list/tuple", severity="error"))
    else:
        for idx, candidate in enumerate(candidates):
            if not isinstance(candidate, (int, float)):
                errors.append(ValidationIssue(field=f"entry_candidates[{idx}]", message="must be numeric", severity="error"))

    support = payload["support_level"]
    resistance = payload["resistance_level"]
    price = payload["last_price"]
    atr = payload["atr"]
    for numeric_field, value in (("support_level", support), ("resistance_level", resistance), ("last_price", price), ("atr", atr)):
        if not isinstance(value, (int, float)):
            errors.append(ValidationIssue(field=numeric_field, message="must be numeric", severity="error"))

    if isinstance(support, (int, float)) and isinstance(resistance, (int, float)) and support >= resistance:
        errors.append(ValidationIssue(field="support_level", message="must be lower than resistance_level", severity="error"))

    if isinstance(atr, (int, float)) and atr <= 0:
        errors.append(ValidationIssue(field="atr", message="must be > 0", severity="error"))

    if isinstance(price, (int, float)) and isinstance(support, (int, float)) and isinstance(resistance, (int, float)):
        if price < support or price > resistance:
            warnings.append(ValidationIssue(field="last_price", message="price outside S/R corridor", severity="warning"))

    if payload.get("input_quality_status") == QualityStatus.BAD.value:
        warnings.append(ValidationIssue(field="input_quality_status", message="payload eligible for hard reject", severity="warning"))

    return ValidationResult(is_valid=not errors, errors=tuple(errors), warnings=tuple(warnings))


def _validate_iso(payload: dict[str, Any], field: str, errors: list[ValidationIssue]) -> None:
    try:
        datetime.fromisoformat(str(payload[field]).replace("Z", "+00:00"))
    except Exception:
        errors.append(ValidationIssue(field=field, message="must be ISO-8601 datetime", severity="error"))


def _validate_enum(payload: dict[str, Any], field: str, enum_type: Any, errors: list[ValidationIssue]) -> None:
    try:
        enum_type(str(payload[field]))
    except Exception:
        errors.append(ValidationIssue(field=field, message=f"must be one of {[item.value for item in enum_type]}", severity="error"))


def _validate_range(payload: dict[str, Any], field: str, min_value: float, max_value: float, errors: list[ValidationIssue]) -> None:
    value = payload[field]
    if not isinstance(value, (int, float)):
        errors.append(ValidationIssue(field=field, message="must be numeric", severity="error"))
        return
    if value < min_value or value > max_value:
        errors.append(ValidationIssue(field=field, message=f"must be in [{min_value}, {max_value}]", severity="error"))
