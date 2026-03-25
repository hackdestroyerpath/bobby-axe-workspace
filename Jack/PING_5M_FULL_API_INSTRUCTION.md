# PING_5M_FULL_API_INSTRUCTION

## Purpose
Полная детальная инструкция по API нового regulated `Ping_5m` contour.

Этот документ описывает:
- какие endpoints существуют,
- кто их использует,
- в каком порядке они используются,
- какие обязательные поля требуются,
- какие business rules enforced,
- какие expected responses и failure cases важны.

---

# 1. Core contour

## Final regulated business model
Финальная business-модель `Ping_5m` состоит из 7 сущностей:
- `Pings`
- `Tiks`
- `BK_per_strtg_report`
- `BK_total_report`
- `Maffi_grids_report`
- `DB_report`
- `SQL_Logs`

## Core runtime
Текущий runtime file:
- `ping_5m_api.py`

## Current bind
Рекомендуемый bind target:
- `http://127.0.0.1:8793`

## Auth
Текущая auth-модель использует Jack-controlled key layer.
Запросы идут через header:
- `X-API-Key: <key>`

Hard rules:
- direct SQL writes by Ben / Maffi / Bill forbidden
- raw keys must not be printed in reports / logs / chats
- all final business writes go only through sanctioned API

---

# 2. Core production rules

## 2.1 API-only rule
Все regulated reads/writes должны идти через sanctioned API routes.

## 2.2 Time-window rule
Для Ben и Maffi canonical market-data read path:
- deterministic `from_ts / to_ts`

Old loose recent-read by just `limit=N`:
- not canonical for regulated contour

## 2.3 Bill gate rule
Dollar Bill cannot write final output before full upstream bundle exists:
- `12` rows in `BK_per_strtg_report`
- `3` rows in `BK_total_report`
- `1` row in `Maffi_grids_report`

## 2.4 Regulated truth rule
Final business truth lives in:
- `Pings`
- `Tiks`
- Ben tables
- `Maffi_grids_report`
- `DB_report`
- `SQL_Logs`

---

# 3. `Pings` API

## 3.1 `POST /pings`
### Purpose
Создать / зарегистрировать новый ping.

### Used by
- Jack orchestration
- owner/admin

### Required fields
- `ping_id`
- `time`
- `requested_tf`
- `approved_tickers_json`
- `created_by`

### Optional fields
- `status`
- `completion_state`
- `approved_by`
- `approved_at`
- `notes`

### Important rules
- `requested_tf` currently restricted to `5m`
- `approved_tickers_json` must be array
- `ticker_count` is derived from approved tickers

### Expected success
```json
{
  "status": "stored",
  "data": {
    "ping_id": "PING_5M_...",
    "ticker_count": 2
  }
}
```

---

## 3.2 `GET /pings/<ping_id>`
### Purpose
Read one ping registry row.

### Returns
- `ping_id`
- `time`
- `requested_tf`
- `approved_tickers_json`
- `status`
- `completion_state`
- counts and lifecycle timestamps

---

## 3.3 `GET /pings`
### Purpose
List pings.

### Supported query params
- `status`
- `limit`
- `from_ts`
- `to_ts`

---

## 3.4 `PUT /pings/<ping_id>/status`
### Purpose
Controlled lifecycle status update.

### Important rules
Transition validation is enforced.
Invalid transitions are rejected.

### Example invalid case
- `completed -> approved`
- rejected with `invalid_status_transition`

---

## 3.5 `GET /pings/<ping_id>/gate`
### Purpose
Explicit gate evaluation for the whole ping.

### Returns per ticker
- `ben_strategy_count`
- `ben_total_count`
- `maffi_count`
- `bill_count`
- `gate_status`
- `blockers[]`
- `ready_for_bill`
- `bill_ready`

### Returns per ping
- `ticker_count`
- `ben_ready_ticker_count`
- `maffi_ready_ticker_count`
- `bill_ready_ticker_count`
- `gate_status`
- `completion_gate_status`
- embedded `Pings` snapshot

