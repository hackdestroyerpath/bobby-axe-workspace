from __future__ import annotations

from datetime import datetime
from typing import Any

from .enums import DominantSide, MarketRegime, QualityStatus, VolatilityRegime
from .models import (
    ValidationCounts,
    ValidationDegrade,
    ValidationIssue,
    ValidationResult,
    ValidationSummary,
    ValidationTopReason,
)

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
    total_checks = 0
    passed = 0

    for field in sorted(_REQUIRED_FIELDS):
        total_checks += 1
        if field not in payload:
            errors.append(ValidationIssue(field=field, message="missing required field", severity="error"))
        else:
            passed += 1

    if errors:
        return _build_result(payload, errors=errors, warnings=warnings, total_checks=total_checks, passed=passed)

    total_checks, passed = _validate_iso(payload, "generated_at_utc", errors, total_checks, passed)
    total_checks, passed = _validate_enum(payload, "input_quality_status", QualityStatus, errors, total_checks, passed)
    total_checks, passed = _validate_enum(payload, "market_regime", MarketRegime, errors, total_checks, passed)
    total_checks, passed = _validate_enum(payload, "volatility_regime", VolatilityRegime, errors, total_checks, passed)
    total_checks, passed = _validate_enum(payload, "dominant_side", DominantSide, errors, total_checks, passed)

    for field in ("long_score", "short_score", "reject_score"):
        total_checks, passed = _validate_range(payload, field, 0.0, 100.0, errors, total_checks, passed)

    total_checks, passed = _validate_range(payload, "confidence_hint", 0.0, 1.0, errors, total_checks, passed)

    candidates = payload["entry_candidates"]
    total_checks += 1
    if not isinstance(candidates, (list, tuple)) or not candidates:
        errors.append(ValidationIssue(field="entry_candidates", message="must be non-empty list/tuple", severity="error"))
    else:
        passed += 1
        for idx, candidate in enumerate(candidates):
            total_checks += 1
            if not isinstance(candidate, (int, float)):
                errors.append(ValidationIssue(field=f"entry_candidates[{idx}]", message="must be numeric", severity="error"))
            else:
                passed += 1

    support = payload["support_level"]
    resistance = payload["resistance_level"]
    price = payload["last_price"]
    atr = payload["atr"]
    for numeric_field, value in (("support_level", support), ("resistance_level", resistance), ("last_price", price), ("atr", atr)):
        total_checks += 1
        if not isinstance(value, (int, float)):
            errors.append(ValidationIssue(field=numeric_field, message="must be numeric", severity="error"))
        else:
            passed += 1

    total_checks += 1
    if isinstance(support, (int, float)) and isinstance(resistance, (int, float)):
        if support >= resistance:
            errors.append(ValidationIssue(field="support_level", message="must be lower than resistance_level", severity="error"))
        else:
            passed += 1

    total_checks += 1
    if isinstance(atr, (int, float)):
        if atr <= 0:
            errors.append(ValidationIssue(field="atr", message="must be > 0", severity="error"))
        else:
            passed += 1

    total_checks += 1
    if isinstance(price, (int, float)) and isinstance(support, (int, float)) and isinstance(resistance, (int, float)):
        if price < support or price > resistance:
            warnings.append(ValidationIssue(field="last_price", message="price outside S/R corridor", severity="warning"))
        else:
            passed += 1

    total_checks += 1
    if payload.get("input_quality_status") == QualityStatus.BAD.value:
        warnings.append(ValidationIssue(field="input_quality_status", message="payload eligible for hard reject", severity="warning"))
    else:
        passed += 1

    return _build_result(payload, errors=errors, warnings=warnings, total_checks=total_checks, passed=passed)


