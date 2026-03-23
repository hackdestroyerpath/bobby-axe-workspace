from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping, Sequence

from .common.tick_normalizer import NormalizedTick, normalize_ticks
from .common.tick_to_features_engine import CandleFeatureRow, build_tick_feature_candles
from .machine_registry import MachineSpec, get_machine_spec
from .runtime_contract import (
    STATUS_ERROR,
    STATUS_PARTIAL,
    STATUS_READY,
    RuntimeErrorInfo,
    assess_partial_window,
    assess_warmup,
    build_failure_error,
    build_meta,
    build_summary,
    now_utc_iso,
    validate_request,
    validate_response_payload,
)
from .strategy_cores import (
    StrategyComputation,
    compute_elliott,
    compute_levels_fibo_hv,
    compute_rsi_macd,
    compute_volume,
)


@dataclass(frozen=True, slots=True)
class MachineExecutor:
    machine_spec: MachineSpec
    compute_fn: Callable[[Sequence[CandleFeatureRow]], StrategyComputation]
    build_version: str = "phase2.0"

    def execute(
        self,
        request: Mapping[str, Any],
        ticks: Iterable[Mapping[str, Any] | NormalizedTick],
        *,
        gap_threshold: timedelta | None = None,
        retention_floor: datetime | None = None,
        page_complete: bool = True,
    ) -> dict[str, Any]:
        request_errors = validate_request(request, self.machine_spec)
        if request_errors:
            return self._error_response(request, request_errors)

        strict_mode = bool(request.get("options", {}).get("strict_mode", False))
        include_incomplete_candle = bool(request.get("options", {}).get("include_incomplete_candle", False))
        window_from = _parse_dt(request["input_window"]["from"])
        window_to = _parse_dt(request["input_window"]["to"])

        try:
            normalization = normalize_ticks(
                ticks,
                window_from=window_from,
                window_to=window_to,
                gap_threshold=gap_threshold or _default_gap_threshold(self.machine_spec.timeframe),
                retention_floor=retention_floor,
                page_complete=page_complete,
            )
        except Exception as exc:
            return self._runtime_failure_response(
                request,
                code="NORMALIZATION_FAILED",
                message=f"Shared tick normalizer failed: {exc}",
            )

        status, runtime_errors = assess_partial_window(normalization, strict_mode=strict_mode)
        if status == STATUS_ERROR and normalization.empty_window:
            return self._terminal_response(request, normalization, {}, runtime_errors, status)

        try:
            candle_result = build_tick_feature_candles(
                normalization.ticks,
                window_from=window_from,
                window_to=window_to,
                timeframes=(self.machine_spec.timeframe,),
                include_incomplete_candle=include_incomplete_candle,
            )
        except Exception as exc:
            return self._terminal_response(
                request,
                normalization,
                {},
                [
                    *runtime_errors,
                    self._build_runtime_error(
                        "FEATURE_ENGINE_FAILED",
                        f"Shared tick-to-features engine failed: {exc}",
                    ),
                ],
                STATUS_ERROR,
            )

        candles = candle_result.candles_by_timeframe[self.machine_spec.timeframe]
        warmup = assess_warmup(_count_usable_candles(candles), self.machine_spec.warmup, strict_mode=strict_mode)
        if not warmup.has_sufficient_warmup:
            runtime_errors = [
                *runtime_errors,
                self._build_runtime_error("INSUFFICIENT_WARMUP", warmup.note),
            ]
            features: dict[str, Any] = {}
            final_status = STATUS_ERROR if warmup.status == STATUS_ERROR else STATUS_PARTIAL
            return self._terminal_response(request, normalization, features, runtime_errors, final_status)

        try:
            computation = self.compute_fn(candles)
        except Exception as exc:
            return self._terminal_response(
                request,
                normalization,
                {},
                [
                    *runtime_errors,
                    self._build_runtime_error(
                        "FEATURE_ENGINE_FAILED",
                        f"Strategy compute failed after candle build: {exc}",
                    ),
                ],
                STATUS_ERROR,
            )

        final_status = STATUS_PARTIAL if normalization.is_partial else STATUS_READY
        return self._terminal_response(request, normalization, dict(computation.features), runtime_errors, final_status)

    def _build_runtime_error(self, code: str, message: str | None = None) -> RuntimeErrorInfo:
        return build_failure_error(self.machine_spec.machine_id, code, message=message)

    def _error_response(self, request: Mapping[str, Any], errors: list[Any]) -> dict[str, Any]:
        generated_at = now_utc_iso()
        response = {
            "request_id": self._safe_request_string(request, "request_id", f"invalid-request-{self.machine_spec.machine_id}"),
            "agent_id": request.get("agent_id", self.machine_spec.agent_id),
            "strategy": request.get("strategy", self.machine_spec.strategy),
            "timeframe": request.get("timeframe", self.machine_spec.timeframe),
            "symbol": request.get("symbol", "UNKNOWN"),
            "source": request.get("source", "UNKNOWN"),
            "requested_at": request.get("requested_at", now_utc_iso()),
            "generated_at": generated_at,
            "response_contract_version": request.get("response_contract_version", "unknown"),
            "status": STATUS_ERROR,
            "input_window": request.get("input_window", {"from": now_utc_iso(), "to": now_utc_iso()}),
            "features": {},
            "summary": {
                "state": "mixed",
                "strength": "weak",
                "confidence": "low",
                "note": "request validation failed",
            },
            "meta": {
                "data_points": 0,
                "coverage_ratio": 0.0,
                "is_partial": False,
                "partial_reason": None,
                "source_contract_version": request.get("source_contract_version", "unknown"),
                "build_version": self.build_version,
                "api_key_id": self.machine_spec.api_key_id,
                "machine_id": self.machine_spec.machine_id,
            },
            "errors": [error.as_dict() if hasattr(error, "as_dict") else error for error in errors],
        }
        return self._validate_or_output_failure(request, response)

    def _runtime_failure_response(
        self,
        request: Mapping[str, Any],
        *,
        code: str,
        message: str,
        normalization: Any | None = None,
        errors: Sequence[Any] = (),
    ) -> dict[str, Any]:
        generated_at = now_utc_iso()
        response = self._build_response_payload(
            request,
            normalization=normalization,
            features={},
            errors=[*errors, self._build_runtime_error(code, message)],
            status=STATUS_ERROR,
            generated_at=generated_at,
        )
        return self._validate_or_output_failure(request, response)

    def _terminal_response(
        self,
        request: Mapping[str, Any],
        normalization: Any,
        features: Mapping[str, Any],
        errors: list[Any],
        status: str,
    ) -> dict[str, Any]:
        generated_at = now_utc_iso()
        response = self._build_response_payload(
            request,
            normalization=normalization,
            features=features,
            errors=errors,
            status=status,
            generated_at=generated_at,
        )
        return self._validate_or_output_failure(request, response)

    def _build_response_payload(
        self,
        request: Mapping[str, Any],
        *,
        normalization: Any | None,
        features: Mapping[str, Any],
        errors: Sequence[Any],
        status: str,
        generated_at: str | None = None,
    ) -> dict[str, Any]:
        meta = self._build_meta_payload(request, normalization, status)
        summary = build_summary(
            self.machine_spec.strategy,
            features,
            normalization.partial_reasons if normalization is not None and status != STATUS_READY else (),
        )
        if status == STATUS_ERROR and not features:
            summary = {
                "state": "mixed",
                "strength": "weak",
                "confidence": "low",
                "note": "runtime terminated before usable strategy output",
            }
        payload_generated_at = generated_at or now_utc_iso()
        return {
            "request_id": self._safe_request_string(request, "request_id", f"unknown-request-{self.machine_spec.machine_id}"),
            "agent_id": self.machine_spec.agent_id,
            "strategy": self.machine_spec.strategy,
            "timeframe": self.machine_spec.timeframe,
            "symbol": self._safe_request_string(request, "symbol", "UNKNOWN"),
            "source": self._safe_request_string(request, "source", "UNKNOWN"),
            "requested_at": self._safe_request_datetime(request, "requested_at"),
            "generated_at": payload_generated_at,
            "response_contract_version": self._safe_request_string(request, "response_contract_version", "unknown"),
            "status": status,
            "input_window": self._safe_input_window(request),
            "features": dict(features),
            "summary": summary,
            "meta": meta,
            "errors": [error.as_dict() if hasattr(error, "as_dict") else error for error in errors],
        }

    def _build_meta_payload(self, request: Mapping[str, Any], normalization: Any | None, status: str) -> dict[str, Any]:
        if normalization is None:
            return {
                "data_points": 0,
                "coverage_ratio": 0.0,
                "is_partial": False,
                "partial_reason": None,
                "source_contract_version": self._safe_request_string(request, "source_contract_version", "unknown"),
                "build_version": self.build_version,
                "api_key_id": self.machine_spec.api_key_id,
                "machine_id": self.machine_spec.machine_id,
            }

        normalized_request = dict(request)
        normalized_request["source_contract_version"] = self._safe_request_string(request, "source_contract_version", "unknown")
        meta = build_meta(
            machine_spec=self.machine_spec,
            request=normalized_request,
            normalization=normalization,
            build_version=self.build_version,
        )
        meta["is_partial"] = status == STATUS_PARTIAL
        meta["partial_reason"] = None
        if status == STATUS_PARTIAL:
            meta["partial_reason"] = normalization.partial_reason or "insufficient_warmup"
        return meta

    def _validate_or_output_failure(self, request: Mapping[str, Any], response: dict[str, Any]) -> dict[str, Any]:
        schema_errors = validate_response_payload(response)
        if not schema_errors:
            return response

        output_error = self._build_runtime_error(
            "OUTPUT_SCHEMA_FAILED",
            f"Response contract validation failed: {'; '.join(schema_errors)}",
        )
        fallback = self._build_response_payload(
            request,
            normalization=None,
            features={},
            errors=[output_error],
            status=STATUS_ERROR,
            generated_at=self._safe_response_datetime(response, "generated_at"),
        )
        return fallback

    def _safe_request_string(self, request: Mapping[str, Any], field: str, default: str) -> str:
        value = request.get(field)
        return value if isinstance(value, str) and value else default

    def _safe_request_datetime(self, request: Mapping[str, Any], field: str) -> str:
        value = request.get(field)
        if isinstance(value, str) and value:
            try:
                _parse_dt(value)
                return value
            except ValueError:
                pass
        return now_utc_iso()

    def _safe_input_window(self, request: Mapping[str, Any]) -> dict[str, str]:
        value = request.get("input_window")
        if isinstance(value, Mapping):
            from_value = value.get("from")
            to_value = value.get("to")
            if isinstance(from_value, str) and from_value and isinstance(to_value, str) and to_value:
                try:
                    _parse_dt(from_value)
                    _parse_dt(to_value)
                    return {"from": from_value, "to": to_value}
                except ValueError:
                    pass
        now = now_utc_iso()
        return {"from": now, "to": now}

    def _safe_response_datetime(self, response: Mapping[str, Any], field: str) -> str:
        value = response.get(field)
        if isinstance(value, str) and value:
            try:
                _parse_dt(value)
                return value
            except ValueError:
                pass
        return now_utc_iso()


