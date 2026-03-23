# Ben_Kim Duplicate = Skip Verification Plan

## Status
Phase 6 verification plan.

## Purpose
Зафиксировать, как practically проверять, что behavioral change
- `duplicate = skip`

реально произошёл, а не остался только на уровне документации.

---

# 1. Verification goal

Проверка должна ответить на один главный вопрос:
- изменился ли фактический write-path behavior на replay scenario?

Не wording,
не explanation,
а именно runtime behavior.

---

# 2. Core replay scenario

## Scenario V1 — mixed batch replay with known duplicate
Нужен batch, в котором:
- хотя бы один logical row уже существует
- хотя бы один другой row остаётся non-conflicting

Это лучший practical case, потому что он показывает одновременно:
1. как system трактует duplicate
2. отравляет ли duplicate остальную часть batch
3. как response читает mixed outcome

---

# 3. Expected success behavior

If `duplicate = skip` is truly working, expected behavior is:

## E1
Duplicate row is not treated as hard failure.

## E2
Duplicate row does not push the rest of batch into transaction-aborted cascade semantics.

## E3
Non-conflicting rows still proceed normally.

## E4
Response distinguishes duplicate/skipped from true failures.

## E5
Operator can read mixed outcome without major guesswork.

---

# 4. Minimum expected evidence

Verification should produce evidence in three layers.

## Layer A — response evidence
Response should show that duplicate is its own class or clearly non-failure class.

## Layer B — batch behavior evidence
The rest of batch should not collapse into old cascade pattern.

## Layer C — durable-state evidence
Post-write reconcile should confirm that:
- non-conflicting rows behaved as expected
- duplicate rows did not create misleading durable interpretation

---

# 5. Failure signs

The verification should be considered failed if any of the following still happens.

## F1
Duplicate still appears as ordinary hard failure.

## F2
Duplicate still causes `transaction aborted` tail behavior for remaining rows.

## F3
Response still mixes duplicate with failure ambiguity.

## F4
Operator still cannot tell from response whether mixed batch outcome is safe.

---

# 6. Practical test sequence

1. choose a keyspace with known existing logical row
2. prepare mixed batch with:
   - duplicate row
   - non-conflicting rows
3. execute write
4. inspect response semantics
5. inspect whether cascade occurred
6. run reconcile
7. compare observed behavior against expected success behavior

---

# 7. What counts as real success

Real success is not:
- fewer scary words in response
- different phrasing in docs
- softer interpretation of the same failure pattern

Real success is:
- duplicate no longer behaves like the old poison path
- mixed batch remains operationally legible
- response and reconcile together confirm the new semantics

---

# 8. Final short rule

If behavior on mixed replay scenario does not change, then `duplicate = skip` is not yet implemented in any operationally meaningful way.

---

# 9. Use

Этот plan использовать как:
- first practical verification baseline after H1 decision;
- bridge from policy note to runtime validation;
- anti-self-deception check before claiming duplicate semantics improved.
