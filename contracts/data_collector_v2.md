# Contract: Data Collector v2

## Purpose
`Data_collector v2` is a tick-only collector and access layer.

## Producer
- Jack / Data_collector v2

## Consumers
- Boss
- Ben_Kim
- future downstream clients with API keys

## Canonical stored object
Tick / trade record.

## Required canonical fields
- `symbol`
- `event_time_utc`
- `price`
- `quantity`
- `side`

## Technical fields
- `source`
- `trade_id`
- `ingested_at_utc`

## Supported symbols (initial)
- `BTCUSDC`
- `ETHUSDC`

## Retention
- rolling hot window: 3 days

## Input sources
- Binance historical tick/trade source
- Binance live tick/trade stream

## Hard constraints
- no candles
- no second bars
- no 1m/5m/60m aggregation
- no indicators
- no feature layer in collector core

## Access model
- read access only by API key
- each client has its own key
- requests are logged and attributable
- keys can be issued and revoked

## Accounting requirements
At minimum log:
- client id
- request timestamp
- endpoint
- symbol / symbols requested
- range requested
- request count

## Service expectation
- 24/7 operation
- live ingest always on
- rolling 3-day window maintained
- gaps auto-refilled when detected
