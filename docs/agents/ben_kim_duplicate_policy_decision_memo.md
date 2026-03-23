# Ben_Kim Duplicate Policy Decision Memo

## Status
Phase 6 resolution memo.

## Purpose
Коротко сравнить три возможные canonical duplicate policies для write-path `Ben_Kim` и зафиксировать рекомендованный выбор.

---

# 1. Decision to make

Для duplicate по logical key:
- `(snapshot_id, symbol, strategy, frame)`

нужно выбрать canonical policy:
1. `duplicate = skip`
2. `duplicate = update`
3. `duplicate = reject but batch survives`

---

# 2. Option A — duplicate = skip

## Meaning
Если logical row уже существует:
- новый replay не меняет существующую запись
- duplicate считается safe no-op
- batch продолжает обработку остальных rows

## Strengths
- safest operator semantics
- best for replay after uncertain outcome
- easiest mental model for controlled production loops
- lowest accidental overwrite risk

## Weaknesses
- не исправляет уже существующую плохую/legacy row автоматически
- требует отдельной policy для intentional correction/update

## Operational fit
Очень хорошо подходит для текущего состояния, где главная задача:
- убрать ambiguity
- сделать replay безопасным
- не усиливать риск неявной перезаписи

---

# 3. Option B — duplicate = update

## Meaning
Если logical row уже существует:
- новый replay обновляет существующую запись

## Strengths
- удобно для correction flows
- потенциально уменьшает need for manual cleanup

## Weaknesses
- dangerous without very strong semantics
- harder to reason about operator intent
- easier to overwrite a row when the retry was not meant as correction
- bad fit while storage contamination is still unresolved

## Operational fit
Сейчас fit слабый, потому что:
- response trust is weak
- contamination exists
- replay intent is not yet cleanly separated from correction intent

---

# 4. Option C — duplicate = reject but batch survives

## Meaning
Если duplicate найден:
- duplicate row rejected explicitly
- other non-conflicting rows continue

## Strengths
- semantically strict
- avoids silent overwrite
- keeps duplicate visible as a distinct event

## Weaknesses
- still creates operator friction on retry
- less replay-friendly than skip
- may still require more operator effort than needed for normal guarded loops

## Operational fit
Лучше текущего поведения, но всё ещё не лучший default для uncertainty-heavy controlled replay cases.

---

# 5. Recommended choice

## Recommendation
Choose:
- **`duplicate = skip`**

---

# 6. Why this is the best current choice

## Reason 1
Current primary need is safe replay semantics.

## Reason 2
Current system still has:
- response-accounting weakness
- storage contamination
- guarded-loop reality

So the default policy should minimize damage and ambiguity, not maximize mutation power.

## Reason 3
`skip` is the easiest policy to explain operationally:
- if row already exists, do not rewrite it implicitly
- continue batch
- report duplicate clearly

## Reason 4
This choice creates a stable base for later tracks:
- H2 batch behavior
- H3 response accounting
- H4 storage interpretation

---

# 7. Required companion rule

If `duplicate = skip` is chosen, then intentional correction/update must be handled separately.

Meaning:
- normal replay path = skip
- intentional replacement path = separate explicit workflow, not accidental retry side effect

This separation is important.

---

# 8. What this policy should imply operationally

If duplicate is encountered:
1. mark row as duplicate/skipped
2. do not poison remaining batch
3. continue processing non-conflicting rows
4. report duplicates distinctly from hard failures

---

# 9. Final decision statement

For current Ben_Kim hardening stage, the recommended canonical duplicate policy is:
- **duplicate = skip**

because it gives:
- safest replay behavior
- clearest operator semantics
- best fit for guarded loops
- lowest ambiguity while other write/storage tracks are still being hardened

---

# 10. Use

Этот memo использовать как:
- resolution starting point for H1;
- decision reference before implementation work;
- justification for why `skip` is the best current default policy.
