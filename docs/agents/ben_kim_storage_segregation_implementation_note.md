# Ben_Kim Storage Segregation Implementation Note

## Status
Phase 6 implementation note.

## Purpose
Зафиксировать, что practically должна означать canonical H4 direction:
- `segregation`

для storage contamination handling `Ben_Kim`.

---

# 1. Direction statement

Segregation means:
- historical/test contamination is not allowed to silently share the same interpretation lane as active canonical rows.

The point is not immediate deletion.
The point is clean interpretation.

---

# 2. What segregation should achieve

At minimum, segregation should make it possible to distinguish:
- canonical-active rows
- historical/test rows

without guesswork.

---

# 3. Practical operator meaning

If segregation is working correctly, operator should be able to answer quickly:
1. is this row in the canonical-active lane?
2. is this row historical/test contamination?
3. should this row influence current duplicate interpretation?

---

# 4. What segregation should improve immediately

## S1 — cleaner duplicate reading
Duplicate analysis should reason first against canonical-active rows, not against undifferentiated mixed history.

## S2 — cleaner source-of-truth reading
When operator asks "what is the current canonical state?", the answer should come from canonical-active lane first.

## S3 — less contamination ambiguity
Legacy/test rows should stop silently defining the interpretation baseline.

---

# 5. What segregation should not require immediately

Segregation does not require at the first step:
- full destructive cleanup
- perfect historical migration
- elimination of all old artifacts

It only requires that interpretation lane becomes clear.

---

# 6. Minimum sign that implementation is working

Implementation can be considered directionally correct if:
1. canonical-active lane is explicitly distinguishable
2. contamination lane is explicitly distinguishable
3. duplicate reasoning becomes cleaner
4. operator no longer treats all rows in one mixed bucket by default

---

# 7. Relationship to the rest of hardening

Segregation becomes much more useful after:
- duplicate policy is clarified
- batch semantics are clarified
- response/accounting semantics are clearer

This is why H4 is correctly downstream from H1/H2/H3.

---

# 8. Final short rule

`segregation` means:
- keep history if needed,
- but do not let mixed history define the active canonical reading lane.

---

# 9. Use

Этот note использовать как:
- practical implementation reference for H4 direction;
- bridge from storage-direction decision into real operator-visible storage interpretation changes.