### Gate rule
Ticker is `ready_for_bill` only if:
- `BK_per_strtg_report.status='stored'` count = `12`
- `BK_total_report.status='stored'` count = `3`
- `Maffi_grids_report.status='stored'` count = `1`

---

## 3.6 `POST /pings/<ping_id>/sync-counters`
### Purpose
Sync `Pings` counters and lifecycle snapshot with actual materialized report rows.

### Writes back
- `ben_ready_ticker_count`
- `maffi_ready_ticker_count`
- `bill_ready_ticker_count`

### May update status conservatively to
- `ben_running`
- `maffi_running`
- `ben_maffi_running`
- `ready_for_bill`
- `completed`

### Important note
This is sanctioned progress reconciliation.

---

## 3.7 `POST /pings/<ping_id>/trigger-bill`
### Purpose
Jack-controlled runtime transition from `ready_for_bill` to `bill_running`.

### Accepts
Optional payload fields:
- `trigger_id`
- `source_request_id`

### Enforced behavior
- checks current gate state
- rejects if ping is not really ready
- idempotent replay if already `bill_running` or `completed`
- updates `Pings.status -> bill_running`
- updates `completion_state -> in_progress`

### Returns trigger payload
- `ping_id`
- `requested_tf`
- `tickers[]`
- `time`
- `gate_status`
- `ben_ready_ticker_count`
- `maffi_ready_ticker_count`
- optional `trigger_id`
- optional `source_request_id`

### Important limitation
Current endpoint authorizes and emits payload, but does not auto-dispatch an external Bill runtime by itself.

---

# 4. `Tiks` API

## 4.1 `GET /tiks/tickers`
### Purpose
List live ticker universe from collector foundation.

### Returns
- `ticker`
- `row_count`
- `last_event_time`

---

## 4.2 `GET /tiks/latest`
### Purpose
Quick debug read of latest ticks.

### Required query params
- `ticker`

### Optional
- `limit`

### Current limit
- hard max `5000`

### Important note
Useful for debug, but not the canonical regulated Ben/Maffi input path.

---

## 4.3 `GET /tiks/range`
### Purpose
Canonical deterministic market-data read path.

### Required query params
- `ticker`
- `from_ts`
- `to_ts`

### Optional
- `limit`
- `order`
- `source`
- `ping_id`

### Current limits
- default `50000`
- hard max `250000`

### Validations
- `from_ts < to_ts`
- valid timestamp format required
- `order` must be `asc` or `desc`

### Important production meaning
Ben and Maffi should use this as canonical market-data input path.

---

# 5. Ben API

Ben has two output layers.

---

## 5.1 `POST /reports/ben/strategy`
### Purpose
Write one row into `BK_per_strtg_report`.

### Required fields
- `id`
- `ping_id`
- `ticker`
- `tf`
- `st_name`
- `st_txt`
- `time`
- `stored_by`

### Optional traceability fields
- `agent_id`
- `machine_id`
- `request_id`
- `source_window_from`
- `source_window_to`
- `llm_model`
- `prompt_version`
- `build_version`
- `storage_request_id`
- `storage_note`
- `status`

### Allowed `tf`
- `5m`
- `60m`
- `1m`

### Allowed `status`
- `stored`
- `partial`
- `rejected`
- `superseded`

---

## 5.2 `POST /reports/ben/strategy/bulk`
### Purpose
Preferred Ben strategy write path.

### Canonical use
Per `ping_id + ticker`, Ben should bulk write:
- `12` rows
- `4 strategies × 3 TF`

### Request shape
```json
{
  "items": [ ... ]
}
```

---

## 5.3 `GET /reports/ben/strategy/<id>`
### Purpose
Read one Ben strategy row.

---

