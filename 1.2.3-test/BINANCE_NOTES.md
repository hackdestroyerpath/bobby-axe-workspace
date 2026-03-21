# Binance USDS-M Notes for Bobby

Source set reviewed on 2026-03-20:
- Exchange Information
- New Order
- General Info

## Core operational facts
- REST base: `https://fapi.binance.com`
- Testnet REST base: `https://demo-fapi.binance.com`
- Testnet WS base: `wss://fstream.binancefuture.com`
- Timestamps are in milliseconds.
- GET params go in query string.
- POST/PUT/DELETE params may be query string or form-encoded body.

## Risk / execution implications
- Use `exchangeInfo` as source of truth for symbol constraints.
- Do not use `pricePrecision` as tick size.
- Do not use `quantityPrecision` as step size.
- Use symbol filters instead:
  - `PRICE_FILTER.tickSize`
  - `LOT_SIZE.stepSize`
  - `MIN_NOTIONAL.notional`
  - `orderTypes`
  - `timeInForce`
- `GTX` exists in docs as a supported time-in-force value on exchange info examples, relevant for maker-first behavior.

## Rate limits / failure handling
- Exchange info example shows:
  - `REQUEST_WEIGHT`: 2400/min
  - `ORDERS`: 1200/min
- New-order doc shows order-count limits apply per 10s and per 1m.
- `429` = rate limit exceeded.
- `418` = auto-ban after continuing after `429`.
- `503` with unknown execution status is not a confirmed failure; verify before retrying.
- `-1008` = overload throttling; reduce-only / close-position flows are exempt or prioritized.

## Bobby implications
- Current Bobby symbol-specific sizing should later be replaced or validated against live `exchangeInfo` filters.
- Future live connector should prefer single orders over batches during stress to reduce unknown-status ambiguity.
- Future live retry logic must distinguish:
  - unknown execution
  - definite failure
  - overload throttling
- Future live deployment should use testnet first, not production first.
