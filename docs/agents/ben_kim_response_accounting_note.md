# Ben_Kim Response Accounting Trust Note

## Status
Phase 6 hardening note.

## Purpose
Зафиксировать текущее состояние trustworthiness response counters на write-path `Ben_Kim`:
- какие counters сейчас нельзя считать fully trustworthy;
- каким должен быть trustworthy response;
- какой reconcile policy нужен до исправления.

---

# 1. Why this note exists

После двух controlled loops было замечено одно и то же:
- API response сообщает partial success counters;
- durable DB state не подтверждает ожидаемый практический outcome.

Значит response accounting нужно рассматривать как отдельный hardening track.

---

# 2. Current observed issue

## Observed pattern R1
Response может сообщать, например:
- `accepted_count = 18`
- `stored_count = 2`
- `rejected_count = 16`

## Observed pattern R2
Post-write reconcile по БД не подтверждает новых durable rows, соответствующих этим counters.

### Practical meaning
Response body currently cannot be treated as self-sufficient proof of durable write success.

---

# 3. Which counters are not yet fully trustworthy

На текущем этапе нельзя считать fully trustworthy без reconcile:
- `stored_count`
- `updated_count`
- any implied durable-success interpretation derived from partial status alone

## Why
Потому что counters уже хотя бы дважды расходились с post-write DB interpretation.

---

# 4. What a trustworthy response should mean

Trustworthy response means:
- operator can read counters and understand real durable outcome;
- partial success semantics are not misleading;
- reported `stored/updated/rejected` values correspond to actual DB state.

---

# 5. Minimum properties of a trustworthy response

## Property A
`stored_count` means rows durably stored and query-confirmable.

## Property B
`updated_count` means rows durably updated and query-confirmable.

## Property C
`rejected_count` means rows not durably accepted.

## Property D
Counters do not imply success for rows rolled back or lost in transaction ambiguity.

---

# 6. Current gap

## Gap R1
Response counters are more optimistic than operator can safely trust.

## Gap R2
The response does not yet provide enough certainty about durable outcome.

## Gap R3
Operational reporting still requires DB reconcile for important writes.

---

# 7. Current correct operator rule

Until hardening is complete:
1. do not treat `stored_count` as final truth
2. do not treat partial success as durable success by default
3. after important writes, run reconcile
4. if response and DB diverge, trust durable DB state over response counters

---

# 8. Reconcile policy until fix

## Mandatory reconcile cases
Reconcile is required when:
- batch write is important
- response is `partial`
- duplicate conflict appears
- transaction-aborted cascade appears
- operator needs trustworthy reporting

## Optional reconcile cases
Reconcile may be lighter when:
- non-critical diagnostic write
- isolated known-safe test path

But for current production-like guarded loops, reconcile should be considered standard.

---

# 9. Improvement target for this track

This track is improved only if:
1. response counters align with durable DB state
2. operator can trust `stored/updated/rejected` meanings
3. reconcile becomes exception rather than default requirement

---

# 10. Current status of this track

Current status:
- response accounting weakness is reproduced
- operator workaround exists
- but response trust is not yet hardened

Therefore this track remains:
- open

---

# 11. Use

Этот note использовать как:
- response-trust baseline;
- reconcile policy reference;
- input into write-path accounting hardening.
