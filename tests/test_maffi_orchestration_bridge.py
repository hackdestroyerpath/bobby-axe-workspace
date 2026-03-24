from __future__ import annotations

import unittest

from TRADING_ALGOS.ben_kim_packaging import assemble_symbol_batch, project_machine_response_to_symbol_object
from TRADING_ALGOS.machine_registry import MACHINE_REGISTRY
from Maffi.runtime import decide
from Maffi.runtime.bridge import (
    BRIDGE_MAPPING_CONTRACT,
    batch_to_maffi_payload,
    payload_dict_from_batch,
    payload_dict_from_symbol_object,
)
from Maffi.runtime.enums import Decision, QualityStatus


class MaffiOrchestrationBridgeTests(unittest.TestCase):
    def test_e2e_machine_response_to_symbol_object_to_payload_to_decision(self) -> None:
        machine_response = _machine_response(
            machine_id="rsi_macd_1m",
            strategy="RSI_MACD",
            timeframe="1m",
            state="bullish",
            strength="strong",
            confidence="high",
        )

        symbol_object = project_machine_response_to_symbol_object(machine_response)
        payload = payload_dict_from_symbol_object(symbol_object)
        output = decide(payload)

        self.assertEqual(payload["schema_version"], "maffi-v0.1")
        self.assertEqual(payload["symbol"], "BTCUSDC")
        self.assertEqual(payload["input_quality_status"], QualityStatus.OK.value)
        self.assertGreater(payload["long_score"], payload["short_score"])
        self.assertEqual(output.decision, Decision.LONG)
        self.assertIsNone(output.reject_reason)

    def test_e2e_batch_bridge_respects_partial_status_and_contract_mapping(self) -> None:
        responses = []
        for machine_id, spec in MACHINE_REGISTRY.items():
            if machine_id == "volume_5m":
                responses.append(
                    _machine_response(
                        machine_id=machine_id,
                        strategy=spec.strategy,
                        timeframe=spec.timeframe,
                        status="partial",
                        partial_reason="pagination_truncation",
                        state="bullish",
                        strength="medium",
                    )
                )
            else:
                responses.append(
                    _machine_response(
                        machine_id=machine_id,
                        strategy=spec.strategy,
                        timeframe=spec.timeframe,
                        state="bullish",
                        strength="medium",
                    )
                )

        batch = assemble_symbol_batch("BTCUSDC", responses)
        maffi_payload = batch_to_maffi_payload(batch)
        payload_dict = payload_dict_from_batch(batch)
        output = decide(payload_dict)

        self.assertEqual(maffi_payload.input_quality_status, QualityStatus.DEGRADED)
        self.assertLess(payload_dict["reject_score"], 60)
        self.assertEqual(set(BRIDGE_MAPPING_CONTRACT), {"scores", "quality_status", "candidates"})
        self.assertIn(output.decision, {Decision.LONG, Decision.SHORT})


def _machine_response(
    *,
    machine_id: str,
    strategy: str,
    timeframe: str,
    status: str = "ready",
    partial_reason: str | None = None,
    state: str = "bullish",
    strength: str = "medium",
    confidence: str = "medium",
) -> dict[str, object]:
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
        "features": {
            "summary_state": state,
            "summary_strength": strength,
            "nearest_support": "86980",
            "nearest_resistance": "87640",
            "nearest_fib_level": "87200",
            "hv_poc": "87260",
            "distance_to_support": "280",
            "distance_to_resistance": "380",
            "pressure_side": "buyers" if state in {"bullish", "buyers", "up"} else "sellers",
            "trend_state": "up" if state in {"bullish", "buyers", "up"} else "down",
            "elliott_direction_candidate": "up" if state in {"bullish", "buyers", "up"} else "down",
            "elliott_confidence_state": "medium",
            "momentum_state": state,
            "structure_state": state,
        },
        "summary": {
            "state": state,
            "strength": strength,
            "confidence": confidence,
            "note": "bridge integration fixture",
        },
        "meta": {
            "data_points": 128,
            "is_partial": status == "partial",
            "partial_reason": partial_reason,
            "coverage_ratio": 0.84 if status == "partial" else 1.0,
            "source_contract_version": "tick-source-v1",
            "build_version": "phase3.0",
            "api_key_id": MACHINE_REGISTRY[machine_id].api_key_id,
            "machine_id": machine_id,
        },
        "errors": [],
    }


if __name__ == "__main__":
    unittest.main()
