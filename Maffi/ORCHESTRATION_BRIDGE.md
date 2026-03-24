# Maffi Orchestration Bridge Contract

Статус: implementation contract (Ben_Kim -> Maffi), версия `v0.1`.

## Scope
Bridge переводит:
- `BenKimSymbolObject` -> `MaffiInputPayload`
- `BenKimBatch` (12 машин) -> агрегированный `MaffiInputPayload`

Реализация: `maffi/bridge.py`.

## Fixed mapping contract

### 1) Поля, влияющие на `scores`
Bridge использует только следующие источники:
- `summary.state`
- `summary.strength`
- `summary.confidence`
- `meta.is_partial`
- `meta.partial_reason`
- `meta.coverage_ratio`
- `features.momentum_state`
- `features.structure_state`
- `features.pressure_side`
- `features.elliott_direction_candidate`
- `features.elliott_confidence_state`

Как это применяется:
- `summary.state` -> directional bias (`bullish/up/buyers` в long, `bearish/down/sellers` в short).
- `summary.strength` и `summary.confidence` -> multipliers веса голоса машины.
- `timeframe` (`60m > 5m > 1m`) -> старший tf имеет больший вес.
- partial/blocked статусы через `meta.*` и readiness штрафуют вклад в итоговые `long_score/short_score`.

### 2) Поля, влияющие на `quality_status`
Bridge использует:
- `status`
- `object_readiness`
- `meta.is_partial`
- `meta.partial_reason`
- `meta.coverage_ratio`
- `errors[*].severity`
- `errors[*].code`

Правила:
- любой `error`/`blocked` -> `input_quality_status=bad`
- любой partial (`object_readiness=partial`, `meta.is_partial=true`, низкий `coverage_ratio`) -> `degraded`
- иначе -> `ok`

### 3) Поля, влияющие на `candidates`
Bridge строит `support/resistance/entry_candidates` из:
- `features.nearest_support`
- `features.nearest_resistance`
- `features.nearest_fib_level`
- `features.hv_poc`
- `features.distance_to_support`
- `features.distance_to_resistance`

Правила:
- support = минимум валидных support/fib уровней
- resistance = максимум валидных resistance
- `last_price` берется как медиана валидных `hv_poc` (или midpoint support/resistance)
- `atr` = `(resistance - support) / 6`
- `entry_candidates` = `[last_price-atr, last_price, last_price+atr]` с зажимом в коридор support/resistance

## Batch semantics
- Для batch bridge агрегирует все объекты в один payload для `maffi.decide`.
- `generated_at_utc` берется как максимум `generated_at` среди объектов.
- `source` для batch фиксируется как `Ben_Kim_orchestration`.
- Trace bridge пишется в `context.bridge`:
  - mapping contract
  - число объектов
  - readiness breakdown
  - метаданные по каждой машине

## End-to-end pipeline
1. machine runtime response
2. `project_machine_response_to_symbol_object(...)`
3. `batch_to_maffi_payload(...)` или `symbol_object_to_maffi_payload(...)`
4. `payload_to_dict(...)`
5. `maffi.decide(...)`

## Compatibility
- Target schema: `maffi-v0.1`
- Bridge детерминирован для одинакового входного symbol object/batch.
