# Ben_Kim Safe Partial Processing Response Model

## Status
Phase 6 response/accounting note.

## Purpose
Зафиксировать, как response должен выглядеть при canonical batch model:
- `safe partial processing`

чтобы оператор мог читать mixed batch outcome в один проход.

---

# 1. Response design goal

Response должен позволять оператору сразу понять:
- что реально stored
- что duplicate-skipped
- что failed
- где main failure cause, если он был

---

# 2. Minimum outcome classes

Under safe partial processing response должен различать минимум:

## A — stored
Rows, которые durably stored.

## B — duplicate_skipped
Rows, которые не были записаны повторно, потому что duplicate policy = skip.

## C — failed
Rows, которые действительно failed for material reason.

---

# 3. Minimum counters

Минимально response должен содержать:
- `stored_count`
- `duplicate_skipped_count`
- `failed_count`

Optionally also:
- `accepted_count`
- `updated_count` (только если explicit update path exists)

---

# 4. Main-failure visibility

If any true failure exists, operator should be able to see:
- main/root failure class
- not just a long tail of noisy dependent messages

This means response should be root-cause oriented, not cascade-noise oriented.

---

# 5. One-pass readability rule

A good response should allow operator to read the batch in one pass like this:
- X stored
- Y duplicate-skipped
- Z failed
- main failure cause = <cause>

If this cannot be done, response model is still too muddy.

---

# 6. What should not happen

## Not acceptable
- duplicate mixed with failure class
- failed rows hidden inside generic partial wording
- cascade noise dominating response meaning
- counters that still require guesswork to interpret

---

# 7. Relationship to H1

Because H1 recommends:
- `duplicate = skip`

H2/H3 response model must preserve duplicate as its own non-failure class.

This is essential for safe partial processing to remain readable.

---

# 8. Practical success sign

Response/accounting model can be considered directionally correct if:
1. operator can read mixed batch outcome in one pass
2. duplicate rows are clearly non-failure rows
3. hard failures remain visible as incidents
4. response is more interpretable before reconcile, even if reconcile still exists as safety layer

---

# 9. Final short rule

For `safe partial processing`, a good response should make this sentence true:
- mixed outcome is normal,
- unreadable mixed outcome is not.

---

# 10. Use

Этот note использовать как:
- response/accounting target for canonical batch model;
- bridge from H2 into H3;
- reference for future operator-facing write response redesign.
