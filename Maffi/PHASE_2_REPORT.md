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
- **New:** payload builder (`maffi.payload_builder`) wired to `new_collector` tick shape and `TRADING_ALGOS/common` normalization + candle feature engine.
- **New:** explicit degradation policy with machine-readable trace reasons:
  - empty window,
  - heavy gaps,
  - truncation (retention/pagination),
  - low coverage.
- **New:** integration tests for payload assembly (`tests/test_maffi_payload_builder.py`) with healthy/degraded/reject fixtures.

## Quality matrix
- `input_quality_status=ok` + valid payload + low reject score -> decision `long|short`.
- `input_quality_status=degraded` -> still tradable, confidence penalty.
- `input_quality_status=bad` OR schema invalid OR high reject score -> `reject`.

## Risks
- Regime/scoring calibration is heuristic and should be re-tuned on live distributions.
- Full runtime orchestration path (Ben_Kim aggregate -> Maffi builder -> Maffi decide) is not yet wired by default entrypoint.
