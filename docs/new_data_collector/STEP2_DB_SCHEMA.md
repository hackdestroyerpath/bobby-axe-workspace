# New Data Collector — Step 2 DB Schema

## Goal
Define a clean SQL foundation for `Data_collector v2`.

This step covers only the database layer.
No ingest/runtime/API implementation is included here.

---

## Schema
Namespace:
- `collector_v2`

---

## Tables

### 1. `collector_v2.tick_trade`
Canonical hot tick store.

Fields:
- `source`
- `symbol`
- `trade_id`
- `event_time_utc`
- `price`
- `quantity`
- `side`
- `ingested_at_utc`
- `created_at_utc`

Purpose:
- store raw ticks only
- support time-range reads
- support symbol-scoped reads
- serve as source-of-truth for downstream clients

### Uniqueness
- `UNIQUE (source, symbol, trade_id)`

This gives idempotent ingestion when Binance provides stable trade ids.

---

### 2. `collector_v2.api_client`
Registry of consumers and their API keys.

Fields:
- `client_id`
- `nickname`
- `status`
- `api_key_hash`
- `note`
- `created_at_utc`
- `revoked_at_utc`

Purpose:
- issue access
- revoke access
- identify who is using the collector

---

### 3. `collector_v2.api_access_log`
Per-request accounting log.

Fields:
- `client_id`
- `nickname`
- `request_at_utc`
- `endpoint`
- `symbol`
- `range_from_utc`
- `range_to_utc`
- `request_status`
- `row_count`
- `remote_addr`
- `note`

Purpose:
- count and audit usage
- support future dashboarding
- track who queried what and when

---

### 4. `collector_v2.system_checkpoint`
Small utility table for runtime checkpoints.

Examples:
- last historical backfill cursor
- last live sync state
- retention cleanup watermark

---

## Index strategy
### Tick table
- `(symbol, event_time_utc desc)`
- `(event_time_utc desc)`
- `(ingested_at_utc desc)`

This supports:
- reads by symbol + time window
- freshness checks
- retention cleanup scans

### Access log table
- `(client_id, request_at_utc desc)`
- `(request_at_utc desc)`
- `(symbol, request_at_utc desc)`

This supports:
- usage by client
- recent request inspection
- symbol-specific accounting

---

## What is intentionally NOT in this schema
Not included by design:
- candles
- second bars
- timeframe tables
- features
- indicators
- report tables
- downstream analytics results

This DB layer is tick-only.

---

## Retention note
The schema is built for a rolling 3-day hot window.
Retention implementation itself belongs to runtime/service logic, not to this SQL step.

---

## Definition of done for Step 2
Step 2 is complete when:
- tick storage table exists
- client registry exists
- access log exists
- checkpoint table exists
- indexes support symbol/time lookups and accounting
- no derived analytics structures are present
