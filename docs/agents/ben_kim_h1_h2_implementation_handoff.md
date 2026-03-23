# Ben_Kim H1/H2 Implementation Handoff

## Status
Phase 6 implementation handoff note.

## Purpose
Свести в одном месте всё, что уже выбрано и подтверждено по H1/H2, чтобы следующий шаг мог быть уже не planning-heavy, а implementation-oriented.

---

# 1. Chosen H1 policy

## Canonical choice
- `duplicate = skip`

## Meaning
Если row уже существует по logical key:
- не переписывать её неявно;
- не считать ordinary hard failure;
- трактовать как safe duplicate replay case.

---

# 2. Chosen H2 model

## Canonical choice
- `safe partial processing`

## Meaning
Batch должен быть mixed-outcome object, где:
- новые rows могут stored
- duplicate rows могут duplicate-skipped
- true failures остаются true failures
- mixed outcome остаётся readable for operator

---

# 3. Runtime gap already validated

Runtime validation уже показал, что current live behavior пока не соответствует выбранной H1/H2 модели.

## Observed current behavior
- duplicate still treated as hard failure
- duplicate still poisons the rest of batch
- non-conflicting row still collapses into aborted transaction tail
- no `duplicate_skipped` class is visible in response

This gap is already tested, not hypothetical.

---

# 4. Patch target already identified

The first real patch target belongs primarily to:
- **transaction/write handling layer**

not mainly to:
- validator layer
- cosmetic response wording layer

Reason:
- current mismatch happens when logical duplicate key collides in DB behavior,
  while current path still effectively reasons too much through `analysis_id` path.

---

# 5. Minimal patch shape already identified

The first minimal patch should contain:

## A — logical-key pre-check
Check duplicate by:
- `(snapshot_id, symbol, strategy, frame)`

## B — duplicate-skipped classification
If logical duplicate exists:
- route row into non-failure duplicate-skipped path

## C — batch continuation
Keep processing remaining non-conflicting rows.

---

# 6. First honest success criterion

The first real behavioral win is not:
- better wording
- more notes
- softer interpretation of same old behavior

The first real behavioral win is:
- a mixed validation batch with known duplicate no longer collapses the rest of batch into old aborted semantics

This is the decisive success criterion.

---

# 7. Immediate implementation meaning

If implementation starts now, the next honest engineering move is:
- make logical duplicate stop acting like poison

In practical terms:
1. detect duplicate by logical key
2. classify it as duplicate-skipped
3. continue non-conflicting rows
4. only then refine response/accounting around the new behavior

---

# 8. Final short summary

H1/H2 are now ready for actual behavior-fix work because the following are already explicit:
- policy
- model
- runtime gap
- patch target
- patch shape
- first success criterion

This is enough for a real implementation handoff.

---

# 9. Use

Этот note использовать как:
- compact implementation handoff for the first H1/H2 behavior fix;
- bridge from resolution design into actual patch work.
