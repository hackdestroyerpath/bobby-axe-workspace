# Ben_Kim Write Path Failure Map

## Status
Controlled-runtime operator guidance.

## Purpose
Описать типовые сбои write-path `Ben_Kim` на `POST /analysis/write`:
- как они выглядят;
- что они на самом деле означают;
- как их распознавать;
- что делать операторски.

---

# 1. Scope

Документ покрывает write-side failures для:
- request shaping;
- validator failures;
- duplicate conflicts;
- transaction abort cascades;
- response-vs-durable-state mismatch.

---

# 2. Failure classes

## F1 — Missing mode

### Symptom
Server-side traceback:
- `ValueError: mode must be single or batch`

### Meaning
Top-level request не содержит обязательное поле:
- `mode`

или содержит недопустимое значение.

### How to recognize
- client получает `curl: (52) Empty reply from server`
- server log показывает `mode must be single or batch`

### Operator action
1. проверить top-level payload
2. добавить:
   - `mode = single`
   - или `mode = batch`
3. повторить запрос только после исправления shape

### Prevention
Использовать только live contract examples.

---

## F2 — Wrong batch key

### Symptom
Server-side traceback:
- `ValueError: no analysis_result payloads provided`

### Meaning
Для `mode=batch` был передан неверный массивный ключ.

Ожидается:
- `analysis_results`

Не подходят:
- `results`
- `rows`
- произвольные wrappers

### How to recognize
- client может снова видеть empty reply
- server log указывает на `no analysis_result payloads provided`

### Operator action
1. проверить top-level key
2. заменить его на:
   - `analysis_results`
3. повторить write

### Prevention
Не использовать старые examples с `results` как live source.

---

## F3 — Missing required item fields

### Symptom
Write response or logs указывают на validation error по missing fields.

### Most important fields
- `event_type`
- `analysis_id`
- `symbol`
- `strategy_id`
- `strategy_name`
- `frame`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `source_window`
- `status`
- `result_code`

### Meaning
Item-level payload неполный и не может считаться canonical analysis row.

### Operator action
1. сверить item against live contract
2. восстановить все required fields
3. повторно валидировать before write

### Prevention
Перед write использовать pre-write gate плюс live write contract doc.

---

## F4 — Invalid status/result_code pairing

### Symptom
Write проходит validation poorly or row rejects semantically.

### Meaning
Пара:
- `status`
- `result_code`

не согласована с canonical rule.

### Valid combinations
- `ready + ok`
- `partial + skipped`
- `partial + insufficient_data`
- `rejected + error`

### Operator action
1. сверить semantic pairing
2. исправить before replay

### Prevention
Не менять `status/result_code` вручную без связи с реальным execution outcome.

---

## F5 — Invalid signal enum

### Symptom
Storage reject or validation failure.

### Meaning
В write path используются только:
- `bullish`
- `bearish`
- `neutral`
- `ignore`

Все иные значения live storage не принимает как canonical signal enum.

### Operator action
1. проверить `signal`
2. привести к live enum
3. не использовать prose-like signal labels в storage payload

### Prevention
Разделять:
- runtime analytical wording
- storage enum vocabulary

---

## F6 — Duplicate unique-key conflict

### Symptom
Write response содержит ошибку вида:
- `duplicate key value violates unique constraint "uq_analysis_results_snapshot_symbol_strategy_frame"`

### Meaning
В canonical storage уже есть row для:
- `(snapshot_id, symbol, strategy, frame)`

### Operator action
1. не делать слепой retry без проверки
2. проверить, существует ли row уже в `collector.analysis_results`
3. определить, это:
   - ожидаемый replay
   - legacy contamination
   - conflict between canonical and old test rows
4. только после этого решать:
   - skip
   - upsert/update path
   - manual cleanup

### Prevention
Перед replay учитывать duplicate risk.

---

## F7 — Transaction aborted cascade

### Symptom
После первой ошибки batch выдаёт серию ошибок:
- `current transaction is aborted, commands ignored until end of transaction block`

### Meaning
Первая ошибка уже сломала текущую DB transaction, а остальные rows не были независимо обработаны.

### Operator action
1. считать корневой причиной первую ошибку batch-а
2. не анализировать каскадные ошибки как независимые проблемы
3. исправить root-cause
4. затем повторить clean batch

### Prevention
При чтении batch response всегда искать first real error, а не весь cascade tail.

---

## F8 — Response counters do not match durable state

### Symptom
API отвечает, например:
- `stored_count > 0`

но reconcile по БД не подтверждает новые durable rows.

### Meaning
Response semantics write service пока не полностью trustworthy.

### Operator action
1. не считать counters final truth
2. после важного write делать DB reconcile
3. если mismatch подтвердился — логировать как write-path reliability issue

### Prevention
До hardening считать reconcile обязательным для важных batch writes.

---

## F9 — Legacy/non-canonical rows already present

### Symptom
В `collector.analysis_results` обнаруживаются historical rows с naming drift, например:
- `rsi_macd_cluster`

### Meaning
Canonical storage уже содержит legacy/test contamination.

### Operator action
1. не считать текущее содержимое storage автоматически canonical-clean
2. разделять:
   - active canonical rows
   - legacy/test rows
3. учитывать contamination в duplicate analysis

### Prevention
Нужна отдельная политика cleanup/segregation legacy rows.

---

# 3. Operator sequence when write fails

## Minimal sequence
1. проверить client symptom
2. посмотреть server/root error
3. классифицировать failure по map above
4. исправить root cause
5. повторить write only after shape/semantic fix
6. после важного write сделать reconcile

---

# 4. Root-cause priority rule

Если batch вернул много ошибок, приоритет разбора такой:
1. request shape failure
2. first validator failure
3. first duplicate or write error
4. transaction-aborted cascade
5. counter mismatch after response

---

# 5. Practical operator rules

## Rule O1
Empty reply from server не означает "сервер умер"; часто это validator exception без graceful error body.

## Rule O2
Первую содержательную ошибку считать основной.

## Rule O3
После duplicate conflict не считать оставшийся batch independently processed.

## Rule O4
После partial write не доверять counters без reconcile.

## Rule O5
Canonical storage может быть contaminated historical rows; это надо учитывать до интерпретации duplicate conflicts.

---

# 6. Use

Этот документ использовать как operator baseline для:
- write-path debugging;
- post-write incident handling;
- duplicate/replay troubleshooting;
- controlled execution hardening.
