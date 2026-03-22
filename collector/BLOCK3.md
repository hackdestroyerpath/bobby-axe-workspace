# Block 3 status

Implemented:
- env-backed config loader
- normalized trade model for Binance aggTrades
- PostgreSQL helper with idempotent raw insert
- watermark read/write helpers
- historical backfill entrypoint for Binance Futures `BTCUSDC`
- paginated fetch by time cursor for `/fapi/v1/aggTrades`

Current runtime assumption:
- historical bootstrap uses Binance Futures aggTrades as the initial trade source
- uniqueness/dedup is enforced on `(source, symbol, trade_id)`

Next block:
- WebSocket live ingest
- reconnect logic
- continuous raw insert path
