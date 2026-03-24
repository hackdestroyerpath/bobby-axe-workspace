from __future__ import annotations

from typing import Any

from .llm_router import LLMRoute
from .models import FinalNormalizedResponse, LLMFallbackResult, LLMRawResponse, LLMValidationResult



def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)



def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)



def finalize_response(
    *,
    validation_result: LLMValidationResult,
    raw_response: LLMRawResponse,
    route: LLMRoute,
    fallback_result: LLMFallbackResult | None = None,
) -> FinalNormalizedResponse:
    if validation_result.is_valid and validation_result.normalized_payload is not None:
        payload = validation_result.normalized_payload
        status = "ok"
    else:
        payload = fallback_result.fallback_payload if fallback_result is not None else {}
        status = fallback_result.action if fallback_result is not None else "reject"

    return FinalNormalizedResponse(
        ticker=str(payload.get("ticker", raw_response.request_meta.get("ticker", raw_response.ticker))).upper(),
        timeframe=str(payload.get("timeframe", raw_response.request_meta.get("timeframe", "1m"))).lower(),
        direction=str(payload.get("direction", raw_response.request_meta.get("direction", "reject"))).lower(),
        tp=_to_float(payload.get("tp")),
        sl=_to_float(payload.get("sl")),
        grids=_to_int(payload.get("grids")),
        price_up=_to_float(payload.get("price_up")),
        price_down=_to_float(payload.get("price_down")),
        conclusion=str(payload.get("conclusion", "empty_response")),
        status=status,
        confidence=None,
        model_id=route.model_id,
        prompt_version=raw_response.prompt_version,
        validator_summary=validation_result.summary,
        trace={
            "validator": validation_result.trace,
            "route": {
                "route_name": route.route_name,
                "ticker": route.ticker,
                "provider": route.provider,
                "temperature": route.temperature,
            },
            "raw": {
                "model_id": raw_response.model_id,
                "prompt_version": raw_response.prompt_version,
                "has_parsed_json": raw_response.parsed_json is not None,
            },
            "fallback": fallback_result.trace if fallback_result is not None else None,
        },
    )
