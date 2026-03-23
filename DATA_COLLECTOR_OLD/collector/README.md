# Data Collector (Jack)

Initial scaffold for Stage 0 `Data_collector`.

## Scope
- Source: Binance Futures
- Initial symbol: `BTCUSDC`
- Runtime: 24/7 on current VPS
- Modes:
  - historical backfill for last 3 days on first start
  - live ingest via websocket
  - periodic reconcile for recent gaps

## Planned modules
- `config.py` — env loading and runtime config
- `db.py` — PostgreSQL connection helpers
- `models.py` — normalized trade structures
- `backfill.py` — REST historical ingestion
- `live.py` — websocket live ingestion
- `aggregate.py` — second-bar materialization
- `reconcile.py` — short-gap repair
- `main.py` — entrypoint/orchestration

## Status
Scaffold only. SQL and runtime code will be added block by block.