## 5.4 `GET /reports/ben/strategy?ping_id=...`
## 5.5 `GET /reports/ben/strategy?ping_id=...&ticker=...`
## 5.6 `GET /reports/ben/strategy?ping_id=...&ticker=...&tf=...`
### Purpose
Filtered read/list on `BK_per_strtg_report`.

---

## 5.7 `POST /reports/ben/total`
### Purpose
Write one row into `BK_total_report`.

### Required fields
- `id`
- `ping_id`
- `ticker`
- `tf`
- `st_report`
- `time`
- `stored_by`

### Optional traceability fields
- `request_id`
- `source_strategy_count`
- `llm_model`
- `prompt_version`
- `build_version`
- `storage_request_id`
- `storage_note`
- `status`

### Allowed `tf`
- `5m`
- `60m`
- `1m`

### Allowed `status`
- `stored`
- `partial`
- `rejected`
- `superseded`

---

## 5.8 `POST /reports/ben/total/bulk`
### Purpose
Preferred Ben total write path.

### Canonical use
Per `ping_id + ticker`, Ben should bulk write:
- `3` rows
- one per TF: `5m`, `60m`, `1m`

---

## 5.9 `GET /reports/ben/total/<id>`
## 5.10 `GET /reports/ben/total?ping_id=...`
## 5.11 `GET /reports/ben/total?ping_id=...&ticker=...`
## 5.12 `GET /reports/ben/total?ping_id=...&ticker=...&tf=...`
### Purpose
Filtered read/list on `BK_total_report`.

---

## 5.13 Ben success condition
For one `ping_id + ticker`, Ben side is materially ready only if:
- `12` stored rows exist in `BK_per_strtg_report`
- `3` stored rows exist in `BK_total_report`

---

# 6. Maffi API

## 6.1 `POST /reports/maffi/grid`
### Purpose
Write one row into `Maffi_grids_report`.

### Required fields
- `id`
- `ping_id`
- `ticker`
- `tf`
- `grid_par`
- `grid_report`
- `time`
- `stored_by`

### Optional traceability fields
- `request_id`
- `collector_window_from`
- `collector_window_to`
- `llm_model`
- `prompt_version`
- `build_version`
- `storage_request_id`
- `storage_note`
- `direction`
- `upper_price`
- `lower_price`
- `stop_loss`
- `take_profit`
- `grid_count`
- `status`

### Allowed `tf`
- `5m`

### Allowed `status`
- `stored`
- `partial`
- `rejected`
- `superseded`

---

## 6.2 `POST /reports/maffi/grid/bulk`
### Purpose
Preferred multi-ticker Maffi write path.

### Canonical use
Per `ping_id`, Maffi should produce:
- `1` row per approved ticker
- always with `tf = 5m`

---

## 6.3 `GET /reports/maffi/grid/<id>`
## 6.4 `GET /reports/maffi/grid?ping_id=...`
## 6.5 `GET /reports/maffi/grid?ping_id=...&ticker=...`
### Purpose
Filtered read/list on `Maffi_grids_report`.

---

## 6.6 Maffi success condition
For one `ping_id + ticker`, Maffi side is materially ready only if:
- exactly `1` stored row exists in `Maffi_grids_report`
- with `tf = 5m`

---

# 7. Bill API

## 7.1 `POST /reports/bill/final`
### Purpose
Write one final row into `DB_report`.

### Required fields
- `id`
- `ping_id`
- `ticker`
- `tf`
- `grid_pnl`
- `bill_report`
- `time`
- `stored_by`

### Optional traceability fields
- `request_id`
- `source_bundle_count`
- `llm_model`
- `prompt_version`
- `build_version`
- `storage_request_id`
- `storage_note`
- `direction`
- `confidence_score`
- `bill_reasoning_json`
- `status`

### Allowed `tf`
- `5m`

### Allowed `status`
- `stored`
- `partial`
- `rejected`
- `superseded`

