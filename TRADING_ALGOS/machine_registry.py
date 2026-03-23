from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Mapping


@dataclass(frozen=True, slots=True)
class WarmupSpec:
    minimum_window: timedelta
    recommended_window: timedelta
    minimum_valid_candles: int
    insufficient_warmup_status: str


@dataclass(frozen=True, slots=True)
class MachineSpec:
    machine_id: str
    agent_id: str
    strategy: str
    timeframe: str
    human_name: str
    input_timeframe_target: str
    primary_output_packet: str
    runtime_entrypoint: str
    api_key_id: str
    build_version_policy: str
    owner: str
    warmup: WarmupSpec
    confidence_downgrade_rules: tuple[str, ...]
    retryable_failure_codes: tuple[str, ...]


_STRATEGY_SPECS = {
    "RSI_MACD": {
        "human_prefix": "RSI + MACD",
        "primary_output_packet": "momentum_packet",
        "runtime_entrypoint": "TRADING_ALGOS.machines:execute_rsi_macd_machine",
        "api_key_id": "collector-primary",
        "build_version_policy": "phase2-rsi-macd-family-semver",
        "owner": "Maffi",
        "warmup": {
            "1m": WarmupSpec(timedelta(minutes=35), timedelta(minutes=180), 35, "partial"),
            "5m": WarmupSpec(timedelta(minutes=175), timedelta(hours=12), 35, "partial"),
            "60m": WarmupSpec(timedelta(hours=35), timedelta(days=14), 35, "partial"),
        },
        "confidence_downgrade_rules": (
            "gap_heavy_window_caps_confidence_at_low",
            "incomplete_last_candle_caps_strength_at_medium",
            "retention_or_pagination_forces_partial",
        ),
        "retryable_failure_codes": (
            "READ_TIMEOUT",
            "PAGINATION_DRIFT",
            "NORMALIZATION_FAILED",
            "FEATURE_ENGINE_FAILED",
        ),
    },
    "LEVELS_FIBO_HV": {
        "human_prefix": "Levels + Fibo + Horizontal Volume",
        "primary_output_packet": "structure_packet",
        "runtime_entrypoint": "TRADING_ALGOS.machines:execute_levels_fibo_hv_machine",
        "api_key_id": "collector-primary",
        "build_version_policy": "phase2-levels-fibo-hv-family-semver",
        "owner": "Ben_Kim",
        "warmup": {
            "1m": WarmupSpec(timedelta(minutes=90), timedelta(hours=6), 45, "partial"),
            "5m": WarmupSpec(timedelta(hours=8), timedelta(days=2), 45, "partial"),
            "60m": WarmupSpec(timedelta(days=5), timedelta(days=30), 45, "partial"),
        },
        "confidence_downgrade_rules": (
            "weak_swing_structure_caps_confidence_at_low",
            "retention_depth_on_60m_forces_partial",
            "partial_input_disallows_strong_structure_claims",
        ),
        "retryable_failure_codes": (
            "READ_TIMEOUT",
            "PAGINATION_DRIFT",
            "FEATURE_ENGINE_FAILED",
        ),
    },
    "VOLUME": {
        "human_prefix": "Volume Analysis",
        "primary_output_packet": "volume_packet",
        "runtime_entrypoint": "TRADING_ALGOS.machines:execute_volume_machine",
        "api_key_id": "collector-primary",
        "build_version_policy": "phase2-volume-family-semver",
        "owner": "Dollar_Bill",
        "warmup": {
            "1m": WarmupSpec(timedelta(minutes=20), timedelta(minutes=120), 20, "partial"),
            "5m": WarmupSpec(timedelta(minutes=100), timedelta(hours=12), 20, "partial"),
            "60m": WarmupSpec(timedelta(hours=20), timedelta(days=10), 20, "partial"),
        },
        "confidence_downgrade_rules": (
            "missing_relative_volume_baseline_caps_confidence_at_low",
            "incomplete_last_candle_caps_strength_at_medium",
            "partial_input_forces_partial",
        ),
        "retryable_failure_codes": (
            "READ_TIMEOUT",
            "PAGINATION_DRIFT",
            "FEATURE_ENGINE_FAILED",
        ),
    },
    "ELLIOTT": {
        "human_prefix": "Elliott + Trends + Patterns",
        "primary_output_packet": "elliott_packet",
        "runtime_entrypoint": "TRADING_ALGOS.machines:execute_elliott_machine",
        "api_key_id": "collector-primary",
        "build_version_policy": "phase2-elliott-family-semver",
        "owner": "Jusetta",
        "warmup": {
            "1m": WarmupSpec(timedelta(minutes=180), timedelta(hours=8), 60, "partial"),
            "5m": WarmupSpec(timedelta(hours=15), timedelta(days=4), 60, "partial"),
            "60m": WarmupSpec(timedelta(days=10), timedelta(days=45), 60, "partial"),
        },
        "confidence_downgrade_rules": (
            "default_confidence_is_low",
            "partial_or_gap_heavy_input_forces_low_confidence",
            "unclear_structure_must_not_emit_confirmed_labels",
        ),
        "retryable_failure_codes": (
            "READ_TIMEOUT",
            "PAGINATION_DRIFT",
            "FEATURE_ENGINE_FAILED",
        ),
    },
}

_TIMEFRAMES = ("1m", "5m", "60m")


def _machine_key(strategy: str, timeframe: str) -> str:
    return f"{strategy}_{timeframe.upper()}".lower()


def build_machine_registry() -> Mapping[str, MachineSpec]:
    registry: dict[str, MachineSpec] = {}
    for strategy, config in _STRATEGY_SPECS.items():
        for timeframe in _TIMEFRAMES:
            machine_key = _machine_key(strategy, timeframe)
            registry[machine_key] = MachineSpec(
                machine_id=machine_key,
                agent_id=machine_key,
                strategy=strategy,
                timeframe=timeframe,
                human_name=f"{config['human_prefix']} {timeframe}",
                input_timeframe_target=timeframe,
                primary_output_packet=config["primary_output_packet"],
                runtime_entrypoint=config["runtime_entrypoint"],
                api_key_id=config["api_key_id"],
                build_version_policy=config["build_version_policy"],
                owner=config["owner"],
                warmup=config["warmup"][timeframe],
                confidence_downgrade_rules=config["confidence_downgrade_rules"],
                retryable_failure_codes=config["retryable_failure_codes"],
            )
    return registry


MACHINE_REGISTRY = build_machine_registry()


def get_machine_spec(strategy: str, timeframe: str) -> MachineSpec:
    return MACHINE_REGISTRY[_machine_key(strategy, timeframe)]
