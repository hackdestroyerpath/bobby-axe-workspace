# New Data Collector — Step 4 Continuity / Gap Maintenance

## Goal
Add the first continuity layer to `Data_collector v2`.

This step introduces:
- rolling-window continuity checks
- simple gap detection
- targeted refill attempts

This step does **not** yet introduce:
- service orchestration
- periodic scheduler
- full worker/sub-agent maintenance loop

---

## What was added
### DB helpers
- `get_symbol_window_bounds()`
- `get_recent_gaps()`

### Backfill helpers
- `fetch_agg_trades()`
- `write_rows()`
- `refill_gap_window()`
- `maintain_continuity()`

### Runtime mode
- `main.py continuity`

---

## Current continuity behavior
For each configured symbol:
1. inspect current tick window bounds
2. if storage is empty, reseed recent history
3. if the left edge of the 3-day window is missing, backfill that missing front segment
4. scan for large gaps inside the recent window
5. attempt refill for each detected gap window

---

## Current gap rule
The first baseline rule is simple:
- if consecutive stored ticks are separated by more than 120 seconds,
  treat that as a candidate gap window

This rule is intentionally conservative and can be refined later.

---

## Why this step matters
This is the first implementation of the requirement that collector should not only ingest, but also help maintain a continuous 3-day substrate.

It is not yet full self-healing automation, but it creates the core refill logic needed for that next stage.

---

## Known limitations
- uses simple time-gap heuristic only
- historical refill still depends on Binance aggTrades windowing and may need paging improvements later
- not yet daemonized/scheduled
- not yet supervised by a dedicated worker

---

## Definition of done for Step 4
Step 4 is complete when:
- collector can inspect symbol coverage
- collector can identify large recent gaps
- collector can attempt targeted refill of missing windows
- continuity logic is exposed as a dedicated runtime mode