### Gate-aware protection
Before write, runtime checks:
- `12` stored rows in `BK_per_strtg_report`
- `3` stored rows in `BK_total_report`
- `1` stored row in `Maffi_grids_report`

If bundle incomplete:
- write rejected with `bill_gate_not_ready`

---

## 7.2 `POST /reports/bill/final/bulk`
### Purpose
Bulk Bill final write path.

### Canonical use
Per `ping_id`, Bill may bulk write:
- `1` row per ticker

Same gate-aware protection applies per ticker.

---

## 7.3 `GET /reports/bill/final/<id>`
## 7.4 `GET /reports/bill/final?ping_id=...`
## 7.5 `GET /reports/bill/final?ping_id=...&ticker=...`
### Purpose
Filtered read/list on `DB_report`.

---

## 7.6 Bill success condition
For one `ping_id + ticker`, Bill side is materially ready only if:
- exactly `1` stored row exists in `DB_report`
- with `tf = 5m`

At ping level, Bill stage is materially complete only if:
- every approved ticker has exactly one final Bill row

---

# 8. `SQL_Logs` API

## 8.1 `GET /sql-logs`
### Purpose
Read raw regulated audit rows.

### Supported query params
- `table_name`
- `action_type`
- `key_id`
- `client_id`
- `ping_id`
- `ticker`
- `from_ts`
- `to_ts`
- `limit`

### Current meaning
Owner/ops sanctioned readback of regulated activity.

---

## 8.2 `GET /sql-logs/rollup`
### Purpose
Read summary rollups over regulated audit rows.

### Supported query params
- `group_by=table`
- `group_by=key`
- `group_by=client`
- `group_by=ping`
- `group_by=ticker`
- `from_ts`
- `to_ts`

### Returns
- `total_requests`
- `last_seen`
- `get_count`
- `post_count`
- `put_count`
- `delete_count`

---

# 9. Canonical execution order by actor

## 9.1 Jack orchestration
1. create ping via `POST /pings`
2. optional read/list via `GET /pings`
3. let Ben + Maffi produce upstream rows
4. check gate via `GET /pings/<ping_id>/gate`
5. sync counters via `POST /pings/<ping_id>/sync-counters`
6. trigger Bill via `POST /pings/<ping_id>/trigger-bill`
7. sync counters again after Bill writes
8. inspect `SQL_Logs`

---

## 9.2 Ben
1. `GET /pings/<ping_id>`
2. `GET /tiks/range`
3. `POST /reports/ben/strategy/bulk`
4. `POST /reports/ben/total/bulk`
5. optional readback

---

## 9.3 Maffi
1. `GET /pings/<ping_id>`
2. `GET /tiks/range`
3. `POST /reports/maffi/grid` or `/bulk`
4. optional readback

---

## 9.4 Dollar Bill
1. `GET /pings/<ping_id>`
2. `GET /pings/<ping_id>/gate`
3. `POST /pings/<ping_id>/trigger-bill`
4. read Ben + Maffi bundle
5. `POST /reports/bill/final` or `/bulk`
6. optional `POST /pings/<ping_id>/sync-counters`

---

# 10. Key failure behaviors already enforced

## Invalid TF writes
- rejected

## Invalid time-range params
- rejected

## Early Bill write
- rejected with gate blockers

## Trigger before readiness
- rejected

## Invalid lifecycle transition
- rejected

## Duplicate trigger replay
- idempotent replay

---

# 11. Current known caveat
Known hardening caveat:
- not every validation reject is yet fully logged into `SQL_Logs`

Meaning:
- business behavior is governed correctly
- but reject-path audit completeness still needs improvement

This is a hardening item, not a reason to abandon the regulated contour.

---

# 12. Final operating rule
For regulated `Ping_5m`, the production business path is now:
- `Pings`
- `Tiks`
- `BK_per_strtg_report`
- `BK_total_report`
- `Maffi_grids_report`
- `DB_report`
- `SQL_Logs`

Everything else may survive only as support/foundation layer, not as final business truth.
