from __future__ import annotations

from typing import Any

from .models import LLMFallbackResult, LLMRawResponse, LLMValidationResult

MAX_RETRY_COUNT = 1
RETRYABLE_CODES = {
    "json_parse_failed",
    "required_field_missing",
}



def _error_codes(validation_result: LLMValidationResult) -> tuple[str, ...]:
    return tuple(str(error.get("code", "unknown")) for error in validation_result.errors)



def _build_fallback_payload(raw_response: LLMRawResponse, reason: str) -> dict[str, Any]:
    request_meta = raw_response.request_meta
    return {
        "ticker": str(request_meta.get("ticker") or raw_response.ticker).upper(),
        "timeframe": str(request_meta.get("timeframe", "1m")).lower(),
        "direction": str(request_meta.get("direction", "reject")).lower(),
        "tp": None,
        "sl": None,
        "grids": None,
        "price_up": None,
        "price_down": None,
        "conclusion": f"fallback:{reason}",
    }



def apply_fallback_policy(
    validation_result: LLMValidationResult,
    raw_response: LLMRawResponse,
    *,
    retry_attempt: int = 0,
    max_retry_count: int = MAX_RETRY_COUNT,
) -> LLMFallbackResult:
    error_codes = _error_codes(validation_result)
    primary_code = error_codes[0] if error_codes else "unknown_error"
    retry_allowed = retry_attempt < max_retry_count
    retry_recommended = primary_code in RETRYABLE_CODES and retry_allowed

    if primary_code in {"json_parse_failed", "required_field_missing"} and retry_recommended:
        action = "retry"
    elif primary_code in {
        "invalid_type",
        "invalid_range",
        "invalid_grids",
        "invalid_tp_sl",
        "direction_mismatch",
        "ticker_mismatch",
        "timeframe_mismatch",
    }:
        action = "fallback"
    else:
        action = "reject"

    return LLMFallbackResult(
        action=action,
        reason=primary_code,
        retry_allowed=retry_allowed,
        retry_recommended=retry_recommended,
        fallback_payload=_build_fallback_payload(raw_response, primary_code),
        trace={
            "step": "fallback_policy",
            "retry_attempt": retry_attempt,
            "max_retry_count": max_retry_count,
            "error_codes": error_codes,
            "primary_code": primary_code,
            "action": action,
        },
    )
