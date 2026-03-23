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
    ERROR_SCOPE_FEATURES,
    assess_partial_window,
    assess_warmup,
    build_meta,
    build_summary,
    now_utc_iso,
    validate_request,
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
        window_from = _parse_dt(request["input_window"]["from"])
        window_to = _parse_dt(request["input_window"]["to"])
        normalization = normalize_ticks(
            ticks,
            window_from=window_from,
            window_to=window_to,
            gap_threshold=gap_threshold or _default_gap_threshold(self.machine_spec.timeframe),
            retention_floor=retention_floor,
            page_complete=page_complete,
        )
        status, runtime_errors = assess_partial_window(normalization, strict_mode=strict_mode)
        if status == STATUS_ERROR and normalization.empty_window:
            return self._terminal_response(request, normalization, {}, runtime_errors, status)

        candle_result = build_tick_feature_candles(
            normalization.ticks,
            window_from=window_from,
            window_to=window_to,
            timeframes=(self.machine_spec.timeframe,),
        )
        candles = candle_result.candles_by_timeframe[self.machine_spec.timeframe]
        warmup = assess_warmup(len([c for c in candles if c.close is not None]), self.machine_spec.warmup, strict_mode=strict_mode)
        if not warmup.has_sufficient_warmup:
            runtime_errors = [
                *runtime_errors,
                {
                    "code": "INSUFFICIENT_WARMUP",
                    "message": warmup.note,
                    "severity": "warning",
                    "scope": ERROR_SCOPE_FEATURES,
                    "retryable": False,
                },
            ]
            features: dict[str, Any] = {}
            final_status = STATUS_ERROR if warmup.status == STATUS_ERROR else STATUS_PARTIAL
            return self._terminal_response(request, normalization, features, runtime_errors, final_status)

        computation = self.compute_fn(candles)
        final_status = STATUS_PARTIAL if normalization.is_partial else STATUS_READY
        return self._terminal_response(request, normalization, dict(computation.features), runtime_errors, final_status)

    def _error_response(self, request: Mapping[str, Any], errors: list[Any]) -> dict[str, Any]:
        return {
            "agent_id": request.get("agent_id", self.machine_spec.agent_id),
            "strategy": request.get("strategy", self.machine_spec.strategy),
            "timeframe": request.get("timeframe", self.machine_spec.timeframe),
            "symbol": request.get("symbol", "UNKNOWN"),
            "source": request.get("source", "UNKNOWN"),
            "requested_at": request.get("requested_at", now_utc_iso()),
            "as_of": now_utc_iso(),
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

    def _terminal_response(
        self,
        request: Mapping[str, Any],
        normalization,
        features: Mapping[str, Any],
        errors: list[Any],
        status: str,
    ) -> dict[str, Any]:
        meta = build_meta(
            machine_spec=self.machine_spec,
            request=request,
            normalization=normalization,
            build_version=self.build_version,
        )
        meta["is_partial"] = status == STATUS_PARTIAL
        meta["partial_reason"] = normalization.partial_reason if status == STATUS_PARTIAL else None
        summary = build_summary(self.machine_spec.strategy, features, normalization.partial_reasons if status != STATUS_READY else ())
        if status == STATUS_ERROR and not features:
            summary = {
                "state": "mixed",
                "strength": "weak",
                "confidence": "low",
                "note": "runtime terminated before usable strategy output",
            }
        return {
            "agent_id": self.machine_spec.agent_id,
            "strategy": self.machine_spec.strategy,
            "timeframe": self.machine_spec.timeframe,
            "symbol": request["symbol"],
            "source": request["source"],
            "requested_at": request["requested_at"],
            "as_of": now_utc_iso(),
            "response_contract_version": request["response_contract_version"],
            "status": status,
            "input_window": request["input_window"],
            "features": dict(features),
            "summary": summary,
            "meta": meta,
            "errors": [error.as_dict() if hasattr(error, "as_dict") else error for error in errors],
        }


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
