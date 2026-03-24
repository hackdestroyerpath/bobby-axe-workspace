# Maffi Readiness Matrix

Дата: 2026-03-24

## Statuses
- `ready`: validator passes, reject gate not triggered, deterministic output generated.
- `partial`: input degraded but usable; decision emitted with confidence penalty.
- `blocked`: hard reject or validation failure.

## Checkpoints
1. Contract v0.1 approved: ✅
2. Validator + decision engine skeleton: ✅
3. Deterministic replay helper: ✅
4. Unit scenarios (validator/scoring/reject/degraded): ✅ (implemented in `tests/test_maffi_decision_engine.py`)
5. E2E scenarios (good long/good short/bad reject/chaotic reject/degraded usable): ✅ (implemented in `tests/test_maffi_decision_engine.py`)

## Release caveat
Runtime ingestion from live collector into Maffi payload builder remains integration work.