def _build_result(
    payload: dict[str, Any],
    *,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
    total_checks: int,
    passed: int,
) -> ValidationResult:
    quality_status = str(payload.get("input_quality_status", "bad"))
    is_degraded = quality_status in {QualityStatus.DEGRADED.value, QualityStatus.BAD.value}
    degrade_score = 1.0 if quality_status == QualityStatus.BAD.value else (0.5 if quality_status == QualityStatus.DEGRADED.value else 0.0)
    degrade_sources = ("input_quality_status",) if is_degraded else ()

    reasons = _aggregate_reasons(errors, warnings, quality_status=quality_status)
    severity_distribution = {
        "error": len(errors),
        "warning": len(warnings),
        "degrade": 1 if is_degraded else 0,
    }
    warning_count = len(warnings)
    failed = len(errors)
    counts = ValidationCounts(
        total_checks=total_checks + warning_count,
        passed=max(0, passed),
        failed=failed,
        warnings=warning_count,
    )
    summary = ValidationSummary(
        counts=counts,
        errors=tuple(f"{issue.field}: {issue.message}" for issue in errors),
        warnings=tuple(f"{issue.field}: {issue.message}" for issue in warnings),
        degrade=ValidationDegrade(
            is_degraded=is_degraded,
            degrade_score=degrade_score,
            sources=degrade_sources,
        ),
        top_reasons=tuple(
            ValidationTopReason(code=reason["code"], count=reason["count"], severity=reason["severity"])
            for reason in reasons
        ),
    )
    return ValidationResult(
        is_valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        trace={
            "counts": {
                "total_checks": counts.total_checks,
                "passed": counts.passed,
                "failed": counts.failed,
                "warnings": counts.warnings,
            },
            "reasons": reasons,
            "severity_distribution": severity_distribution,
            "degrade_score": degrade_score,
            "is_degraded": is_degraded,
        },
        summary=summary,
    )


def _aggregate_reasons(
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
    *,
    quality_status: str,
) -> list[dict[str, Any]]:
    counter: dict[tuple[str, str], int] = {}
    for issue in tuple(errors) + tuple(warnings):
        key = (str(issue.field), str(issue.severity))
        counter[key] = counter.get(key, 0) + 1

    if quality_status in {QualityStatus.DEGRADED.value, QualityStatus.BAD.value}:
        key = ("input_quality_status", "degrade")
        counter[key] = counter.get(key, 0) + 1

    return [
        {"code": code, "count": count, "severity": severity}
        for (code, severity), count in sorted(counter.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
    ]


def _validate_iso(
    payload: dict[str, Any],
    field: str,
    errors: list[ValidationIssue],
    total_checks: int,
    passed: int,
) -> tuple[int, int]:
    total_checks += 1
    try:
        datetime.fromisoformat(str(payload[field]).replace("Z", "+00:00"))
    except Exception:
        errors.append(ValidationIssue(field=field, message="must be ISO-8601 datetime", severity="error"))
        return total_checks, passed
    return total_checks, passed + 1


def _validate_enum(
    payload: dict[str, Any],
    field: str,
    enum_type: Any,
    errors: list[ValidationIssue],
    total_checks: int,
    passed: int,
) -> tuple[int, int]:
    total_checks += 1
    try:
        enum_type(str(payload[field]))
    except Exception:
        errors.append(ValidationIssue(field=field, message=f"must be one of {[item.value for item in enum_type]}", severity="error"))
        return total_checks, passed
    return total_checks, passed + 1


def _validate_range(
    payload: dict[str, Any],
    field: str,
    min_value: float,
    max_value: float,
    errors: list[ValidationIssue],
    total_checks: int,
    passed: int,
) -> tuple[int, int]:
    total_checks += 1
    value = payload[field]
    if not isinstance(value, (int, float)):
        errors.append(ValidationIssue(field=field, message="must be numeric", severity="error"))
        return total_checks, passed
    if value < min_value or value > max_value:
        errors.append(ValidationIssue(field=field, message=f"must be in [{min_value}, {max_value}]", severity="error"))
        return total_checks, passed
    return total_checks, passed + 1
