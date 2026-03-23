# New Data Collector — Step 5 API Access Layer

## Goal
Expose the first read API for `collector_v2.tick_trade`.

This step adds only a minimal tick read API.
It does **not** yet add:
- API key enforcement
- client registry runtime
- access logging runtime
- key issuance / revocation endpoints

---

## New file
- `new_collector/api.py`

---

## Endpoints
### `GET /health`
Returns simple liveness.

### `GET /ticks`
Query parameters:
- `symbol` (required)
- `from` (optional, ISO-8601)
- `to` (optional, ISO-8601)
- `limit` (optional, default 1000, capped at 10000)

Returns:
- `symbol`
- `count`
- `rows[]`

Rows include:
- `source`
- `symbol`
- `trade_id`
- `event_time_utc`
- `price`
- `quantity`
- `side`
- `ingested_at_utc`

---

## Why this step matters
This is the first external read surface for downstream consumers.
It proves the collector can already act as a tick substrate, even before full key management is wired in.

---

## Known limitations
- no API key validation yet
- no access accounting yet
- no rate limits yet
- no pagination token model yet

Those belong to later steps.
