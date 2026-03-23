# SQL schema notes

## Files
- `001_init.sql` — initial collector schema for Block 2

## Objects
### `collector.raw_trades`
Normalized raw trade storage.

Key points:
- one shared table for all symbols
- dedup key: `(source, symbol, trade_id)`
- canonical fields: `event_time_utc`, `quantity`, `trade_id`, `ingested_at_utc`
- generated fields:
  - `trade_day_utc`
  - `quote_notional`

### `collector.second_bar`
Canonical 1-second aggregate layer.

Key points:
- primary key: `(symbol, ts_second_utc)`
- stores OHLC + volume fields + `vwap`
- supports `ready` and `partial`

### `collector.ingest_watermark`
Stores backfill/live checkpoints and repair cursors.

Key points:
- primary key: `(pipeline, symbol, watermark_type)`
- supports separate cursors per symbol and per pipeline stage

### `collector.second_bar_with_timeframes`
Read-oriented view exposing attached `1m`, `5m`, `60m` OHLC columns from second bars.

## Notes
- In Block 2 the timeframe layer is a view, not final materialized tables yet.
- In Block 3+ we may add materialized views or rollup tables if runtime performance requires it.
- `side` is stored as `buy`/`sell` on raw trades, then mapped into `buy_volume` / `sell_volume` during aggregation.
