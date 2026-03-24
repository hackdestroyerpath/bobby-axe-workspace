from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from types import MappingProxyType
import unittest

from TRADING_ALGOS.machine_registry import MACHINE_REGISTRY, MachineSpec
from TRADING_ALGOS.runtime_contract import (
    STATUS_ERROR,
    STATUS_PARTIAL,
    STATUS_READY,
    validate_response_payload,
)
from tests.fixtures.btc_baseline import (
    canonical_baseline_ticks,
    gap_heavy_baseline_ticks,
)


RESPONSE_REQUIRED_KEYS = {
    "request_id",
    "agent_id",
    "strategy",
    "timeframe",
    "symbol",
    "source",
    "requested_at",
    "generated_at",
    "response_contract_version",
    "status",
    "input_window",
    "features",
    "summary",
    "meta",
    "errors",
}


def _execute_registry_machine(
    machine_spec: MachineSpec,
    *,
    ticks: list[dict[str, str]],
    options: dict[str, bool] | None = None,
    kwargs: dict[str, object] | None = None,
) -> dict[str, object]:
    """Single registry-driven runner for all machine specs."""

    module_name, function_name = machine_spec.runtime_entrypoint.split(":", maxsplit=1)
    executor_fn = getattr(import_module(module_name), function_name)
    request = {
        "request_id": f"phase3-{machine_spec.machine_id}",
        "agent_id": machine_spec.agent_id,
        "strategy": machine_spec.strategy,
        "timeframe": machine_spec.timeframe,
        "symbol": "BTCUSDC",
        "source": "Data_collector",
        "requested_at": "2026-03-23T10:15:00Z",
        "input_window": {
            "from": "2026-03-20T00:00:00Z",
            "to": "2026-03-23T00:00:00Z",
        },
        "response_contract_version": "v1",
        "source_contract_version": "tick-source-v1",
        "options": {
            "strict_mode": False,
            "include_incomplete_candle": False,
            **(options or {}),
        },
    }
    runtime_kwargs = {
        "gap_threshold": _non_gap_heavy_threshold(machine_spec.timeframe),
        **(kwargs or {}),
    }
    return executor_fn(request, ticks, **runtime_kwargs)


def _non_gap_heavy_threshold(timeframe: str) -> timedelta:
    return {
        "1m": timedelta(minutes=2),
        "5m": timedelta(minutes=10),
        "60m": timedelta(hours=2),
    }[timeframe]


class Phase3IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = MappingProxyType(dict(MACHINE_REGISTRY))
        cls.canonical_ticks = canonical_baseline_ticks()
        cls.gap_heavy_ticks = gap_heavy_baseline_ticks()

    def test_canonical_baseline_and_readiness_verdict_for_all_12_machines(self) -> None:
        verdict_by_machine: dict[str, str] = {}

        for machine_id, machine_spec in self.registry.items():
            response = _execute_registry_machine(machine_spec, ticks=self.canonical_ticks)
            verdict_by_machine[machine_id] = str(response["status"])

            self.assertEqual(response["symbol"], "BTCUSDC")
            self.assertEqual(response["status"], STATUS_READY)
            self.assertEqual(response["meta"]["machine_id"], machine_id)
            self.assertFalse(response["meta"]["is_partial"])
            self.assertGreater(len(response["features"]), 0)

        self.assertEqual(set(verdict_by_machine), set(self.registry))
        self.assertEqual(set(verdict_by_machine.values()), {STATUS_READY})

    def test_contract_completeness_matrix_across_12_outputs(self) -> None:
        matrix: dict[str, dict[str, bool]] = {}

        for machine_id, machine_spec in self.registry.items():
            response = _execute_registry_machine(machine_spec, ticks=self.canonical_ticks)
            schema_errors = validate_response_payload(response)
            matrix[machine_id] = {
                "top_level_contract_complete": RESPONSE_REQUIRED_KEYS.issubset(response.keys()),
                "meta_traceability_complete": {"machine_id", "api_key_id", "build_version", "source_contract_version"}.issubset(
                    response["meta"].keys()
                ),
                "summary_complete": {"state", "strength", "confidence", "note"}.issubset(response["summary"].keys()),
                "schema_valid": not schema_errors,
            }

        self.assertEqual(len(matrix), 12)
        for checks in matrix.values():
            self.assertTrue(all(checks.values()), checks)

    def test_status_honesty_for_retention_pagination_gap_and_empty_windows(self) -> None:
        for machine_spec in self.registry.values():
            retention_response = _execute_registry_machine(
                machine_spec,
                ticks=self.canonical_ticks,
                kwargs={
                    "retention_floor": datetime(2026, 3, 22, 0, 0, tzinfo=timezone.utc),
                    "gap_threshold": timedelta(minutes=1),
                },
            )
            self.assertEqual(retention_response["status"], STATUS_PARTIAL)
            self.assertEqual(retention_response["meta"]["partial_reason"], "retention_truncation")

            pagination_response = _execute_registry_machine(
                machine_spec,
                ticks=self.canonical_ticks,
                kwargs={"page_complete": False, "gap_threshold": timedelta(minutes=1)},
            )
            self.assertEqual(pagination_response["status"], STATUS_PARTIAL)
            self.assertEqual(pagination_response["meta"]["partial_reason"], "pagination_truncation")

            gap_heavy_response = _execute_registry_machine(
                machine_spec,
                ticks=self.gap_heavy_ticks,
                kwargs={"gap_threshold": _gap_heavy_threshold(machine_spec.timeframe)},
            )
            self.assertEqual(gap_heavy_response["status"], STATUS_PARTIAL)
            self.assertEqual(gap_heavy_response["meta"]["partial_reason"], "gap_heavy_window")

            empty_response = _execute_registry_machine(
                machine_spec,
                ticks=[],
            )
            self.assertEqual(empty_response["status"], STATUS_ERROR)
            self.assertTrue(any(error["code"] == "EMPTY_WINDOW" for error in empty_response["errors"]))

    def test_warmup_validation_for_all_four_strategy_families(self) -> None:
        strategy_minimums = {
            "RSI_MACD": 10,
            "LEVELS_FIBO_HV": 10,
            "VOLUME": 10,
            "ELLIOTT": 10,
        }

        family_seen: set[str] = set()
        for machine_spec in self.registry.values():
            if machine_spec.timeframe != "1m":
                continue

            family_seen.add(machine_spec.strategy)
            reduced_ticks = self.canonical_ticks[-strategy_minimums[machine_spec.strategy] :]
            response = _execute_registry_machine(machine_spec, ticks=reduced_ticks)

            self.assertEqual(response["status"], STATUS_PARTIAL)
            self.assertEqual(response["meta"]["partial_reason"], "insufficient_warmup")
            self.assertTrue(any(error["code"] == "INSUFFICIENT_WARMUP" for error in response["errors"]))

        self.assertEqual(family_seen, {"RSI_MACD", "LEVELS_FIBO_HV", "VOLUME", "ELLIOTT"})


def _gap_heavy_threshold(timeframe: str) -> timedelta:
    return {
        "1m": timedelta(seconds=30),
        "5m": timedelta(minutes=2),
        "60m": timedelta(minutes=2),
    }[timeframe]


if __name__ == "__main__":
    unittest.main()
