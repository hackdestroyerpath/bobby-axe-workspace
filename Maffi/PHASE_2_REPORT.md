# Maffi Phase 2 Report

Дата: 2026-03-24

## Delivered
- Contract-first input/output model (`maffi.models`, `Maffi/CONTRACT_V0_1.md`).
- Structural + semantic + cross-field validator (`maffi.validator`).
- Preprocessing building blocks:
  - tick sanitation,
  - volatility features,
  - order-flow features.
- Composite decision/scoring layer (`maffi.decision_engine`): reject gate, long/short scoring, confidence penalty.
- Candidate selection and TP/SL policy (deterministic).
- Explainability and machine-readable decision trace included in output.
- Deterministic replay helper (`maffi.replay`).

## Quality matrix
- `input_quality_status=ok` + valid payload + low reject score -> decision `long|short`.
- `input_quality_status=degraded` -> still tradable, confidence penalty.
- `input_quality_status=bad` OR schema invalid OR high reject score -> `reject`.

## Risks
- Regime classifier currently assumed from payload; auto-classifier integration is still minimal.
- Full 1m/5m/15m OHLC aggregation is not yet wired into runtime pipeline.
