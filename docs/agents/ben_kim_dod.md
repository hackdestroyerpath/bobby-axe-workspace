# Ben_Kim Definition of Done

## Status
Final baseline.

## Purpose
Канонический документ, который фиксирует, когда работа `Ben_Kim` считается завершённой:
- технически;
- аналитически;
- downstream-корректно.

---

# 1. Technical DoD

Технически execution `Ben_Kim` считается завершённым только если выполняются все условия ниже.

## T1. Snapshot identity fixed
Должны быть определены:
- `snapshot_id`
- `correlation_id`
- `symbol`

## T2. Snapshot passes readiness gate
Должно быть подтверждено:
- `frames.1m.status = ready`
- `frames.5m.status = ready`
- `frames.60m.status = ready`

## T3. Payload read through canonical path
Payload должен быть прочитан через approved source:
- centralized `/payload`

## T4. Strategy registry is canonical
Перед execution должны быть прочитаны:
- `strategy_id`
- `strategy_name`
из canonical registry source.

## T5. Payload validation passed
Payload не должен быть:
- partial;
- semantically broken;
- invalid for core strategy fields.

## T6. All 6 strategies executed
По тикеру должны быть реально обработаны все 6 canonical strategies.

## T7. All 3 frames covered
По тикеру должны быть conclusions для:
- `1m`
- `5m`
- `60m`

## T8. Full cardinality built
Для одного тикера при 6 стратегиях и 3 frames должно быть:
- `18 conclusions`

## T9. Canonical analysis_result built
Результат должен быть собран в canonical structured form.

## T10. Writeback sent through approved path
Результат должен быть отправлен через:
- `POST /analysis/write`

## T11. Writeback confirmed
Должен быть получен корректный write response.

## T12. Canonical stored layer updated
Результат должен появиться в:
- `collector.analysis_results`

## T13. Strategy identity preserved in storage
Stored row должна сохранять:
- `strategy_id`
- `strategy_name`

## T14. Downstream source is known
Должно быть понятно, что downstream читает canonical layer.

---

# 2. Analytical DoD

Аналитически execution `Ben_Kim` считается завершённым только если conclusions соответствуют качественным требованиям.

## A1. Conclusions are verifiable
Каждый conclusion должен опираться на наблюдаемые признаки из payload.

## A2. No fabricated signal
Нельзя выдумывать сильный сигнал там, где данные weak / candidate / mixed.

## A3. Strategy meaning preserved
Conclusion должен соответствовать смыслу своей стратегии.

## A4. Observation, implication, confidence discipline aligned
Conclusion должен содержать:
- observation basis;
- implication within strategy;
- confidence discipline.

## A5. Ready != strong signal
Frame readiness не должна путаться с силой сигнала.

## A6. Heuristic strategies stay cautious
Heuristic layers обязаны звучать осторожнее.

## A7. Placeholder stays non-analytical
`added_later_placeholder` не должна имитировать аналитику.

## A8. Conclusions stay concise and comparable
Формулировки должны быть:
- короткими;
- проверяемыми;
- сравнимыми.

## A9. Signal strength not inflated
Нельзя завышать сигнал сверх доказательной силы данных.

## A10. Weak/partial/unclear cases remain visible
Слабость сигнала должна быть видна в тексте.

## A11. Summary must not contradict base layer
Любая последующая агрегация не должна ломать исходные strategy/frame conclusions.

---

# 3. Downstream DoD

Execution `Ben_Kim` считается системно завершённым только если downstream использует слой корректно.

## D1. Downstream reads canonical source
Downstream должен читать:
- `collector.analysis_results`

## D2. Strategy identity preserved downstream
Downstream должен сохранять:
- `strategy_id`
- `strategy_name`

## D3. Cardinality preserved on canonical layer
Если Ben_Kim дал 18 conclusions, canonical downstream layer должен сохранять эти 18 logical units.

## D4. Summary is separated from canonical layer
Preview/summary/reporting допустимы только как derived layer.

## D5. Summary does not replace source of truth
Derived layer не должен маскироваться под canonical Ben_Kim result.

## D6. Snapshot binding preserved
Downstream artifacts должны сохранять:
- `snapshot_id`
- `symbol`

## D7. Frame binding preserved
Downstream не должен терять distinctions between:
- `1m`
- `5m`
- `60m`

## D8. Mock layers are not used as production source
Mock/test/preview layers не должны читаться как canonical production source.

## D9. Maffi reads analytical layer, not presentation layer
Decision-stage downstream должен читать strategy-level analytical rows.

## D10. Jusetta may present, but not rewrite source semantics
Presentation downstream может упаковывать, но не менять source semantics.

## D11. Weak/strong distinctions preserved downstream
Downstream не должен завышать силу сигнала относительно canonical layer.

## D12. Downstream remains verifiable
При споре должно быть возможно проверить:
- какой source читался;
- какой snapshot использовался;
- совпадает ли result с canonical stored rows.

---

# 4. Condensed DoD formula

## Technical completion
`usable snapshot -> payload -> 6 strategies x 3 frames -> 18 results -> canonical writeback -> stored layer`

## Analytical completion
`verifiable conclusions -> no overclaim -> strategy-specific meaning preserved -> weak cases visible`

## System completion
`downstream reads canonical source -> preserves strategy identity -> does not replace source with summary`

---

# 5. Operational use

Этот документ является baseline для:
- execution completion checks;
- pre-run discipline;
- pre-write discipline;
- downstream alignment.
