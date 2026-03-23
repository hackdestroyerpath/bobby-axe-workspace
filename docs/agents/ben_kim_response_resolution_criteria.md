# Ben_Kim Response Accounting Resolution Criteria

## Status
Phase 6 resolution criteria.

## Purpose
Зафиксировать, что именно должно измениться, чтобы response accounting track можно было считать реально закрытым.

---

# 1. Scope

Этот документ относится к track:
- response accounting trustworthiness

Он фиксирует:
- какие признаки означают, что response counters стали trustworthy enough;
- какие критерии должны быть выполнены;
- чего недостаточно для честного close.

---

# 2. Resolution target

Track считается закрытым только если оператор может использовать response body как trustworthy summary of durable write outcome without routine guesswork.

Это означает:
- counters соответствуют фактической durable reality;
- partial semantics не вводят в заблуждение;
- reconcile становится exception, а не default operational crutch.

---

# 3. Mandatory closure questions

Track нельзя считать закрытым, пока нет ответа на три вопроса.

## Q1 — What exactly does each counter mean?
Нужно явно определить meaning of:
- `stored_count`
- `updated_count`
- `rejected_count`
- `accepted_count`

## Q2 — Are counters durable-state aligned?
Нужно понимать:
- counters отражают committed DB state
или
- промежуточное processing intent

Без этого operator trust невозможен.

## Q3 — When is reconcile still required?
Нужно явно определить:
- когда response достаточно
- когда reconcile всё ещё обязателен
- когда mismatch itself is an incident

---

# 4. Minimum runtime criteria for closure

Track можно считать закрытым только если выполнены все criteria below.

## C1 — counters are semantically explicit
Каждый counter meaning documented.

## C2 — counters match durable DB reality
Операторский reconcile больше не опровергает normal response semantics.

## C3 — partial responses are interpretable safely
Оператор понимает, что partial actually means in durable terms.

## C4 — response can support operational reporting
Response пригоден для status reporting without immediate manual correction.

## C5 — reconcile is no longer default for routine important writes
Reconcile остаётся safeguard, но не mandatory crutch for normal trust.

---

# 5. What is not enough to call the track closed

Следующего недостаточно:

## Not enough N1
Просто улучшить wording в response.

## Not enough N2
Просто уменьшить число mismatch cases without clear semantics.

## Not enough N3
Просто всегда делать reconcile вручную и считать это нормой.

## Not enough N4
Просто считать counters approximate by design.

---

# 6. Strong closure indicators

Track закрыт сильно, если одновременно true:
1. counter meanings explicit
2. counters reliably align with durable state
3. operator can trust partial summary enough for reporting
4. reconcile becomes exception instead of standard compensating step

---

# 7. Practical closure test

Track можно честно закрыть, если оператор может без сомнений ответить:

1. Что конкретно означает `stored_count`?
2. Что конкретно означает `updated_count`?
3. Можно ли по response делать trustworthy short report без immediate DB correction?
4. Нужен ли reconcile всегда, или только в exceptional cases?

Если ответы всё ещё расплывчаты — track не закрыт.

---

# 8. Current status against these criteria

Current status:
- criteria are now defined
- but they are not yet satisfied

Therefore this track remains:
- open

---

# 9. Use

Этот документ использовать как:
- closure criteria for response accounting track;
- basis for future implementation evaluation;
- anti-false-confidence checklist before claiming H3 resolved.
