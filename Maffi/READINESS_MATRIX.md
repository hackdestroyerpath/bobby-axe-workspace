# Maffi Readiness Matrix

Дата: 2026-03-24

## Statuses
- `ready`: payload builder собрал полный `MaffiInputPayload`, validator passes, reject gate not triggered, deterministic output generated.
- `partial`: input degraded but usable (`input_quality_status=degraded`), decision emitted with confidence penalty.
- `blocked`: hard reject (`input_quality_status=bad`, `reject_score>=60`) или validation failure.

## Checkpoints
1. Contract v0.1 approved: ✅
2. Validator + decision engine skeleton: ✅
3. Deterministic replay helper: ✅
4. Payload builder integration (`maffi/payload_builder.py`): ✅
5. Explicit degradation rules (empty/heavy gaps/truncation/coverage): ✅
6. Machine-readable degradation trace in `context`: ✅
7. Unit + integration scenarios (healthy/degraded/reject): ✅ (`tests/test_maffi_decision_engine.py`, `tests/test_maffi_payload_builder.py`)

## Release caveat
- Runtime wiring from orchestration layer into live Maffi execution still requires explicit call-site integration.
