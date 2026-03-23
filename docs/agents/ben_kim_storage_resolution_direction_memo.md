# Ben_Kim Storage Contamination Resolution Direction Memo

## Status
Phase 6 resolution memo.

## Purpose
Коротко сравнить возможные направления решения storage contamination и зафиксировать рекомендованный текущий canonical direction для H4.

---

# 1. Decision to make

Для H4 нужно выбрать preferred resolution direction:
1. `cleanup`
2. `segregation`
3. `tagging / marking`

---

# 2. Option A — cleanup

## Meaning
Legacy/test rows physically removed or archived out of active canonical storage.

## Strengths
- cleanest end-state
- simplest future interpretation once done well

## Weaknesses
- riskiest immediate move
- dangerous before write semantics are fully stabilized
- easy to over-clean or lose useful audit context

## Fit
Weak fit as immediate current direction.

---

# 3. Option B — segregation

## Meaning
Legacy/test rows preserved but clearly separated from active canonical rows.

## Strengths
- safer than destructive cleanup
- strong improvement in interpretation clarity
- preserves audit/history value
- good fit while semantics are still maturing

## Weaknesses
- requires additional separation logic
- not as visually clean as full cleanup

## Fit
Best current direction.

---

# 4. Option C — tagging / marking

## Meaning
Rows stay in place, but metadata/policy marks which are canonical vs contamination.

## Strengths
- low destructive risk
- easier to adopt quickly

## Weaknesses
- weakest cleanliness improvement
- interpretation may still remain muddy if tags are not rigorously enforced
- duplicate analysis may remain less clean than under segregation

## Fit
Useful supportive technique, but weak as sole long-term direction.

---

# 5. Recommended choice

## Recommendation
Choose:
- **`segregation`**

as the canonical current direction for H4.

---

# 6. Why this is the best current choice

## Reason 1
It improves interpretation strongly without requiring risky destructive cleanup too early.

## Reason 2
It preserves historical/test evidence while still protecting the active canonical reading lane.

## Reason 3
It fits the current stage, where write semantics are improving but not yet fully closed.

## Reason 4
It can coexist with later cleanup or tagging refinements.

---

# 7. Companion rule

If `segregation` is chosen, then:
- operator must be able to tell which storage lane is canonical-active;
- duplicate analysis should preferentially reason against the canonical-active lane;
- historical/test rows should not silently define current interpretation.

---

# 8. Final decision statement

For current Ben_Kim hardening stage, the recommended storage contamination resolution direction is:
- **`segregation`**

because it gives:
- strongest current interpretation improvement
- lower risk than immediate cleanup
- better clarity than tagging alone

---

# 9. Use

Этот memo использовать как:
- resolution starting point for H4;
- decision reference before storage-policy implementation work;
- justification for why segregation is the best current direction.
