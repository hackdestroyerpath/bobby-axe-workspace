# Ben_Kim Safe Partial Processing Implementation Note

## Status
Phase 6 implementation note.

## Purpose
Зафиксировать, что practically должна означать canonical batch model:
- `safe partial processing`

для write-path `Ben_Kim`.

---

# 1. Model statement

Batch should behave as a mixed-outcome object where:
- new valid rows can be stored;
- duplicate rows can be skipped safely;
- true failures are reported distinctly;
- operator can still interpret the whole batch coherently.

---

# 2. Core behavioral expectation

## P1 — mixed outcomes are normal, not exceptional by themselves
A batch may legitimately contain:
- stored rows
- duplicate-skipped rows
- failed rows

This should not automatically collapse into opaque transaction chaos.

## P2 — non-failure classes stay out of hard-failure lane
Duplicates/skips should remain non-failure classes.

## P3 — true failures stay visible
Real failures should remain clearly visible and not be hidden by aggregate wording.

---

# 3. What batch should do practically

For a mixed batch:
1. process storable rows
2. skip duplicate rows safely
3. classify real failures distinctly
4. return a readable mixed-outcome response

---

# 4. What batch should not do

Safe partial processing should NOT mean:
- ambiguous partial with unreadable semantics
- duplicate triggering `transaction aborted` cascade
- failure classes and non-failure classes mixed together
- operator needing guesswork just to understand what happened

---

# 5. Root cause handling

If true failures occur, response should still preserve:
- which rows were stored
- which rows were duplicate-skipped
- which rows truly failed
- what the main failure cause was

This is crucial.

Safe partial processing is not the same as ignoring root cause.

---

# 6. Companion requirement from H1

Because H1 recommends:
- `duplicate = skip`

safe partial processing should treat duplicate as:
- safe non-failure outcome class

This is one of the main reasons the model becomes readable.

---

# 7. Minimum sign that implementation is working

Implementation can be considered directionally correct if:
1. mixed batch no longer degenerates into old cascade pattern
2. duplicate rows are visible as duplicate-skipped
3. non-conflicting rows still complete
4. operator can read batch outcome in one pass

---

# 8. Final short rule

`safe partial processing` means:
- mixed outcomes are allowed,
- ambiguity is not.

That is the essence of the model.

---

# 9. Use

Этот note использовать как:
- practical implementation reference for canonical batch model;
- bridge from H2 decision memo into response/accounting redesign expectations.
