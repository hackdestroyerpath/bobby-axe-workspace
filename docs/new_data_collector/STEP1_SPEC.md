# New Data Collector — Step 1 Specification

## 1. Purpose
New `Data_collector` is a **foundational tick storage and access layer**.

Jack is responsible only for:
- receiving ticks
- storing ticks in SQL
- maintaining continuity and retention
- exposing tick access by API key
- logging access activity

Jack is **not** responsible for:
- candles
- MACD / RSI
- feature engineering
- pattern logic
- trading formulas
- downstream analytics

Those are downstream concerns and must be built by other agents/consumers on top of the tick layer.

---

## 2. Scope
### In scope
- Binance tick ingestion
- historical tick backfill
- live tick ingestion
- 3-day retention window
- gap detection and refill
- SQL storage
- API-key-protected read access
- per-client access accounting
- 24/7 runtime and self-maintenance

### Out of scope
- OHLC / candles
- second bars
- 1m / 5m / 60m materialization
- feature packets
- indicators
- reports
- dashboards for end users

---

## 3. Supported universe
Initial supported symbols:
- `BTCUSDC`
- `ETHUSDC`

No other symbols are in scope for the first version.

---

## 4. Storage retention
Retention target:
- keep only the most recent **3 days** of tick data in the primary hot store

Operational rule:
- collector must continuously maintain a full rolling 3-day window
- if data drops below the target window, the system must backfill to restore continuity

---

## 5. Canonical tick object
Tick is the only canonical market data unit in this collector.

## Required fields
- `symbol`
- `event_time_utc`
- `price`
- `quantity`
- `side`

## Optional/technical fields
- `source`
- `trade_id`
- `ingested_at_utc`

## Notes
- storage should contain only the minimum data necessary to reconstruct downstream analytics externally
- no candle/derived fields should be written into the core tick store

---

## 6. Input model
### Historical input
- historical ticks are backfilled from Binance
- only tick/trade data is downloaded
- no other market formats are part of the collector scope

### Live input
- live ticks are consumed from Binance stream
- collector must append new ticks continuously

### Self-healing behavior
collector must:
- detect missing windows/gaps
- refill those windows from historical source when possible
- keep live ingestion running while maintaining continuity

---

## 7. Storage model
The new collector is SQL-first.

Core storage responsibilities:
- persist ticks
- support time-range queries
- support symbol filtering
- support API-driven reads for downstream clients
- support retention deletion of old data beyond 3 days

The SQL layer is the canonical source of truth for the new collector.

---

## 8. Access model
Access is provided by API key.

Rules:
- each consumer gets its own key
- keys are revocable
- access must be logged
- accounting must track who queried, when, and how often

Initial expected consumers:
- Boss
- Ben_Kim
- other downstream agents/clients as needed later

---

## 9. Access accounting
Collector must track at minimum:
- client identity
- API key identity / client id
- timestamp of request
- endpoint used
- symbol or symbol set requested
- time window requested
- request count metrics

Future dashboarding is expected, but dashboard UX is not part of Step 1.

---

## 10. Runtime model
Collector must run 24/7.

Operational expectations:
- live ingestion remains active continuously
- historical 3-day window remains intact
- gaps are repaired automatically
- service health can be supervised by Jack
- a dedicated worker/sub-agent for maintenance is recommended later

---

## 11. Definition of done for the new collector foundation
The foundation is considered correctly scoped when all of the following are true:
- only ticks are stored
- only BTCUSDC and ETHUSDC are supported initially
- hot storage keeps 3 rolling days
- historical refill exists
- live ingest exists
- gap refill exists
- reads are API-key protected
- access is logged and attributable per client
- downstream users can consume raw ticks and build their own analytics independently

---

## 12. What downstream clients are expected to do themselves
Downstream clients/agents are expected to:
- pull ticks by API key
- build candles themselves if needed
- compute indicators themselves
- compute strategies/models themselves
- operate their own machines/services for those derived computations

Jack provides only the foundational tick substrate.