def execute_rsi_macd_machine(request: Mapping[str, Any], ticks: Iterable[Mapping[str, Any] | NormalizedTick], **kwargs: Any) -> dict[str, Any]:
    return MachineExecutor(get_machine_spec("RSI_MACD", request["timeframe"]), compute_rsi_macd).execute(request, ticks, **kwargs)


def execute_levels_fibo_hv_machine(request: Mapping[str, Any], ticks: Iterable[Mapping[str, Any] | NormalizedTick], **kwargs: Any) -> dict[str, Any]:
    return MachineExecutor(get_machine_spec("LEVELS_FIBO_HV", request["timeframe"]), compute_levels_fibo_hv).execute(request, ticks, **kwargs)


def execute_volume_machine(request: Mapping[str, Any], ticks: Iterable[Mapping[str, Any] | NormalizedTick], **kwargs: Any) -> dict[str, Any]:
    return MachineExecutor(get_machine_spec("VOLUME", request["timeframe"]), compute_volume).execute(request, ticks, **kwargs)


def execute_elliott_machine(request: Mapping[str, Any], ticks: Iterable[Mapping[str, Any] | NormalizedTick], **kwargs: Any) -> dict[str, Any]:
    return MachineExecutor(get_machine_spec("ELLIOTT", request["timeframe"]), compute_elliott).execute(request, ticks, **kwargs)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _default_gap_threshold(timeframe: str) -> timedelta:
    return {
        "1m": timedelta(seconds=30),
        "5m": timedelta(minutes=2),
        "60m": timedelta(minutes=20),
    }[timeframe]


def _count_usable_candles(candles: Sequence[CandleFeatureRow]) -> int:
    return sum(1 for candle in candles if candle.close is not None)
