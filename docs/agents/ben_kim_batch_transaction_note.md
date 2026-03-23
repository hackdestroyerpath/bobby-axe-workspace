# Ben_Kim Batch Transaction Behavior Note

## Status
Phase 6 hardening note.

## Purpose
Зафиксировать текущее batch transaction behavior write-path `Ben_Kim`:
- что происходит после first failure;
- как отделять root cause от cascade;
- каким должно быть minimally acceptable batch behavior.

---

# 1. Why this note exists

После двух controlled loops стало ясно:
- проблема не только в duplicate itself;
- проблема в том, как batch path ведёт себя после первой ошибки.

Поэтому batch transaction semantics нужно фиксировать отдельно от duplicate semantics.

---

# 2. Current observed pattern

## Observed pattern B1
Batch starts processing rows.

## Observed pattern B2
First meaningful write error appears.

Например:
- unique constraint violation

## Observed pattern B3
After that, many later rows return:
- `current transaction is aborted, commands ignored until end of transaction block`

Это означает, что remaining errors are mostly cascade effects, not independent root causes.

---

# 3. Root cause vs cascade

## Root cause
Первая содержательная ошибка batch-а.

Например:
- duplicate conflict on unique key
- validation failure for one item
- write-side DB exception for one item

## Cascade
Все последующие ошибки, которые возникли потому, что transaction уже испорчена.

### Practical rule
В batch failure analysis:
- искать first real error first;
- не трактовать tail of aborted-transaction errors как набор независимых проблем.

---

# 4. Why current behavior is operationally weak

## Weakness T1
One row can poison interpretation of all later rows.

## Weakness T2
Operator sees many errors, but most are not informative.

## Weakness T3
Response may look more granular than the transaction reality really is.

## Weakness T4
The batch path is not resilient enough for replay-heavy or partially duplicated conditions.

---

# 5. Minimally acceptable batch behavior

Даже если write path остаётся strict, minimally acceptable behavior should satisfy at least one of the following models.

## Model M1 — per-row isolation
Each row is processed independently enough that one failure does not poison the rest.

## Model M2 — clean grouped rollback semantics
If whole batch must fail atomically, response should clearly say:
- root cause
- whole batch rolled back
- no ambiguous partial counters

## Model M3 — partial-safe handling
Non-conflicting rows still finish, and conflicting rows are reported distinctly.

---

# 6. What current behavior most resembles

Current behavior most resembles:
- partial processing with weak transaction clarity

because:
- response reports partial counters;
- but actual durable outcome is not self-evident;
- cascade errors obscure row-level interpretation.

---

# 7. Exact gap in current batch semantics

## Gap T1
Root cause is present, but not cleanly separated from cascade in the operator-facing result.

## Gap T2
Transaction outcome is not intuitive enough from response alone.

## Gap T3
Batch semantics are not cleanly one of:
- atomic rollback
- per-row isolation
- safe partial processing

This ambiguity is the core problem.

---

# 8. Current operator rule

Until hardening is complete:
1. identify first real error
2. treat later `transaction aborted` rows as cascade
3. do not over-interpret per-row tail errors
4. reconcile after important partial writes
5. do not assume response granularity equals durable granularity

---

# 9. Improvement target for this track

This track is improved only if:
1. batch semantics are explicitly defined
2. root cause is clearly visible in response/operator flow
3. cascade errors no longer dominate interpretation
4. durable outcome is understandable without guesswork

---

# 10. Current status of this track

Current status:
- batch transaction behavior is understood
- but not yet acceptable for strong operational trust

Therefore this track remains:
- open

---

# 11. Use

Этот note использовать как:
- batch semantics baseline;
- root-cause vs cascade reference;
- input into write-path resilience hardening.
