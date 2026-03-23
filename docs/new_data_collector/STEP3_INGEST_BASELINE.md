# New Data Collector — Step 3 Ingest Baseline

## Goal
Create the first runnable baseline for `Data_collector v2`.

This step includes only:
- historical tick backfill
- live tick ingest
- tick-only storage into `collector_v2.tick_trade`
- retention cleanup mode

It does **not** include:
- API access layer
- key issuance/revocation
- request accounting runtime
- dashboards

---

## Files added
- `new_collector/config.py`
- `new_collector/models.py`
- `new_collector/db.py`
- `new_collector/backfill.py`
- `new_collector/live.py`
- `new_collector/main.py`
- `new_collector/requirements.txt`
- `new_collector/.env.example`

---

## Modes
### `backfill`
Downloads recent historical ticks for configured symbols and writes them into `collector_v2.tick_trade`.

### `live`
Consumes realtime aggregate trade stream from Binance and writes ticks continuously.

### `retention`
Deletes ticks older than the configured hot window.

---

## Current limitations of baseline
This is a baseline only.

Known limitations:
- historical backfill currently requests one recent window with Binance `aggTrades`
- no iterative paging loop yet
- no explicit gap scanner yet
- no service supervisor yet
- no API layer yet
- no access log runtime yet

---

## Why this step is still valid
Even with limitations, Step 3 establishes the first working foundation for:
- loading ticks
- storing ticks
- keeping live ingest open
- enforcing 3-day retention

This is enough to proceed to the next layers cleanly.
