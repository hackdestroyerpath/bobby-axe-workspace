from __future__ import annotations

import unittest

from TRADING_ALGOS.ben_kim_packaging import (
    BATCH_ACCEPTANCE_BLOCKED,
    BATCH_ACCEPTANCE_DEGRADED,
    BATCH_COMPLETENESS_COMPLETE,
    BATCH_COMPLETENESS_INCOMPLETE,
    EXPECTED_BATCH_SIZE,
    OBJECT_STATUS_BLOCKED,
    OBJECT_STATUS_PARTIAL,
    OBJECT_STATUS_READY,
    assemble_symbol_batch,
    evaluate_batch_acceptance,
    load_symbol_object_schema,
    project_machine_response_to_symbol_object,
    validate_symbol_object_payload,
)
from TRADING_ALGOS.machine_registry import MACHINE_REGISTRY


class BenKimPackagingTests(unittest.TestCase):
    def test_project_machine_response_to_symbol_object_keeps_traceability_and_marks_ready(self) -> None:
        response = self._machine_response(machine_id="rsi_macd_1m", strategy="RSI_MACD", timeframe="1m")

        symbol_object = project_machine_response_to_symbol_object(response)

        self.assertEqual(symbol_object.machine_id, "rsi_macd_1m")
        self.assertEqual(symbol_object.request_id, response["request_id"])
        self.assertEqual(symbol_object.response_contract_version, "v1")
        self.assertEqual(symbol_object.summary["note"], response["summary"]["note"])
        self.assertEqual(symbol_object.features["signal"], response["features"]["signal"])
        self.assertEqual(symbol_object.object_readiness, OBJECT_STATUS_READY)
        self.assertEqual(validate_symbol_object_payload(symbol_object.as_dict()), [])

    def test_project_marks_partial_objects_when_runtime_status_is_partial(self) -> None:
        response = self._machine_response(
            machine_id="volume_5m",
            strategy="VOLUME",
            timeframe="5m",
            status="partial",
            partial_reason="pagination_truncation",
        )

        symbol_object = project_machine_response_to_symbol_object(response)

        self.assertEqual(symbol_object.object_readiness, OBJECT_STATUS_PARTIAL)
        self.assertEqual(symbol_object.meta["partial_reason"], "pagination_truncation")

    def test_project_blocks_error_packets_for_storage_handoff(self) -> None:
        response = self._machine_response(
            machine_id="elliott_1m",
            strategy="ELLIOTT",
            timeframe="1m",
            status="error",
            include_features=False,
            errors=[
                {
                    "code": "FEATURE_ENGINE_FAILED",
                    "message": "compute failed",
                    "severity": "error",
                    "scope": "features",
                    "retryable": True,
                }
            ],
        )

        symbol_object = project_machine_response_to_symbol_object(response)

        self.assertEqual(symbol_object.object_readiness, OBJECT_STATUS_BLOCKED)
        self.assertIn("FEATURE_ENGINE_FAILED", {error["code"] for error in symbol_object.errors})

    def test_assemble_symbol_batch_builds_exact_12_object_package_in_frozen_order(self) -> None:
        responses = [
            self._machine_response(machine_id=machine_id, strategy=spec.strategy, timeframe=spec.timeframe)
            for machine_id, spec in MACHINE_REGISTRY.items()
        ]

        batch = assemble_symbol_batch("BTCUSDC", responses)

        self.assertEqual(len(batch.objects), EXPECTED_BATCH_SIZE)
        self.assertEqual(batch.acceptance.completeness, BATCH_COMPLETENESS_COMPLETE)
        self.assertTrue(batch.acceptance.is_handoff_ready)
        self.assertEqual(tuple(obj.machine_id for obj in batch.objects), tuple(MACHINE_REGISTRY))

    def test_batch_acceptance_marks_complete_batch_with_partial_objects_as_degraded(self) -> None:
        responses = []
        for machine_id, spec in MACHINE_REGISTRY.items():
            if machine_id == "volume_60m":
                responses.append(
                    self._machine_response(
                        machine_id=machine_id,
                        strategy=spec.strategy,
                        timeframe=spec.timeframe,
                        status="partial",
                        partial_reason="retention_truncation",
                    )
                )
            else:
                responses.append(self._machine_response(machine_id=machine_id, strategy=spec.strategy, timeframe=spec.timeframe))

        batch = assemble_symbol_batch("BTCUSDC", responses)

        self.assertEqual(batch.acceptance.completeness, BATCH_COMPLETENESS_COMPLETE)
        self.assertEqual(batch.acceptance.acceptance_status, BATCH_ACCEPTANCE_DEGRADED)
        self.assertIn("volume_60m", batch.acceptance.partial_machine_ids)
        self.assertTrue(batch.acceptance.is_handoff_ready)

    def test_batch_acceptance_blocks_incomplete_batch(self) -> None:
        responses = [
            self._machine_response(machine_id=machine_id, strategy=spec.strategy, timeframe=spec.timeframe)
            for machine_id, spec in list(MACHINE_REGISTRY.items())[:-1]
        ]
        objects = tuple(project_machine_response_to_symbol_object(response) for response in responses)

        verdict = evaluate_batch_acceptance("BTCUSDC", objects)

        self.assertEqual(verdict.completeness, BATCH_COMPLETENESS_INCOMPLETE)
        self.assertEqual(verdict.acceptance_status, BATCH_ACCEPTANCE_BLOCKED)
        self.assertFalse(verdict.is_handoff_ready)
        self.assertEqual(len(verdict.missing_machine_ids), 1)

    def test_symbol_object_schema_file_is_loadable(self) -> None:
        schema = load_symbol_object_schema()

        self.assertEqual(schema["title"], "Ben_Kim Symbol Object")
        self.assertIn("object_readiness", schema["required"])

    @staticmethod
    def _machine_response(
        *,
        machine_id: str,
        strategy: str,
        timeframe: str,
        status: str = "ready",
        partial_reason: str | None = None,
        include_features: bool = True,
        errors: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        meta = {
            "data_points": 128,
            "is_partial": status == "partial",
            "partial_reason": partial_reason,
            "coverage_ratio": 0.82 if status == "partial" else 1.0,
            "source_contract_version": "tick-source-v1",
            "build_version": "phase3.0",
            "api_key_id": MACHINE_REGISTRY[machine_id].api_key_id,
            "machine_id": machine_id,
        }
        payload_errors = errors or ([] if status != "error" else [
            {
                "code": "EMPTY_WINDOW",
                "message": "no data",
                "severity": "warning",
                "scope": "read",
                "retryable": False,
            }
        ])
        return {
            "request_id": f"req-{machine_id}",
            "agent_id": machine_id,
            "strategy": strategy,
            "timeframe": timeframe,
            "symbol": "BTCUSDC",
            "source": "Data_collector",
            "requested_at": "2026-03-23T10:15:00Z",
            "generated_at": "2026-03-23T10:15:02Z",
            "response_contract_version": "v1",
            "status": status,
            "input_window": {
                "from": "2026-03-23T09:00:00Z",
                "to": "2026-03-23T10:15:00Z",
            },
            "features": {"signal": "buy"} if include_features else {},
            "summary": {
                "state": "bullish",
                "strength": "medium",
                "confidence": "medium",
                "note": "packaging test payload",
            },
            "meta": meta,
            "errors": payload_errors,
        }


if __name__ == "__main__":
    unittest.main()
