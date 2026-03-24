from __future__ import annotations

import json
from typing import Any

from .llm_router import LLMRoute
from .models import LLMRawResponse, PromptBuildResult


def build_llm_request(prompt_result: PromptBuildResult, route: LLMRoute) -> dict[str, Any]:
    return {
        "provider": route.provider,
        "model_id": route.model_id,
        "temperature": route.temperature,
        "system_prompt": prompt_result.system_prompt,
        "user_prompt": prompt_result.user_prompt,
        "prompt_version": prompt_result.prompt_version,
        "request_meta": {
            **route.request_meta,
            **prompt_result.request_meta,
        },
    }


def _try_parse_json(raw_text: str) -> dict[str, Any] | None:
    text = raw_text.strip()
    try:
        parsed = json.loads(text)
    except Exception:
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            fenced = "\n".join(lines).strip()
            try:
                parsed = json.loads(fenced)
            except Exception:
                return None
        else:
            return None
    return parsed if isinstance(parsed, dict) else None


def _raw_model_call(request: dict[str, Any], *, transport: Any | None = None) -> str:
    if transport is None:
        raise NotImplementedError("LLM transport is not wired yet")
    return str(transport(request))


def call_llm(prompt_result: PromptBuildResult, route: LLMRoute, *, transport: Any | None = None) -> LLMRawResponse:
    request = build_llm_request(prompt_result, route)
    raw_text = _raw_model_call(request, transport=transport)
    parsed_json = _try_parse_json(raw_text)
    return LLMRawResponse(
        ticker=route.ticker,
        model_id=route.model_id,
        prompt_version=prompt_result.prompt_version,
        raw_text=raw_text,
        parsed_json=parsed_json,
        request_meta={
            **route.request_meta,
            **prompt_result.request_meta,
        },
    )
