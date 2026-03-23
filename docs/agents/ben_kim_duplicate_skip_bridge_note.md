# Ben_Kim Duplicate = Skip Bridge Note

## Status
Phase 6 bridge note.

## Purpose
Коротко зафиксировать, как решение:
- `duplicate = skip`

должно повлиять на следующие hardening tracks:
- H2 — batch transaction behavior
- H3 — response accounting trust

---

# 1. Why this bridge matters

H1 is not isolated.

Once duplicate policy is chosen, it should immediately simplify:
- how batch failures are interpreted;
- how response counters are designed.

---

# 2. Effect on H2 — batch transaction behavior

## Before
Duplicate could behave like a hard failure and poison the rest of batch interpretation.

## After `duplicate = skip`
Duplicate should no longer be treated as a batch-breaking error class.

### Practical implication
For H2 this means:
- duplicate is not root-cause hard failure
- duplicate should not trigger transaction-aborted cascade semantics
- root-cause analysis should focus on real failures only

### Resulting simplification
Batch semantics become cleaner because one major ambiguity class is removed from the hard-failure lane.

---

# 3. Effect on H3 — response accounting trust

## Before
Duplicate and failure could be mixed inside partial outcome interpretation.

## After `duplicate = skip`
Response model should classify duplicate separately from failure.

### Practical implication
For H3 this means:
- counters should distinguish stored vs duplicate_skipped vs failed
- partial status becomes more interpretable
- operator can trust mixed outcomes more easily

### Resulting simplification
Response accounting becomes cleaner because safe replay outcomes are no longer hidden inside failure noise.

---

# 4. Key conceptual change

After `duplicate = skip`, the system should treat duplicate as:
- replay-safe non-failure class

not as:
- normal hard failure class

This is the core bridge from H1 into H2/H3.

---

# 5. What must remain true

Even after this bridge:
- true DB/write failures remain failures
- invalid payloads remain failures
- semantic violations remain failures
- ambiguous correction attempts remain failures

Only true duplicate replay should move into the non-failure lane.

---

# 6. Final short summary

If `duplicate = skip` is accepted, then:
- H2 should become less cascade-heavy
- H3 should become more legible
- partial response should become easier to trust

That is why H1 is the correct upstream resolution track.

---

# 7. Use

Этот note использовать как:
- bridge from duplicate-policy decision into batch/response redesign;
- short dependency explanation for why H1 should be implemented first.
