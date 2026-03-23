# Ben_Kim Storage Contamination Resolution Criteria

## Status
Phase 6 resolution criteria.

## Purpose
Зафиксировать, что именно должно измениться, чтобы storage contamination track можно было считать реально закрытым.

---

# 1. Scope

Этот документ относится к track:
- storage contamination policy

Он фиксирует:
- какие признаки означают, что contamination больше не создаёт operational ambiguity;
- какие критерии должны быть выполнены;
- чего недостаточно для честного close.

---

# 2. Resolution target

Track считается закрытым только если оператор может без guesswork отличать:
- canonical active rows
- legacy/test contamination
- historical artifacts that should not define current interpretation

Это означает:
- storage interpretation becomes cleaner;
- duplicate analysis becomes more trustworthy;
- canonical layer becomes easier to reason about.

---

# 3. Mandatory closure questions

Track нельзя считать закрытым, пока нет ответа на три вопроса.

## Q1 — How are canonical rows distinguished?
Нужно явно понимать:
- по каким признакам row считается current canonical output

## Q2 — What happens to contaminated rows?
Нужно выбрать operational policy:
- cleanup
- segregation
- explicit tagging/marking

## Q3 — How should duplicate conflicts be interpreted in contaminated storage?
Нужно понимать:
- duplicate against canonical row
- duplicate against contamination row
- whether they are treated equally or not

---

# 4. Minimum runtime criteria for closure

Track можно считать закрытым только если выполнены все criteria below.

## C1 — canonical vs contaminated distinction is explicit
Оператор может reliably distinguish row classes.

## C2 — contamination no longer creates major interpretation ambiguity
Historical/test rows no longer force guesswork in duplicate analysis or storage reading.

## C3 — chosen policy is documented
Cleanup / segregation / tagging policy explicitly fixed.

## C4 — duplicate interpretation is cleaner
Operator can tell whether an existing row should really block new canonical write.

## C5 — canonical storage trust improves materially
Storage reads become more trustworthy for operational interpretation.

---

# 5. What is not enough to call the track closed

Следующего недостаточно:

## Not enough N1
Просто признать, что contamination exists.

## Not enough N2
Просто перечислить suspicious rows manually.

## Not enough N3
Просто привыкнуть mentally discounting legacy rows.

## Not enough N4
Просто оставить contamination in place without interpretation policy.

---

# 6. Strong closure indicators

Track закрыт сильно, если одновременно true:
1. canonical row criteria explicit
2. contamination policy explicit
3. duplicate conflicts become easier to interpret
4. operator can read storage without major ambiguity

---

# 7. Practical closure test

Track можно честно закрыть, если оператор может без сомнений ответить:

1. Эта row — canonical или contaminated?
2. Должна ли эта historical row блокировать current canonical write?
3. Что делать с contamination: clean, segregate, or tag?
4. Можно ли читать storage как current source of truth без постоянных оговорок?

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
- closure criteria for storage contamination track;
- basis for future cleanup/segregation evaluation;
- anti-guesswork checklist before claiming H4 resolved.
