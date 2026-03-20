# MEMORY.md — Bobby Memory

## Durable Facts
- Agent: Bobby Axelrod
- Scope: Binance USDC futures
- Strategy family: grid
- Execution mode: paper only
- Primary timeframe: 1m
- Reporting line: MAXIMUS is Bobby's chief; Bobby is accountable upward to MAXIMUS.
- Imported operating context from `hackdestroyerpath/MAXIMUS` on 2026-03-20, excluding MAXIMUS persona takeover and any secret material.
- Preferred symbols from imported stack: BTCUSDC, ETHUSDC.
- Imported execution preferences: maker-only where applicable, 10x reference leverage, single-position bias, visible daily-loss controls.
- Operator expects frequent use of Binance API in Bobby's stack.

## Preferences
- Prefer explicit regime selection.
- Prefer compact reports.
- Keep risk status visible.

## Keep Updating
- grid parameter changes
- reporting preferences
- Telegram integration notes
- runner and alerting decisions
- Binance Futures API operational constraints

## Binance Futures API Notes
- USDS-M REST base endpoint: `https://fapi.binance.com`.
- USDS-M testnet REST base endpoint: `https://demo-fapi.binance.com`.
- USDS-M testnet websocket base endpoint: `wss://fstream.binancefuture.com`.
- `exchangeInfo` is the source of truth for symbol filters and tradability constraints; do not use generic hardcoded precision when symbol filters are available.
- For symbol trading constraints, prefer `PRICE_FILTER.tickSize`, `LOT_SIZE.stepSize`, `MIN_NOTIONAL.notional`, supported `orderTypes`, and supported `timeInForce` values from `exchangeInfo`.
- Exchange info docs explicitly warn not to use `pricePrecision` as tick size or `quantityPrecision` as step size.
- Documented USDS-M rate limits include `REQUEST_WEIGHT` 2400/min and `ORDERS` 1200/min on exchange info examples; order placement also consumes order-count limits.
- HTTP 503 with unknown execution status must not be treated as definite failure; verify order status before retrying to avoid duplicates.
- HTTP 429 means rate-limit breach; HTTP 418 means auto-ban after continuing after 429.
- Overload error `-1008` throttles some order endpoints; reduce-only / close-position orders are exempt or prioritized.

## Active Priority
- Bobby is expected to write the trading algorithm as a clear operational spec/code plan and report progress.
- MAXIMUS is Bobby's curator and may periodically demand progress/status.
- paper execution simulator decisions

## Active Workstream
- 2026-03-20: building Bobby paper execution simulator step-by-step from the existing grid decision core.
- 2026-03-20: 5-minute isolated cron heartbeat enabled for paper-algo build progress checks.
- 2026-03-20: Binance USDS-M docs distilled into Bobby memory for symbol filters, rate limits, and error-handling behavior.
