# Ben_Kim Batch Transaction Resolution Criteria

## Status
Phase 6 resolution criteria.

## Purpose
Зафиксировать, что именно должно измениться, чтобы batch transaction behavior track можно было считать реально закрытым.

---

# 1. Scope

Этот документ относится к track:
- batch transaction behavior

Он фиксирует:
- какие признаки означают, что batch semantics стали operationally acceptable;
- какие критерии должны быть выполнены;
- чего недостаточно для честного close.

---

# 2. Resolution target

Track считается закрытым только если batch write semantics перестают быть ambiguous для оператора.

Это означает:
- оператор понимает, что означают root cause и остаток batch;
- durable outcome читается без guesswork;
- response semantics соответствуют transaction reality.

---

# 3. Mandatory closure questions

Track нельзя считать закрытым, пока нет ответа на три вопроса.

## Q1 — What is canonical batch model?
Нужно выбрать и зафиксировать одну модель:
1. atomic rollback
2. per-row isolation
3. safe partial processing

Без этого batch semantics остаются расплывчатыми.

## Q2 — How is root cause separated from cascade?
Нужно явно понимать:
- что считается first meaningful failure
- как отражаются dependent tail errors
- как оператор должен читать response

## Q3 — What does partial actually mean?
Нужно ответить:
- partial response = какие rows точно durable
- какие rows точно not durable
- что требует reconcile

---

# 4. Minimum runtime criteria for closure

Track можно считать закрытым только если выполнены все criteria below.

## C1 — batch semantics are explicit
Модель batch behavior выбрана и documented.

## C2 — root cause is clearly surfaced
Первая содержательная ошибка легко отличима от cascade tail.

## C3 — operator can interpret outcome safely
Оператор понимает:
- что реально произошло
- что можно повторять
- что уже нельзя трактовать как отдельную ошибку

## C4 — response matches transaction reality
Response semantics больше не противоречат transaction model.

## C5 — batch outcome no longer feels structurally ambiguous
Даже при partial failure путь interpretation остаётся ясным.

---

# 5. What is not enough to call the track closed

Следующего недостаточно:

## Not enough N1
Просто знать, что first error важнее tail errors.

## Not enough N2
Просто уменьшить число cascade lines в response.

## Not enough N3
Просто описать root cause manually after each incident.

## Not enough N4
Просто сказать, что batch partial by design, without precise semantics.

---

# 6. Strong closure indicators

Track закрыт сильно, если одновременно true:
1. batch model explicitly chosen
2. root-cause vs cascade interpretation deterministic
3. operator can read partial response without guessing transaction reality
4. batch outcome remains operationally legible after failure

---

# 7. Practical closure test

Track можно честно закрыть, если оператор может без сомнений ответить:

1. Что означает `partial` для whole batch?
2. Какие rows точно durable после first failure?
3. Какие ошибки — root cause, а какие просто cascade tail?
4. Нужно ли трактовать batch как atomic, row-wise, или partial-safe?

Если ответы всё ещё неочевидны — track не закрыт.

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
- closure criteria for batch transaction track;
- basis for future implementation evaluation;
- anti-ambiguity checklist before claiming H2 resolved.
