from __future__ import annotations

from typing import Any, Callable

from .fallbacks import MAX_RETRY_COUNT, apply_fallback_policy
from .finalize import finalize_response
from .llm_client import call_llm
from .llm_router import route_llm
from .models import AlgoPayload, FinalNormalizedResponse, TriggerInput
from .output_validator import validate_llm_output
from .prompt_builder import build_prompt



def run_trigger(
    trigger: TriggerInput,
    *,
    algo_payload: AlgoPayload | None = None,
    payload_source: Callable[[TriggerInput], AlgoPayload] | None = None,
    transport: Any | None = None,
) -> FinalNormalizedResponse:
    if algo_payload is None:
        if payload_source is None:
            raise ValueError("Either algo_payload or payload_source must be provided")
        algo_payload = payload_source(trigger)

    prompt_result = build_prompt(algo_payload)
    route = route_llm(prompt_result)

    max_retries = MAX_RETRY_COUNT
    retry_attempt = 0
    last_raw_response = None
    while True:
        raw_response = call_llm(prompt_result, route, transport=transport)
        last_raw_response = raw_response
        validation_result = validate_llm_output(
            raw_response,
            expected_direction=trigger.direction,
            expected_ticker=trigger.ticker,
            expected_timeframe=trigger.timeframe,
        )
        if validation_result.is_valid:
            return finalize_response(validation_result=validation_result, raw_response=raw_response, route=route)

        fallback_result = apply_fallback_policy(
            validation_result,
            raw_response,
            retry_attempt=retry_attempt,
            max_retry_count=max_retries,
        )
        if fallback_result.action == "retry" and retry_attempt < max_retries:
            retry_attempt += 1
            continue

        return finalize_response(
            validation_result=validation_result,
            raw_response=raw_response,
            route=route,
            fallback_result=fallback_result,
        )

    raise RuntimeError(f"Unreachable state; last_raw_response={last_raw_response}")
