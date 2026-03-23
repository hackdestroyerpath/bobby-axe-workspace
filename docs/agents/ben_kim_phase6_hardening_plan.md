# Ben_Kim Phase 6 Hardening Plan

## Status
Focused hardening baseline.

## Purpose
Зафиксировать узкий и практический план Phase 6:
- что именно нужно усилить;
- в каком порядке;
- что считать Definition of Improvement;
- какие проблемы являются первыми targets.

---

# 1. Phase 6 goal

Цель Phase 6:
- не расширять аналитику,
- не добавлять новые стратегии,
- а усилить write/storage reliability вокруг уже работающего controlled execution.

Фокус Phase 6:
1. duplicate/idempotency behavior
2. batch transaction behavior
3. response accounting reliability
4. storage contamination policy

---

# 2. Why Phase 6 is needed

После Phase 5 уже доказано:
- analytical side strong enough;
- runtime gating strong enough;
- repeatable guarded loops possible.

Но также повторно доказано:
- duplicate conflicts are real;
- one write conflict can poison the batch transaction;
- API counters may not match durable DB state;
- canonical storage already contains legacy/test contamination.

Значит следующий правильный шаг:
- focused hardening,
а не blind continuation.

---

# 3. Hardening tracks

## Track H1 — duplicate/idempotency semantics

### Problem
Сейчас неясно и operationally опасно:
- что должно происходить при replay того же logical row;
- считать ли duplicate нормальным replay-case или hard failure;
- допускается ли safe upsert/update.

### Target
Нужно получить одну чёткую semantics-модель:
- duplicate = skip
или
- duplicate = update
или
- duplicate = reject but batch survives

### Minimum improvement
После hardening должно быть заранее понятно:
- что endpoint делает при duplicate;
- как это интерпретировать операторски;
- как это выглядит в response.

---

## Track H2 — batch transaction resilience

### Problem
Сейчас один duplicate может перевести остаток batch в:
- `current transaction is aborted`

### Target
Нужно добиться, чтобы batch path был устойчивее:
- либо per-row handling;
- либо safe partial handling;
- либо clean deterministic rollback semantics.

### Minimum improvement
После hardening batch response должен быть:
- понятным;
- root-cause oriented;
- без misleading cascade interpretation.

---

## Track H3 — response accounting trustworthiness

### Problem
Сейчас `stored_count` и фактический durable DB state не всегда совпадают.

### Target
Нужно добиться, чтобы API response был trustworthy enough for operators.

### Minimum improvement
После hardening response counters должны:
- отражать реальный durable outcome;
- не вводить в заблуждение при transaction failure;
- быть пригодными для operational reporting.

---

## Track H4 — storage contamination policy

### Problem
В `collector.analysis_results` уже есть legacy/test rows и naming drift.

### Target
Нужно ввести policy, которая отвечает:
- что считать canonical active row;
- что считать legacy/test artifact;
- как оператору отличать одно от другого.

### Minimum improvement
После hardening должно быть понятно:
- как интерпретировать старые загрязнённые строки;
- нужно ли их чистить, изолировать или просто маркировать.

---

# 4. Recommended order

## Priority order
1. duplicate/idempotency semantics
2. batch transaction resilience
3. response accounting trustworthiness
4. storage contamination policy

### Why this order
Первые три пункта влияют прямо на correctness write path.
Четвёртый нужен для cleanliness and interpretation.

---

# 5. Definition of Improvement by track

## H1 improved if
- duplicate handling rule documented
- duplicate runtime behavior reproduced and explained
- operator knows whether to retry / skip / update

## H2 improved if
- batch failure semantics documented
- first failure no longer creates misleading interpretation of remaining rows
- response clearly separates root cause from cascade

## H3 improved if
- response counters align with durable DB state
- operator can trust `stored/updated/rejected` semantics
- reconcile becomes exception, not default requirement

## H4 improved if
- canonical vs legacy rows are distinguishable
- naming drift is explainable
- storage interpretation no longer depends on guesswork

---

# 6. Practical execution rule for Phase 6

В Phase 6 работаем так:
- one hardening target at a time;
- one finding -> one artifact -> one conclusion;
- no broad refactors without need;
- no new analytical scope creep.

---

# 7. Canonical current status entering Phase 6

Entering Phase 6, correct status remains:
- `GO WITH WRITE CAUTION`

Phase 6 is successful only if it moves this status upward by improving write/storage trust.

---

# 8. First concrete next step

First concrete Phase 6 step:
- isolate exact duplicate/idempotency behavior as the first hardening target.

That means:
- document replay scenarios;
- define what should happen;
- compare with what currently happens.

---

# 9. Use

Этот документ использовать как:
- entry point for Phase 6;
- narrow hardening roadmap;
- guard against scope drift.
