# Ben_Kim Duplicate / Idempotency Note

## Status
Phase 6 hardening note.

## Purpose
Изолировать exact duplicate/idempotency behavior текущего write-path `Ben_Kim`:
- какие replay scenarios существуют;
- что было бы хорошим ожидаемым поведением;
- что происходит сейчас на практике;
- в чём именно gap.

---

# 1. Why this note exists

После двух controlled loops стало ясно:
- duplicate conflict не случайный;
- он повторяемый;
- он влияет не на одну row, а на весь batch path.

Значит duplicate/idempotency semantics нужно фиксировать отдельно.

---

# 2. Canonical logical uniqueness

Текущий storage uniqueness rule:
- `(snapshot_id, symbol, strategy, frame)`

Это означает:
- один logical analysis_result на одну комбинацию:
  - snapshot
  - symbol
  - strategy
  - frame

---

# 3. Replay scenarios

## Scenario D1 — exact replay of the same logical row
Повторно отправляется тот же logical row для того же:
- `snapshot_id`
- `symbol`
- `strategy`
- `frame`

Возможны два варианта:
- identical payload replay
- same logical key but different `analysis_id` / wording / details

---

## Scenario D2 — partial batch replay
Повторно отправляется batch, где:
- часть rows уже существует
- часть rows ещё не существует

Это реальный и важный operational case.

---

## Scenario D3 — retry after uncertain write outcome
Повторный write делается после ситуации, где:
- response был partial/unclear
- durable state неочевиден
- оператор пытается safely retry

Это особенно важно, потому что current write response пока не fully trustworthy.

---

# 4. What good expected behavior would look like

## Expected model E1 — duplicate-safe skip
Если logical row уже существует и replay identical or acceptable:
- row should be skipped cleanly
- batch should continue
- response should report duplicate/unchanged explicitly

## Expected model E2 — safe upsert/update
Если policy допускает update:
- row should update deterministically
- batch should continue
- response should report updated rows clearly

## Expected model E3 — hard reject but batch survives
Если duplicate policy intentionally strict:
- duplicate row may be rejected
- but other non-conflicting rows should still be processed cleanly

---

# 5. What current behavior actually looks like

## Observed behavior A1
При duplicate conflict возникает:
- unique constraint violation

## Observed behavior A2
После first duplicate remaining rows may fall into:
- `current transaction is aborted`

## Observed behavior A3
Response may still report counters like:
- `stored_count = 2`

while durable DB state does not clearly confirm expected new rows.

---

# 6. Current practical interpretation

Current behavior is best interpreted as:
- not duplicate-safe
- not replay-safe enough
- not batch-resilient enough
- not fully operator-trustworthy under uncertain outcomes

---

# 7. Exact gap

## Gap G1 — uniqueness exists, replay semantics do not
Logical uniqueness already exists.
But operator-safe replay semantics are not clearly defined.

## Gap G2 — duplicate handling is too expensive
One duplicate can poison the rest of the batch path.

## Gap G3 — response semantics are weaker than operational need
Operator cannot safely infer durable outcome from response alone.

---

# 8. What needs to become explicit

To close the gap, the system needs one explicit answer:

## Which policy is canonical?
Choose one:
1. duplicate = skip
2. duplicate = update
3. duplicate = reject but batch survives

Without this choice, replay semantics remain operationally unsafe.

---

# 9. Current correct operator rule

Until hardening is completed:
- treat duplicate risk as expected and material;
- do not do blind batch replay;
- inspect existing rows before retry if keyspace may already exist;
- do reconcile after important writes;
- do not assume partial counters imply safe idempotent outcome.

---

# 10. Improvement target

This track is improved only if:
1. canonical duplicate policy is chosen
2. replay semantics are documented
3. actual runtime behavior matches chosen policy
4. operator can retry without guesswork

---

# 11. Current status of this track

Current status:
- duplicate/idempotency behavior is understood as a problem
- but not yet hardened

Therefore this track remains:
- open

---

# 12. Use

Этот note использовать как:
- first hardening sub-track baseline;
- replay semantics reference;
- input into write-path redesign/hardening discussion.
