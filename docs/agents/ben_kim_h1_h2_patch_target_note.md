# Ben_Kim H1/H2 Patch Target Note

## Status
Phase 6 patch-target note.

## Purpose
Зафиксировать, в каком именно слое текущего live write-path должен появиться первый реальный behavioral change для H1/H2.

---

# 1. What was inspected

Live backend behavior was inspected in:
- `workspace-jack/tools/snapshot_lookup_backend.py`

The relevant observed structure is:
1. request validation
2. per-item DB write loop
3. response accounting

---

# 2. Main finding

The first required behavioral change belongs primarily to:
- **transaction/write handling layer**

not to:
- validator layer

and not primarily to:
- response-classification layer

---

# 3. Why validator layer is not the first patch target

Validator currently checks request shape and required fields.

But the observed runtime gap is not:
- missing field semantics
- wrong mode semantics
- schema-shape misunderstanding

The runtime gap appears later:
- during actual DB write behavior under duplicate logical keys.

So validator is not the main first patch target for H1/H2.

---

# 4. Why transaction/write layer is the first patch target

Observed live behavior shows:
- duplicate conflict is raised by DB uniqueness on logical key
- then remaining rows collapse into aborted transaction semantics

The inspected backend also shows that current upsert behavior is keyed on:
- `analysis_id`

while the duplicate conflict that matters operationally is on:
- `(snapshot_id, symbol, strategy, frame)`

This mismatch is critical.

### Meaning
Current code path can happily treat a new `analysis_id` as "new" while DB still rejects it on logical duplicate uniqueness.

That is exactly why the first meaningful patch target is the write/transaction layer.

---

# 5. Practical first patch target

The first practical patch target should be:
- the logic that decides how to handle a row when logical duplicate key already exists

Specifically, the first change should happen before current behavior degenerates into:
- hard failure on duplicate
- transaction-aborted cascade

---

# 6. Response layer is second, not first

Response classification still matters a lot.

But if underlying write behavior does not change, response-only patching would be misleading.

So response layer should follow the first behavioral change, not replace it.

---

# 7. Correct patch-order implication

## First patch target
- transaction/write handling layer

## Second patch target
- response classification/accounting layer

## Third patch target
- any broader cleanup or storage interpretation refinements

This order matches the previously chosen H1 -> H2 -> H3 -> H4 sequence.

---

# 8. First concrete behavioral objective

The first concrete behavioral objective is:
- when logical duplicate key already exists, do **not** let that row flow into ordinary hard-failure poison semantics for the rest of the batch.

In short:
- duplicate must be intercepted at write-handling level before it becomes batch poison.

---

# 9. Final short summary

The first real H1/H2 patch target is:
- **the transaction/write handling layer where logical duplicate key collisions are currently turning into hard failure + batch abort behavior**

That is the place where runtime behavior must change first.

---

# 10. Use

Этот note использовать как:
- immediate patch-target marker;
- clarification of where the first real behavioral fix belongs;
- anti-distraction rule against patching the response layer before the write layer.
