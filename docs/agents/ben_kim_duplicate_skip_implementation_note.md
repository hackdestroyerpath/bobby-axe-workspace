# Ben_Kim Duplicate = Skip Implementation Note

## Status
Phase 6 implementation note.

## Purpose
Зафиксировать, что practically должна означать canonical policy:
- `duplicate = skip`

для write-path `Ben_Kim`.

---

# 1. Policy statement

If a row with the same logical key already exists:
- `(snapshot_id, symbol, strategy, frame)`

then the incoming duplicate should:
- not overwrite the existing row implicitly;
- not poison the batch;
- be reported as duplicate/skipped rather than hard failure.

---

# 2. What counts as duplicate

A duplicate is defined by logical key equality:
- same `snapshot_id`
- same `symbol`
- same `strategy`
- same `frame`

This is the canonical duplicate boundary.

---

# 3. Required runtime behavior

## D1 — no implicit overwrite
Existing row remains the authoritative stored row.

## D2 — no batch poisoning
Duplicate row must not push the rest of batch into aborted-transaction semantics.

## D3 — explicit reporting
Duplicate should be visible in response as:
- duplicate/skipped/unchanged-like outcome

not as opaque hard failure.

## D4 — non-conflicting rows continue
Rows without conflict should continue through normal write path.

---

# 4. What response should communicate

If duplicate = skip is implemented correctly, operator-facing response should make clear:
- which rows were stored
- which rows were skipped as duplicates
- which rows truly failed

Meaning:
- duplicate is not mixed with hard failure
- duplicate is not hidden as success
- duplicate is not allowed to create misleading partial ambiguity

---

# 5. What batch behavior should look like

For a mixed batch:
- some rows new
- some rows duplicate

correct behavior should be:
1. new rows stored
2. duplicate rows skipped
3. hard failures reported separately
4. batch remains interpretable without transaction-aborted cascade noise

---

# 6. What should still remain separate

## Important separation
Normal duplicate replay is not the same thing as intentional correction.

Therefore:
- duplicate replay path = skip
- intentional replacement/update path = separate explicit workflow

This prevents accidental mutation under uncertainty.

---

# 7. What should count as hard failure instead of duplicate

The following should remain hard-failure classes:
- invalid payload shape
- invalid required fields
- invalid enums/semantics
- DB failure unrelated to duplicate policy
- ambiguous or forbidden correction attempts through normal replay path

---

# 8. Practical operator meaning

If operator retries after uncertain outcome and row already exists:
- safe default interpretation should be:
  - existing row kept
  - retry row skipped as duplicate
  - rest of batch continues

This is the key practical value of the policy.

---

# 9. Minimum sign that implementation is working

Implementation can be considered directionally correct if:
1. duplicate no longer triggers transaction-aborted cascade
2. duplicate appears distinctly in response
3. non-conflicting rows still process
4. operator can read batch outcome without guesswork

---

# 10. Use

Этот note использовать как:
- practical implementation reference for `duplicate = skip`;
- operator semantics anchor;
- bridge from policy decision to actual write-path behavior expectations.
