# Ben_Kim Duplicate = Skip Response Model

## Status
Phase 6 operator-facing response note.

## Purpose
Зафиксировать, как response должен выглядеть для оператора, если canonical duplicate policy принята как:
- `duplicate = skip`

---

# 1. Response design goal

Response должен позволять оператору без guesswork понять:
- какие rows реально stored
- какие rows skipped as duplicate
- какие rows truly failed

---

# 2. Minimum operator-facing categories

Response должен различать минимум три outcome class:

## A — stored
Новые rows, которые durably stored.

## B — duplicate_skipped
Rows, которые не были записаны повторно, потому что logical key already exists.

## C — failed
Rows, которые действительно не прошли из-за hard failure.

---

# 3. Why this separation matters

Without this split operator cannot safely distinguish:
- safe replay outcome
from
- real write failure

This is exactly the ambiguity that current behavior creates.

---

# 4. Minimum response counters

If duplicate=skip is implemented, operator-facing response should expose at least:
- `stored_count`
- `duplicate_skipped_count`
- `failed_count`

Optionally also:
- `accepted_count`
- `updated_count` (if separate explicit update path exists in future)

---

# 5. Row-level reporting expectation

For mixed batch outcomes, operator should be able to see per-row classification such as:
- stored
- duplicate_skipped
- failed

This can be done via:
- per-row results array
or
- error/result detail sections

But the distinction must be explicit.

---

# 6. Mixed batch example meaning

If a batch has:
- 10 new rows
- 6 duplicates
- 2 hard failures

response should make this read naturally as:
- `stored_count = 10`
- `duplicate_skipped_count = 6`
- `failed_count = 2`

not as a muddy partial state where duplicates are mixed with hard failure semantics.

---

# 7. What should not happen

## Not acceptable
- duplicates reported as hard failures
- duplicates silently counted as success
- duplicates causing transaction-aborted cascade semantics for later rows
- partial response that hides whether duplicate rows were safe or dangerous

---

# 8. Recommended top-level status semantics

Top-level status may still be:
- `ok`
- `partial`
- `error`

But operator meaning should be:

## `ok`
All rows either stored cleanly or intentionally non-problematic under policy.

## `partial`
Some rows stored, some duplicate-skipped, and/or some failed.

## `error`
Batch outcome not trustworthy enough to interpret as normal mixed result.

---

# 9. Practical operator read rule

If duplicate=skip policy is working correctly, operator should be able to read a mixed batch as:
- duplicates are not incidents
- hard failures are incidents
- stored rows are durable outcome

That is the real target.

---

# 10. Minimum sign that response model is working

Response model can be considered directionally correct if:
1. duplicate rows are visible as their own class
2. operator no longer confuses replay-safe duplicate with failure
3. mixed batch outcome is legible in one pass
4. reconcile is used for trust verification, not for basic category decoding

---

# 11. Use

Этот note использовать как:
- operator-facing response target for `duplicate = skip`;
- bridge between policy semantics and response/accounting redesign;
- reference for future H2/H3 hardening alignment.
