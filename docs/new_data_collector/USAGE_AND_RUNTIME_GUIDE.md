# Data Collector v2 — Usage and Runtime Guide

## Purpose
This guide explains how to:
- initialize the new collector
- apply schema
- run backfill/live/continuity/API
- issue and revoke API keys
- connect downstream clients and agents

This is the canonical operator guide for the new `Data_collector v2`.

---

# 1. Scope recap
Collector v2 is **tick-only**.

It provides:
- historical tick backfill
- live tick ingest
- rolling 3-day hot window
- continuity / gap refill baseline
- protected tick read API
- per-request access accounting

It does **not** provide:
- candles
- indicators
- feature engineering
- strategies
- downstream analytics

---

# 2. Directory layout
Main folder:
- `new_collector/`

Important files:
- `sql/001_init.sql`
- `.env.example`
- `requirements.txt`
- `main.py`
- `api.py`
- `clients.py`

Docs:
- `docs/new_data_collector/STEP1_SPEC.md`
- `STEP2_DB_SCHEMA.md`
- `STEP3_INGEST_BASELINE.md`
- `STEP4_CONTINUITY.md`
- `STEP5_API_LAYER.md`
- `STEP6_API_KEYS.md`
- `STEP7_ACCESS_ACCOUNTING.md`

---

# 3. Environment setup
## 3.1 Create DB
Create PostgreSQL database:
```bash
createdb data_collector_v2
```

## 3.2 Prepare environment
```bash
cd /home/openclaw/.openclaw/workspace-jack/new_collector
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 3.3 Example `.env`
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/data_collector_v2
BINANCE_REST_BASE_URL=https://fapi.binance.com
BINANCE_WS_BASE_URL=wss://fstream.binance.com/stream
SYMBOLS=BTCUSDC,ETHUSDC
RETENTION_DAYS=3
```

---

# 4. Apply schema
```bash
cd /home/openclaw/.openclaw/workspace-jack/new_collector
source .venv/bin/activate
psql "$DATABASE_URL" -f sql/001_init.sql
```

---

# 5. Runtime modes
All runtime modes are launched from `main.py`.

## 5.1 Historical backfill
```bash
python main.py backfill
```

## 5.2 Live ingest
```bash
python main.py live
```

## 5.3 Retention cleanup
```bash
python main.py retention
```

## 5.4 Continuity / gap maintenance
```bash
python main.py continuity
```

---

# 6. API runtime
Run tick API:
```bash
python api.py --host 127.0.0.1 --port 8791
```

Health check:
```bash
curl http://127.0.0.1:8791/health
```

---

# 7. API key management
## 7.1 Issue or rotate a key
```bash
python clients.py issue --client-id boss --nickname Boss
```

Example for an agent:
```bash
python clients.py issue --client-id ben_kim --nickname Ben_Kim
```

This prints the raw API key once.
Store it securely.

## 7.2 Revoke a key
```bash
python clients.py revoke --client-id ben_kim
```

---

# 8. How clients connect
## 8.1 Required header
All tick reads require:
```text
X-API-Key: <your_key>
```

## 8.2 Tick query example
```bash
curl -H "X-API-Key: <YOUR_KEY>" \
  "http://127.0.0.1:8791/ticks?symbol=BTCUSDC&limit=100"
```

## 8.3 With time range
```bash
curl -H "X-API-Key: <YOUR_KEY>" \
  "http://127.0.0.1:8791/ticks?symbol=ETHUSDC&from=2026-03-23T00:00:00+00:00&to=2026-03-23T03:00:00+00:00&limit=500"
```

---

# 9. What downstream agents should do
Downstream agents/machines should:
1. request an API key from Jack
2. store it securely
3. query ticks by symbol/time window
4. build their own candles / indicators / models themselves

They should **not** expect the collector to provide derived analytics.

---

# 10. What Jack manages
Jack is responsible for:
- schema
- backfill
- live ingest
- continuity
- retention
- API key issuance
- API key revocation
- access accounting
- service health

If a client needs a key:
- request it from Jack

If a key must be disabled:
- Jack revokes it

---

# 11. Minimal operator sequence
## First bring-up
```bash
cd /home/openclaw/.openclaw/workspace-jack/new_collector
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
psql "$DATABASE_URL" -f sql/001_init.sql
python main.py backfill
python api.py --host 127.0.0.1 --port 8791
```

## Then separately keep live ingest running
```bash
python main.py live
```

## Then periodically run continuity + retention
```bash
python main.py continuity
python main.py retention
```

---

# 12. Recommended next operational layer
Not part of this guide yet, but recommended next:
- systemd units for:
  - `live`
  - `api`
  - `continuity`
  - `retention`
- operator `/status` check
- usage stats endpoint

---

# 13. For colleagues and agents
Short message to colleagues:

> Use `Data_collector v2` only as a tick substrate. Request an API key from Jack, query ticks by symbol/time window, and build your own analytics on your own machine. Do not expect candles or indicators from the collector core.
