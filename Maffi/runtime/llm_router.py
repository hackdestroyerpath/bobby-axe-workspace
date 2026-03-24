from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import PromptBuildResult

DEFAULT_MODEL_ID = "openai:gpt-4.1-mini"
DEFAULT_ROUTE_NAME = "default"


@dataclass(frozen=True, slots=True)
class LLMRoute:
    route_name: str
    ticker: str
    model_id: str
    provider: str
    system_style: str
    risk_mode: str
    temperature: float
    request_meta: dict[str, Any] = field(default_factory=dict)


TICKER_ROUTE_OVERRIDES: dict[str, dict[str, Any]] = {
    "BTC": {
        "route_name": "btc-primary",
        "model_id": "openai:gpt-4.1",
        "provider": "openai",
        "system_style": "macro-liquid-major",
    },
    "BTCUSDC": {
        "route_name": "btc-primary",
        "model_id": "openai:gpt-4.1",
        "provider": "openai",
        "system_style": "macro-liquid-major",
    },
    "ETH": {
        "route_name": "eth-primary",
        "model_id": "openai:gpt-4.1",
        "provider": "openai",
        "system_style": "liquid-major",
    },
    "ETHUSDC": {
        "route_name": "eth-primary",
        "model_id": "openai:gpt-4.1",
        "provider": "openai",
        "system_style": "liquid-major",
    },
}



def _normalize_ticker(raw_ticker: str) -> str:
    return raw_ticker.strip().upper()



def route_llm(prompt_result: PromptBuildResult) -> LLMRoute:
    ticker = _normalize_ticker(str(prompt_result.request_meta.get("ticker", "")))
    risk_mode = str(prompt_result.prompt_meta.get("response_mode", "grid_generation"))
    prompt_risk_mode = str(prompt_result.payload_for_prompt.get("prompt_control", {}).get("risk_mode", "normal"))
    route_conf = TICKER_ROUTE_OVERRIDES.get(ticker, {})

    route_name = route_conf.get("route_name", DEFAULT_ROUTE_NAME)
    model_id = route_conf.get("model_id", DEFAULT_MODEL_ID)
    provider = route_conf.get("provider", model_id.split(":", 1)[0] if ":" in model_id else "openai")
    system_style = route_conf.get("system_style", "general-grid")
    temperature = 0.15 if ticker in {"BTC", "BTCUSDC", "ETH", "ETHUSDC"} else 0.2

    return LLMRoute(
        route_name=route_name,
        ticker=ticker,
        model_id=model_id,
        provider=provider,
        system_style=system_style,
        risk_mode=prompt_risk_mode if prompt_risk_mode else risk_mode,
        temperature=temperature,
        request_meta={
            **prompt_result.request_meta,
            "prompt_version": prompt_result.prompt_version,
            "candidate_count": prompt_result.prompt_meta.get("candidate_count", 0),
        },
    )
