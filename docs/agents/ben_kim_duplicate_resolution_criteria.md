# Ben_Kim Duplicate / Idempotency Resolution Criteria

## Status
Phase 6 resolution criteria.

## Purpose
Зафиксировать, что именно должно измениться, чтобы duplicate/idempotency track можно было считать не просто описанным, а реально закрытым.

---

# 1. Scope

Этот документ относится к track:
- duplicate/idempotency behavior

Он не решает реализацию сам по себе, а фиксирует:
- какие признаки будут означать, что проблема реально закрыта;
- какие критерии должны быть выполнены;
- чего недостаточно для честного close.

---

# 2. Resolution target

Track считается закрытым только если write-path получает operator-safe replay semantics.

Это означает:
- повторная отправка того же logical row больше не создаёт опасного ambiguity;
- оператор понимает, что произойдёт;
- runtime behavior совпадает с задокументированной policy.

---

# 3. Mandatory closure questions

Track нельзя считать закрытым, пока нет чёткого ответа на три вопроса.

## Q1 — What is canonical duplicate policy?
Нужно выбрать одну policy:
1. duplicate = skip
2. duplicate = update
3. duplicate = reject but batch survives

Без этого track остаётся концептуально открытым.

## Q2 — What is canonical replay policy?
Нужно ответить:
- как трактуется exact replay
- как трактуется partial batch replay
- как трактуется retry after uncertain write outcome

## Q3 — How is this surfaced to operator?
Нужно понять:
- как policy отражается в response
- как оператор отличает duplicate from real failure
- когда нужен retry, а когда нет

---

# 4. Minimum runtime criteria for closure

Track можно считать закрытым только если выполнены все criteria below.

## C1 — duplicate behavior is deterministic
Один и тот же duplicate scenario должен давать один и тот же outcome.

## C2 — duplicate behavior is documented
Policy зафиксирована в contract/operator docs.

## C3 — duplicate behavior is operator-safe
Оператор не должен гадать:
- retry
- skip
- inspect
- reconcile first

## C4 — duplicate behavior no longer poisons interpretation of unrelated rows
Даже если duplicate остаётся reject-case, это не должно делать весь batch operationally opaque.

## C5 — replay after uncertain write outcome is manageable
Если write response был partial/uncertain, оператор должен иметь safe rule повторного действия.

---

# 5. What is not enough to call the track closed

Следующего недостаточно:

## Not enough N1
Просто признать, что duplicate exists.

## Not enough N2
Просто задокументировать symptoms without policy choice.

## Not enough N3
Просто привыкнуть делать reconcile вручную всегда.

## Not enough N4
Просто уменьшить количество ошибок без ясной semantics-модели.

---

# 6. Strong closure indicators

Track закрыт сильно, если одновременно true:
1. duplicate policy chosen explicitly
2. replay behavior reproduced against that policy
3. operator response to duplicate is unambiguous
4. duplicate no longer creates major operational ambiguity

---

# 7. Practical closure test

Track можно честно закрыть, если оператор может ответить без сомнений на следующие вопросы:

1. Что произойдёт, если я повторю тот же logical row?
2. Что произойдёт, если я повторю mixed batch, где часть rows уже есть?
3. Нужно ли мне вручную разбирать ambiguous state before retry?
4. Что означает duplicate in response semantics?

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
- closure criteria for duplicate/idempotency track;
- basis for future implementation evaluation;
- anti-self-deception checklist before claiming H1 resolved.
