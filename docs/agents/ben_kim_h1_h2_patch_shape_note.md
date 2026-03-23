# Ben_Kim H1/H2 Patch Shape Note

## Status
Phase 6 patch-shape note.

## Purpose
Коротко зафиксировать, какого рода изменение нужно в live write loop, чтобы появился первый реальный behavioral fix для H1/H2.

---

# 1. Patch-shape goal

The first fix does not need to solve all write/storage issues at once.

It only needs to change one critical behavior:
- logical duplicate should stop becoming hard-failure poison for the rest of batch.

---

# 2. Minimum patch shape

A minimal viable patch shape should contain three elements.

## Element A — pre-check by logical key
Before ordinary insert/upsert path, system should determine whether a row already exists by logical duplicate key:
- `(snapshot_id, symbol, strategy, frame)`

This is the critical pre-check.

## Element B — duplicate classification path
If logical duplicate already exists, row should go into:
- duplicate-skipped path

not into:
- ordinary hard-failure path

## Element C — continue remaining batch
Once duplicate is classified as non-failure skip, remaining non-conflicting rows should continue through normal processing.

---

# 3. Why this patch shape is the right first move

Because it directly addresses the currently validated runtime gap:
- duplicate hard-failure
- transaction-aborted cascade
- unreadable mixed outcome

Without needing full rewrite of the whole endpoint.

---

# 4. What this patch shape should NOT try to do yet

The first patch does not need to fully solve:
- perfect response redesign
- full storage cleanup
- intentional update workflow
- all future edge cases at once

It only needs to stop duplicate from poisoning batch semantics.

---

# 5. Expected behavioral effect

If this patch shape works, then:
1. known duplicate row is classified as duplicate-skipped
2. duplicate no longer creates transaction-aborted tail by default
3. non-conflicting rows still process
4. response becomes easier to redesign around real outcome classes

---

# 6. Practical patch-order inside the behavior fix

Correct order inside the fix should be:
1. detect logical duplicate early
2. classify it as duplicate-skipped
3. keep processing remaining batch rows
4. only then refine response/accounting wording and counters

---

# 7. Minimum honest success condition

The patch should be considered directionally successful if a mixed validation batch shows:
- duplicate row no longer treated as hard failure
- non-conflicting row no longer collapses into aborted tail

That is enough for the first real behavioral win.

---

# 8. Final short rule

The first H1/H2 patch should not be a cosmetic response patch.

It should be:
- logical-key pre-check
- duplicate-skipped classification
- batch continuation for non-conflicting rows

---

# 9. Use

Этот note использовать как:
- first behavior-fix shape reference;
- immediate design-to-patch bridge for H1/H2;
- anti-overreach guide for the first practical runtime fix.
