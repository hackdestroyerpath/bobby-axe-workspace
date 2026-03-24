from __future__ import annotations

from .models import LLMRawResponse, LLMValidationResult

REQUIRED_OUTPUT_FIELDS = (
    "ticker",
    "timeframe",
    "direction",
    "tp",
    "sl",
    "grids",
    "price_up",
    "price_down",
    "conclusion",
)

EXPECTED_TYPES = {
    "ticker": str,
    "timeframe": str,
    "direction": str,
    "tp": (int, float),
    "sl": (int, float),
    "grids": int,
    "price_up": (int, float),
    "price_down": (int, float),
    "conclusion": str,
}



def validate_llm_output(
    raw_response: LLMRawResponse,
    *,
    expected_direction: str,
    expected_ticker: str,
    expected_timeframe: str,
) -> LLMValidationResult:
    if raw_response.parsed_json is None:
        return LLMValidationResult(
            is_valid=False,
            errors=(
                {
                    "code": "json_parse_failed",
                    "field": "raw_text",
                    "message": "response is not a valid JSON object",
                },
            ),
            normalized_payload=None,
            summary={
                "total_checks": 1,
                "failed_checks": 1,
                "warning_checks": 0,
            },
            trace={
                "step": "json_parse",
                "status": "fail",
                "raw_text_present": bool(raw_response.raw_text),
            },
        )

    missing = tuple(field for field in REQUIRED_OUTPUT_FIELDS if field not in raw_response.parsed_json)
    if missing:
        return LLMValidationResult(
            is_valid=False,
            errors=tuple(
                {
                    "code": "required_field_missing",
                    "field": field,
                    "message": "required output field is missing",
                }
                for field in missing
            ),
            normalized_payload=raw_response.parsed_json,
            summary={
                "total_checks": 1 + len(REQUIRED_OUTPUT_FIELDS),
                "failed_checks": len(missing),
                "warning_checks": 0,
            },
            trace={
                "step": "required_fields",
                "status": "fail",
                "missing_fields": missing,
            },
        )

    type_errors = []
    for field, expected_type in EXPECTED_TYPES.items():
        value = raw_response.parsed_json[field]
        if not isinstance(value, expected_type):
            type_errors.append(
                {
                    "code": "invalid_type",
                    "field": field,
                    "message": f"expected {expected_type}, got {type(value)}",
                }
            )

    if type_errors:
        return LLMValidationResult(
            is_valid=False,
            errors=tuple(type_errors),
            normalized_payload=raw_response.parsed_json,
            summary={
                "total_checks": 1 + len(REQUIRED_OUTPUT_FIELDS) + len(EXPECTED_TYPES),
                "failed_checks": len(type_errors),
                "warning_checks": 0,
            },
            trace={
                "step": "field_types",
                "status": "fail",
                "invalid_fields": tuple(item["field"] for item in type_errors),
            },
        )

    range_errors = []
    if float(raw_response.parsed_json["price_down"]) >= float(raw_response.parsed_json["price_up"]):
        range_errors.append(
            {
                "code": "invalid_range",
                "field": "price_down/price_up",
                "message": "price_down must be lower than price_up",
            }
        )
    if int(raw_response.parsed_json["grids"]) <= 0:
        range_errors.append(
            {
                "code": "invalid_grids",
                "field": "grids",
                "message": "grids must be positive",
            }
        )
    if float(raw_response.parsed_json["tp"]) <= 0 or float(raw_response.parsed_json["sl"]) <= 0:
        range_errors.append(
            {
                "code": "invalid_tp_sl",
                "field": "tp/sl",
                "message": "tp and sl must be positive numbers",
            }
        )

    if range_errors:
        return LLMValidationResult(
            is_valid=False,
            errors=tuple(range_errors),
            normalized_payload=raw_response.parsed_json,
            summary={
                "total_checks": 1 + len(REQUIRED_OUTPUT_FIELDS) + len(EXPECTED_TYPES) + 3,
                "failed_checks": len(range_errors),
                "warning_checks": 0,
            },
            trace={
                "step": "range_logic",
                "status": "fail",
                "range_errors": tuple(item["code"] for item in range_errors),
            },
        )

    if str(raw_response.parsed_json["direction"]).lower() != str(expected_direction).lower():
        return LLMValidationResult(
            is_valid=False,
            errors=(
                {
                    "code": "direction_mismatch",
                    "field": "direction",
                    "message": "output direction does not match requested direction",
                },
            ),
            normalized_payload=raw_response.parsed_json,
            summary={
                "total_checks": 1 + len(REQUIRED_OUTPUT_FIELDS) + len(EXPECTED_TYPES) + 4,
                "failed_checks": 1,
                "warning_checks": 0,
            },
            trace={
                "step": "direction_consistency",
                "status": "fail",
                "expected_direction": expected_direction,
                "actual_direction": raw_response.parsed_json["direction"],
            },
        )

    consistency_errors = []
    if str(raw_response.parsed_json["ticker"]).upper() != str(expected_ticker).upper():
        consistency_errors.append(
            {
                "code": "ticker_mismatch",
                "field": "ticker",
                "message": "output ticker does not match requested ticker",
            }
        )
    if str(raw_response.parsed_json["timeframe"]).lower() != str(expected_timeframe).lower():
        consistency_errors.append(
            {
                "code": "timeframe_mismatch",
                "field": "timeframe",
                "message": "output timeframe does not match requested timeframe",
            }
        )

    if consistency_errors:
        return LLMValidationResult(
            is_valid=False,
            errors=tuple(consistency_errors),
            normalized_payload=raw_response.parsed_json,
            summary={
                "total_checks": 1 + len(REQUIRED_OUTPUT_FIELDS) + len(EXPECTED_TYPES) + 6,
                "failed_checks": len(consistency_errors),
                "warning_checks": 0,
                "passed_checks": (1 + len(REQUIRED_OUTPUT_FIELDS) + len(EXPECTED_TYPES) + 6) - len(consistency_errors),
            },
            trace={
                "step": "request_consistency",
                "status": "fail",
                "expected_ticker": expected_ticker,
                "actual_ticker": raw_response.parsed_json["ticker"],
                "expected_timeframe": expected_timeframe,
                "actual_timeframe": raw_response.parsed_json["timeframe"],
            },
        )

    total_checks = 1 + len(REQUIRED_OUTPUT_FIELDS) + len(EXPECTED_TYPES) + 6
    return LLMValidationResult(
        is_valid=True,
        errors=(),
        warnings=(),
        normalized_payload=raw_response.parsed_json,
        summary={
            "total_checks": total_checks,
            "failed_checks": 0,
            "warning_checks": 0,
            "passed_checks": total_checks,
        },
        trace={
            "step": "validation_complete",
            "status": "pass",
            "expected_direction": expected_direction,
            "expected_ticker": expected_ticker,
            "expected_timeframe": expected_timeframe,
            "model_id": raw_response.model_id,
            "prompt_version": raw_response.prompt_version,
        },
    )
