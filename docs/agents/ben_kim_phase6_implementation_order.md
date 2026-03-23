# Ben_Kim Phase 6 Implementation Order Note

## Status
Implementation-order note.

## Purpose
Зафиксировать, в каком порядке реально имеет смысл закрывать hardening tracks H1/H2/H3/H4, чтобы улучшения давали максимальный practical effect и не шли в неверной последовательности.

---

# 1. Tracks

- H1 — duplicate/idempotency
- H2 — batch transaction behavior
- H3 — response accounting trust
- H4 — storage contamination policy

---

# 2. Recommended implementation order

## First
- H1 — duplicate/idempotency

## Second
- H2 — batch transaction behavior

## Third
- H3 — response accounting trust

## Fourth
- H4 — storage contamination policy

---

# 3. Why this order is correct

## H1 before H2
Пока неясно, как system должен трактовать duplicate/replay, сложно честно стабилизировать batch behavior.

Иными словами:
- H2 partly depends on semantics clarified in H1.

## H2 before H3
Пока batch semantics не определены cleanly, response accounting нельзя сделать действительно trustworthy.

Иными словами:
- H3 partly depends on H2.

## H3 before H4
Пока response/durable semantics слабы, storage cleanup/segregation policy будет опираться на shaky operational trust.

Иными словами:
- H4 удобнее и безопаснее доводить после того, как write/reporting semantics стали яснее.

---

# 4. Practical effect by order

## H1 gives first practical effect
- safer replay reasoning
- less duplicate ambiguity
- clearer retry/skip/update logic

## H2 gives second practical effect
- clearer batch failure interpretation
- less cascade ambiguity
- stronger operator understanding of partials

## H3 gives third practical effect
- more trustworthy reporting
- less mandatory reconcile dependence
- stronger operational confidence

## H4 gives fourth practical effect
- cleaner storage interpretation
- cleaner duplicate analysis
- clearer source-of-truth reading

---

# 5. What should not be done out of order

## Do not try to claim H3 solved before H2 is materially improved
Because response trust depends on transaction semantics clarity.

## Do not try to declare storage clean enough before H1/H2/H3 semantics stabilize
Because contamination interpretation depends on understanding what current writes really mean.

## Do not jump to broad storage cleanup before duplicate semantics are decided
Because cleanup without duplicate policy can create new ambiguity instead of reducing it.

---

# 6. Minimum sequential logic

Correct sequence:
1. decide duplicate/replay semantics
2. stabilize batch behavior interpretation
3. stabilize response accounting trust
4. then finalize storage contamination policy

---

# 7. Current status relative to this order

Current state:
- all four tracks are defined
- none of them is fully closed
- implementation should begin with H1

---

# 8. Final short rule

If only one hardening track can be pushed first, push:
- H1 — duplicate/idempotency

Because it gives the strongest upstream leverage on the remaining three tracks.

---

# 9. Use

Этот note использовать как:
- implementation ordering reference;
- anti-chaos rule for Phase 6;
- sequencing guide before attempting actual fixes or stronger status claims.
