# Maffi — PHASE 1 ACCEPTANCE

Дата: 2026-03-24

Документ фиксирует только автоматически проверяемые acceptance-критерии для Phase 1 после внедрения `contract-v1/grid/validator`.

---

## Acceptance matrix (требование → тест-кейс → artifact output/trace)

| ID | Требование | Тест-кейс (авто) | Проверяемый artifact output/trace |
|---|---|---|---|
| DR-100 | Deterministic replay: одинаковый payload даёт identical output + identical decision_trace в 100/100 прогонах | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_deterministic_replay_100_runs_identical` | `MaffiOutput` equality + `decision_trace` equality |
| VC-REQ | Validator required fields: missing required field => invalid + error severity | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_validator_rejects_missing_required_field` | `validation_summary.counts`, `errors[*].severity`, validator `trace.counts` |
| VC-SEV | Validator severity distribution: error/warning/degrade учитываются раздельно | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_validator_trace_has_severity_distribution_contract` | `decision_trace.validation.severity_distribution`, `degrade_score`, `reasons[*].severity` |
| DQ-OK | Decision quality для `long/short`: confidence floor на healthy input | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_good_long_scenario` + `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_good_short_scenario` | `decision`, `confidence`, `decision_summary.direction`, `tp/sl` |
| DQ-DEG | Decision quality для degraded input: решение остаётся usable + confidence penalty | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_degraded_input_remains_usable_with_penalty` | `validation_summary.degrade`, `top_reasons`, `confidence` |
| GRID-60 | Grid scoring: выбранный candidate имеет `efficiency_score >= 0.60` | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_efficiency_score_floor_from_canonical_payload_fixture` | `efficiency_score`, `decision_trace.selection.selected_candidate_id` |
| GRID-DET | Grid ranking deterministic against fixture | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_grid_scoring_ranking_is_deterministic_against_fixture` | ranked candidate ids + selected candidate id |
| RP-95 | Reject policy: на негативном наборе (20 кейсов) корректных reject >= 95% | `tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_negative_batch_correct_reject_ratio_at_least_95_percent` | `decision=reject`, `reject_reason`, computed reject ratio |
| E2E-BRIDGE-01 | Bridge pipeline проходит без ручных фиксов payload + mapping contract соблюдён | `tests/test_maffi_orchestration_bridge.py::MaffiOrchestrationBridgeTests::test_e2e_machine_response_to_symbol_object_to_payload_to_decision` + `tests/test_maffi_orchestration_bridge.py::MaffiOrchestrationBridgeTests::test_e2e_batch_bridge_respects_partial_status_and_contract_mapping` | payload schema/quality fields, `BRIDGE_MAPPING_CONTRACT`, runtime decision |
| CONTRACT-V1 | Финальный output соответствует contract-v1 shape | `tests/test_maffi_contract_v1.py::MaffiContractV1Tests::test_long_short_reject_outputs_follow_contract_v1_shape` + `tests/test_maffi_contract_v1.py::MaffiContractV1Tests::test_final_output_fixture_matches_contract_v1_shape` | `validation_summary`, `decision_summary`, `decision_trace.steps` contract fields |

---

## Test-file references (фактические)

- `tests/test_maffi_decision_engine.py`
- `tests/test_maffi_orchestration_bridge.py`
- `tests/test_maffi_contract_v1.py`

---

## Runbook (минимальный набор команд)

```bash
pytest -q tests/test_maffi_decision_engine.py
pytest -q tests/test_maffi_orchestration_bridge.py
pytest -q tests/test_maffi_contract_v1.py
```

---

## Phase 1 acceptance decision rule

Phase 1 принимается только если все тест-кейсы в acceptance matrix выше зелёные в CI.

Критерии без автоматической проверки в этом документе не фиксируются.
