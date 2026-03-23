# Ben_Kim Repeatable Execution Checklist

## Status
Controlled-loop hardening baseline.

## Purpose
Зафиксировать, что должно быть true перед следующим clean controlled run `Ben_Kim`, чтобы повторяемый execution loop не опирался на предположения.

---

# 1. Goal of the checklist

Checklist нужен для ответа на вопрос:
- можно ли запускать следующий controlled loop как repeatable run,
или
- ещё рано, потому что write-path / storage path остаются недостаточно контролируемыми.

---

# 2. Mandatory readiness blocks

## Block A — snapshot/runtime readiness
Перед повторным run должно быть подтверждено:
- `snapshot_id` существует
- `symbol` существует
- `/lookup` работает
- `/payload` работает
- `payload_status = ready`
- `result_code = ok`
- `1m = ready`
- `5m = ready`
- `60m = ready`
- registry пришёл корректно
- registry содержит canonical strategy set

Если любой пункт не выполнен:
- repeatable clean run не запускать

---

## Block B — analytical readiness
Перед повторным run должно быть подтверждено:
- strategy rules остаются canonical
- conclusion wording не ушёл в drift
- signal discipline не ослаблен
- placeholder по-прежнему идёт как skipped/partial
- `18 conclusions` ожидаются как полный usable loop

Если любой пункт под вопросом:
- сначала устранить analytical drift

---

## Block C — live write contract readiness
Перед повторным run должно быть подтверждено:
- используется именно live contract shape
- `mode` задан
- `single`/`batch` выбраны осознанно
- для batch используется `analysis_results`
- item rows содержат `strategy_id + strategy_name`
- signal enum storage-safe
- status/result_code pair корректен

Если любой пункт не выполнен:
- write path считается not ready

---

# 3. Write-path safety checks before repeatable run

## Safety check S1 — duplicate risk known
Перед run нужно понимать:
- есть ли уже rows для этого `(snapshot_id, symbol, strategy, frame)`
- storage clean для target keyspace или нет

Если duplicate risk неизвестен:
- run нельзя считать clean repeatable loop

---

## Safety check S2 — legacy contamination understood
Перед run нужно понимать:
- есть ли в `collector.analysis_results` legacy/test rows для этого snapshot/symbol
- есть ли naming drift в старых rows

Если contamination не понятна:
- write outcome будет трудно интерпретировать

---

## Safety check S3 — reconcile plan prepared
Перед run нужно заранее понимать:
- как будет делаться post-write reconcile
- по каким полям будет проверяться durable outcome

Если reconcile plan отсутствует:
- важный batch write нельзя считать полностью контролируемым

---

# 4. Minimum criteria for a clean repeatable loop

Следующий loop можно считать clean repeatable run только если одновременно true:

1. runtime readiness passed
2. analytical readiness passed
3. live write contract shape fixed and explicit
4. duplicate risk assessed
5. legacy contamination assessed
6. reconcile plan prepared

Если хотя бы один пункт false:
- loop остаётся exploratory, а не repeatable-clean

---

# 5. Decision outcomes

## Outcome 1 — READY FOR REPEATABLE LOOP
Использовать только если:
- все readiness blocks passed
- write-path risks understood
- reconcile plan ready

## Outcome 2 — GO WITH WRITE CAUTION
Использовать если:
- analytical/runtime side готова
- но write-path still requires guarded interpretation

## Outcome 3 — NOT READY FOR REPEATABLE LOOP
Использовать если:
- duplicate risk unknown
- storage contamination unknown
- contract shape uncertain
- reconcile path absent

---

# 6. Practical operator sequence before next run

1. verify snapshot readiness
2. verify registry and canonical strategy set
3. verify live write contract shape
4. inspect duplicate/legacy risk in storage
5. define reconcile query/verification path
6. only then start next controlled run

---

# 7. Current assessment after first controlled run

После первого controlled run текущая оценка такая:

## Analytical side
- strong enough

## Runtime side
- strong enough

## Write contract
- now materialized

## Duplicate/idempotency semantics
- not yet fully hardened

## Storage cleanliness
- not clean enough

## Response trustworthiness
- not yet sufficient without reconcile

### Current practical outcome
- `GO WITH WRITE CAUTION`

---

# 8. What must improve before calling the next run truly clean-repeatable

Нужно улучшить минимум:
1. duplicate handling clarity
2. interpretation of existing storage contamination
3. confidence in write response vs durable DB state

---

# 9. Use

Этот checklist использовать как gate перед:
- second controlled single-ticker run
- future repeatable loop claims
- small batch controlled execution start.
