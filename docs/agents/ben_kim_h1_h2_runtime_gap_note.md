# Ben_Kim H1/H2 Runtime Gap Note

## Status
Phase 6 runtime-gap note.

## Purpose
Зафиксировать точное расхождение между:
- выбранной target model для H1/H2
и
- фактическим live runtime behavior, подтверждённым validation scenario.

---

# 1. Target model

## H1 target
- `duplicate = skip`

## H2 target
- `safe partial processing`

Вместе это должно было означать:
- duplicate row не считается hard failure
- duplicate row не poison-ит batch
- non-conflicting rows продолжают processing
- response различает duplicate-skipped и true failures

---

# 2. Validation scenario used

Runtime validation scenario был таким:
- mixed batch
- 1 known duplicate row
- 1 intended non-conflicting row

Duplicate candidate:
- `rsi_macd | 1m`

Non-conflicting candidate:
- `trade_speed | 60m`

Goal:
- проверить, changed ли actual runtime behavior toward chosen H1/H2 model.

---

# 3. Actual observed behavior

## Response
- `status = error`
- `accepted_count = 2`
- `stored_count = 0`
- `updated_count = 0`
- `rejected_count = 2`

## Per-row outcome
### Row 1
Duplicate returned as:
- hard write error
- unique constraint violation

### Row 2
Second row returned as:
- `current transaction is aborted`

## Reconcile
- no new durable rows appeared

---

# 4. Exact gaps

## Gap G1 — duplicate is still in hard-failure lane
Expected:
- duplicate -> skip/non-failure class

Actual:
- duplicate -> hard failure

---

## Gap G2 — batch is still poisonable by first duplicate
Expected:
- duplicate should not poison remaining rows

Actual:
- remaining row collapsed into aborted transaction path

---

## Gap G3 — safe partial processing is not yet real
Expected:
- non-conflicting row should still proceed

Actual:
- non-conflicting row did not survive

---

## Gap G4 — response model still reflects old semantics
Expected:
- duplicate-skipped visible as separate class
- failed separate

Actual:
- duplicate mixed inside hard-failure semantics
- no duplicate-skipped class present

---

# 5. What this means

This validation shows that:
- H1 chosen policy is documented but not yet behaviorally implemented
- H2 chosen batch model is documented but not yet behaviorally implemented

In other words:
- resolution direction exists
- runtime behavior still remains on old semantics

---

# 6. Strong current conclusion

At this moment, the correct statement is:
- target semantics chosen
- target semantics described
- target semantics validated as NOT YET ACTIVE in runtime behavior

This is an important form of progress, because the implementation gap is now explicit and tested.

---

# 7. Practical next implication

The next honest work item is not more abstract framing.
It is implementation-gap handling around:
1. duplicate should move from failure lane to skip lane
2. duplicate should stop aborting the rest of batch
3. response should gain duplicate-skipped visibility

---

# 8. Canonical current status after runtime gap test

Status remains:
- `GO WITH WRITE CAUTION`

But with stronger precision:
- H1/H2 target semantics are chosen,
- yet still not behaviorally implemented.

---

# 9. Use

Этот note использовать как:
- runtime-gap baseline after first H1/H2 validation attempt;
- bridge from resolution design into concrete implementation-gap handling.
