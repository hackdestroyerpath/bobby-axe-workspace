# Ben_Kim Batch Model Decision Memo

## Status
Phase 6 resolution memo.

## Purpose
Коротко сравнить возможные canonical batch models для write-path `Ben_Kim` и зафиксировать рекомендованный выбор.

---

# 1. Decision to make

Для batch write semantics нужно выбрать canonical model:
1. `atomic rollback`
2. `per-row isolation`
3. `safe partial processing`

---

# 2. Option A — atomic rollback

## Meaning
Если один row fails materially:
- весь batch считается failed
- durable outcome должен быть all-or-nothing

## Strengths
- максимально чистая transaction story
- легко объяснить если response и DB fully aligned

## Weaknesses
- плохо подходит для guarded loops with expected duplicates
- слишком дорогой operationally under replay-heavy uncertainty
- требует очень strong response accounting trust

## Operational fit
Сейчас fit слабый, потому что current system ещё не имеет такого уровня clarity/trust.

---

# 3. Option B — per-row isolation

## Meaning
Каждый row пишется максимально независимо:
- failure одного row не влияет на остальных

## Strengths
- best isolation semantics
- easiest to reason about mixed outcomes
- strong fit for duplicate=skip world

## Weaknesses
- может быть сложнее реализовать cleanly
- требует хорошего response design for per-row outcomes

## Operational fit
Очень сильный fit conceptually, because it matches guarded batch processing and replay-safe behavior.

---

# 4. Option C — safe partial processing

## Meaning
Batch обрабатывается как mixed outcome pipeline:
- successful rows proceed
- duplicates/skips reported cleanly
- failures reported cleanly
- batch remains interpretable as one object

## Strengths
- pragmatic fit for current guarded reality
- easier to align with duplicate=skip
- supports meaningful partial reporting

## Weaknesses
- требует хорошей semantics discipline
- without clear response model can become muddy

## Operational fit
Очень хороший fit для текущего stage, because Ben_Kim already operates in guarded mixed-outcome conditions.

---

# 5. Recommended choice

## Recommendation
Choose:
- **`safe partial processing`**

---

# 6. Why this is the best current choice

## Reason 1
Current operating reality already includes mixed outcomes.

## Reason 2
This model aligns naturally with:
- `duplicate = skip`
- guarded replay scenarios
- operator-readable partial outcomes

## Reason 3
It is more realistic and less brittle than atomic rollback, while requiring less perfect isolation assumptions than idealized per-row isolation.

## Reason 4
It gives the clearest near-term path to improve H2 and H3 together.

---

# 7. Required companion rule

If `safe partial processing` is chosen, then response must clearly separate:
- stored
- duplicate_skipped
- failed

Otherwise the model degenerates back into ambiguity.

---

# 8. Final decision statement

For current Ben_Kim hardening stage, the recommended canonical batch model is:
- **`safe partial processing`**

because it gives:
- best fit for guarded mixed outcomes
- best compatibility with `duplicate = skip`
- best path toward readable operator semantics without waiting for perfect atomic or fully isolated behavior

---

# 9. Use

Этот memo использовать как:
- resolution starting point for H2;
- decision reference before implementation work;
- justification for why `safe partial processing` is the best current batch model.
