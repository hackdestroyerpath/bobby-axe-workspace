# Ben_Kim Write Path Hardening

## Status
Controlled-execution hardening baseline.

## Purpose
Зафиксировать реальные проблемы, вскрытые первым controlled single-ticker run `Ben_Kim`, и перевести их в конкретный hardening backlog для write-path.

---

# 1. Scope

Документ покрывает только write-side проблемы, выявленные в реальном runtime:
- contract discoverability;
- payload shape strictness;
- duplicate handling;
- idempotency behavior;
- response trustworthiness;
- legacy contamination in canonical storage.

---

# 2. Controlled-run findings

## Finding W1 — hidden required field `mode`
`POST /analysis/write` требует обязательное поле:
- `mode`

Допустимые значения:
- `single`
- `batch`

### Why this matters
Без этого поле endpoint рвёт соединение с server-side exception:
- `ValueError: mode must be single or batch`

### Hardening requirement
Write contract должен явно и заранее фиксировать `mode` как required field.

---

## Finding W2 — batch key is `analysis_results`
Для batch-write endpoint ожидает:
- `analysis_results`

а не:
- `results`
- `rows`
- произвольный wrapper

### Why this matters
При неверном ключе endpoint возвращает server-side exception:
- `ValueError: no analysis_result payloads provided`

### Hardening requirement
Batch contract должен быть материализован как один точный schema-shape.

---

## Finding W3 — item payload requires `strategy_id` + `strategy_name`
Live validator требует внутри каждой записи:
- `strategy_id`
- `strategy_name`

### Why this matters
Registry identity должна доходить до storage без локальной реконструкции на downstream стороне.

### Hardening requirement
Write examples, schemas и runtime docs должны использовать только registry-based item shape.

---

## Finding W4 — duplicate conflict aborts the whole transaction path
При конфликте уникальности:
- `uq_analysis_results_snapshot_symbol_strategy_frame`

batch переходит в состояние:
- `current transaction is aborted, commands ignored until end of transaction block`

### Why this matters
Один duplicate ломает остаток batch-а.

### Hardening requirement
Write path должен стать:
- idempotent-friendly;
- duplicate-aware;
- transaction-safe на уровне batch processing.

---

## Finding W5 — API response is not yet fully trustworthy without reconcile
Во время controlled run endpoint ответил:
- `stored_count = 2`

Но reconcile по БД не подтвердил новые durable rows, относящиеся к текущему write.

### Why this matters
Write response нельзя считать полностью trustworthy без post-write verification.

### Hardening requirement
Нужно выровнять:
- response counters;
- actual durable DB state;
- transactional outcome semantics.

---

## Finding W6 — canonical storage already contains legacy/non-canonical rows
В `collector.analysis_results` уже присутствовали historical rows, включая:
- `rsi_macd_cluster`

### Why this matters
Canonical layer уже не идеально чистый и может смешивать:
- active canonical strategy set;
- legacy/test artifacts.

### Hardening requirement
Нужно явно отделить:
- canonical active rows;
- legacy/test rows;
- migration leftovers.

---

# 3. Hardening backlog

## Priority A — must fix before repeatable clean loop

### A1. Materialize exact live write contract
Нужно явно зафиксировать:
- `mode`
- `analysis_result` for single mode
- `analysis_results` for batch mode
- required item fields
- status/result_code compatibility
- signal enum compatibility

### A2. Add canonical write request examples
Нужны точные examples для:
- single write
- batch write
- skipped/partial row
- duplicate replay case

### A3. Fix duplicate/idempotency semantics
Нужно определить и реализовать одно из:
- safe upsert;
- per-row duplicate skip with surviving batch;
- deterministic update semantics;
- replay-safe insert contract.

### A4. Fix response accounting
Нужно добиться, чтобы:
- `stored_count`
- `updated_count`
- `rejected_count`

соответствовали фактическому durable outcome.

---

## Priority B — should fix for production trust

### B1. Add post-write verification rule
До исправления response semantics:
- важные writes должны сопровождаться reconcile step.

### B2. Separate canonical rows from test/legacy rows
Нужно определить operational policy для:
- legacy strategy names;
- test analysis_ids;
- non-canonical rows already present in storage.

### B3. Add write-path failure map
Нужно явно описать:
- missing `mode`
- wrong batch key
- duplicate conflict
- partial durable mismatch
- transaction-aborted cascade

---

# 4. Minimum acceptance criteria for hardening

Write path можно считать достаточно hardened только если:
1. contract fully documented
2. examples match live endpoint
3. duplicate replay does not corrupt batch behavior
4. response counters match durable DB state
5. canonical rows are distinguishable from legacy/test contamination

---

# 5. Practical rule for Ben_Kim until hardening is done

Пока hardening не завершён:
- считать `/analysis/write` operationally usable, but not fully trusted;
- после важных batch writes делать reconcile;
- не считать `stored_count` достаточным доказательством durable success;
- учитывать риск legacy contamination в `collector.analysis_results`.

---

# 6. Next use

Этот документ использовать как baseline для:
- post-run hardening work;
- write-path debugging;
- future idempotency and duplicate-handling fixes.
