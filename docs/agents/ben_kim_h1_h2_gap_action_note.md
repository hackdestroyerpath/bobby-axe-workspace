# Ben_Kim H1/H2 Implementation-Gap Action Note

## Status
Phase 6 implementation-gap action note.

## Purpose
Коротко зафиксировать, какой минимальный runtime change теперь должен быть первым, чтобы H1/H2 начали реально двигаться из design layer в behavior layer.

---

# 1. Current gap state

Сейчас уже известно:
- target policy for H1 = `duplicate = skip`
- target model for H2 = `safe partial processing`

Но runtime validation показал:
- duplicate всё ещё обрабатывается как hard failure
- duplicate всё ещё poison-ит batch
- non-conflicting row не survives

---

# 2. First minimal runtime change

## Recommended first behavioral change
The first minimal runtime change should be:
- **move duplicate from hard-failure lane into explicit non-failure skip lane**

---

# 3. Why this is the first correct move

Because this single change should immediately improve both:
- H1 semantics
- H2 behavior

Without it:
- `duplicate = skip` remains fake at runtime
- `safe partial processing` remains impossible in practice

---

# 4. What this change should mean practically

After the first minimal change:
1. duplicate no longer returns as ordinary write_error
2. duplicate no longer triggers transaction-aborted cascade by default
3. duplicate becomes explicitly classifiable as skipped/non-failure

This is the first honest behavioral win.

---

# 5. What still does NOT need to be solved in the first move

The first move does not require immediate perfection in:
- full response redesign
- full reconcile elimination
- full storage contamination resolution
- broad cleanup of historical rows

It only needs to prove that duplicate is no longer treated as poison.

---

# 6. First real sign of progress

The first real sign that H1/H2 started moving from design to implementation is:
- a mixed batch with a known duplicate no longer collapses the rest of batch into old aborted semantics

That is the decisive signal.

---

# 7. What should not be mistaken for progress

Do not mistake the following for real H1/H2 implementation progress:
- softer wording about duplicate
- better summaries of the same old failure pattern
- more documentation about why duplicate is bad
- response rephrasing without changed runtime outcome

---

# 8. Final short rule

If duplicate still poisons the rest of batch, then H1/H2 are still design-only in practice.

If duplicate becomes an explicit non-failure skip and batch survives, then H1/H2 have started to become real runtime behavior.

---

# 9. Use

Этот note использовать как:
- immediate implementation-gap action marker;
- definition of first real behavioral win for H1/H2;
- anti-self-deception reminder before claiming runtime improvement.
