from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .models import AlgoPayload, PromptBuildResult

PROMPT_VERSION = "maffi-prompt-v1"
TOP_GRID_CANDIDATES = 3


def _round_floats(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {k: _round_floats(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_round_floats(v) for v in value]
    return value


def serialize_algo_payload_for_prompt(payload: AlgoPayload) -> dict[str, Any]:
    data = asdict(payload)
    data.pop("metadata", None)
    candidates = data.get("grid_candidates", {}).get("candidates", [])
    if isinstance(candidates, (list, tuple)):
        candidates = sorted(list(candidates), key=lambda item: (-float(item.get("efficiency_score", 0.0)), str(item.get("candidate_id", ""))))[:TOP_GRID_CANDIDATES]
        reduced = []
        for item in candidates:
            reduced.append(
                {
                    "candidate_id": item.get("candidate_id"),
                    "price_down": item.get("price_down"),
                    "price_up": item.get("price_up"),
                    "grid_count": item.get("grid_count"),
                    "grid_step": item.get("grid_step"),
                    "efficiency_score": item.get("efficiency_score"),
                    "candidate_notes": item.get("candidate_notes"),
                }
            )
        data["grid_candidates"] = {"candidates": reduced}
    return _round_floats(data)


def build_system_prompt() -> str:
    return (
        "You are Maffi, a grid-generation assistant for one ticker at a time. "
        "The direction is provided externally and must not be changed. "
        "Do not calculate capital allocation. "
        "Return only the requested JSON contract."
    )



def build_task_prompt(payload: AlgoPayload) -> str:
    rc = payload.request_context
    return (
        f"Generate a grid decision for ticker={rc.ticker}, timeframe={rc.timeframe}, "
        f"request_ts_utc={rc.request_ts_utc}, direction={rc.direction}. "
        "Return tp, sl, grids, price_up, price_down, conclusion."
    )



def build_output_contract_prompt(payload: AlgoPayload) -> str:
    fields = ", ".join(payload.prompt_control.must_return_fields)
    return (
        "Return a JSON object with exactly these fields: "
        f"{fields}. Use exact field names and no extra keys."
    )



def build_final_instruction_prompt() -> str:
    return (
        "Return only one valid JSON object. "
        "Do not use markdown, code fences, explanations, extra text, or reasoning."
    )



def build_payload_prompt(payload: AlgoPayload) -> str:
    serialized = serialize_algo_payload_for_prompt(payload)
    return json.dumps(serialized, ensure_ascii=False, separators=(",", ":"), sort_keys=False)



def build_prompt(payload: AlgoPayload) -> PromptBuildResult:
    system_prompt = build_system_prompt()
    task_prompt = build_task_prompt(payload)
    payload_prompt = build_payload_prompt(payload)
    output_contract_prompt = build_output_contract_prompt(payload)
    final_instruction_prompt = build_final_instruction_prompt()
    user_prompt = "\n\n".join((task_prompt, payload_prompt, output_contract_prompt, final_instruction_prompt))
    combined_prompt = "\n\n".join((system_prompt, user_prompt))
    payload_for_prompt = serialize_algo_payload_for_prompt(payload)
    request_meta = {
        "ticker": payload.request_context.ticker,
        "timeframe": payload.request_context.timeframe,
        "request_ts_utc": payload.request_context.request_ts_utc,
        "direction": payload.request_context.direction,
    }
    prompt_meta = {
        "section_count": 5,
        "included_blocks": tuple(payload_for_prompt.keys()),
        "candidate_count": len(payload_for_prompt.get("grid_candidates", {}).get("candidates", [])),
        "language": payload.prompt_control.language,
        "response_mode": payload.prompt_control.response_mode,
    }
    return PromptBuildResult(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        combined_prompt=combined_prompt,
        prompt_version=PROMPT_VERSION,
        payload_for_prompt=payload_for_prompt,
        request_meta=request_meta,
        prompt_meta=prompt_meta,
    )
