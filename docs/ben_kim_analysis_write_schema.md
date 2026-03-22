# Ben_Kim Analysis Write Schema

## Status
Step 2 of 10 for Ben_Kim write-side.

## Purpose
Define the exact write request contract for centralized `analysis_result` writeback.

The contract must support:
- single `analysis_result`
- batch `analysis_result[]`
- centralized auth via `X-API-Key`
- JSON request body

This schema is for the future write endpoint only.

---

## Endpoint expectation
Write endpoint will accept JSON over HTTP.

### Auth
- `X-API-Key`

### Content-Type
- `application/json`

---

## Supported request modes
### Mode A — single object
```json
{
  "mode": "single",
  "analysis_result": { ... }
}
```

### Mode B — batch
```json
{
  "mode": "batch",
  "analysis_results": [ ... ]
}
```

---

## Canonical recommendation
Prefer batch mode for Ben_Kim.

Reason:
- natural unit = `1 ticker × 6 strategies × 3 frames = 18 results`
- fewer API calls
- cleaner idempotent write semantics

---

## Top-level request envelope
### Required fields
- `mode`

### Conditional fields
- if `mode = single` -> `analysis_result` required
- if `mode = batch` -> `analysis_results` required

### Optional top-level fields
- `snapshot_id`
- `correlation_id`
- `producer`

Example:
```json
{
  "mode": "batch",
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a",
  "producer": "Ben_Kim",
  "analysis_results": []
}
```

---

## `analysis_result` object
The object must align with `contracts/schemas/analysis_result.schema.json`.

### Required fields
- `event_type`
- `analysis_id`
- `symbol`
- `strategy_id`
- `strategy_name`
- `frame`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `source_window`
- `status`
- `result_code`

### Optional but recommended
- `snapshot_id`
- `correlation_id`
- `producer`
- `details`

---

## Field semantics
### `event_type`
Must be:
- `analysis_result`

### `analysis_id`
Stable identifier for idempotent write behavior.

### `symbol`
Ticker symbol, e.g.:
- `BTCUSDC`

### `strategy_id`
Ben_Kim machine strategy identifier from canonical registry.

### `strategy_name`
Ben_Kim canonical display strategy name from canonical registry.

### `frame`
Allowed values:
- `1m`
- `5m`
- `60m`

### `signal`
Allowed values:
- `bullish`
- `bearish`
- `neutral`
- `ignore`

### `conclusion`
Human-readable analytical conclusion.

### `confidence`
Float in range:
- `0..1`

### `observed_at`
Frame timestamp the result belongs to.

### `source_window`
Object with:
- `from`
- `to`

### `status`
Allowed:
- `ready`
- `partial`
- `rejected`

### `result_code`
Allowed:
- `ok`
- `skipped`
- `insufficient_data`
- `error`

### `details`
Optional structured payload with strategy-specific internals.

---

## Single request example
```json
{
  "mode": "single",
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a",
  "producer": "Ben_Kim",
  "analysis_result": {
    "event_type": "analysis_result",
    "analysis_id": "benkim-btcusdc-rsi-1m-20260322T025500+0300",
    "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
    "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a",
    "producer": "Ben_Kim",
    "symbol": "BTCUSDC",
    "strategy_id": "rsi_macd",
    "strategy_name": "RSI + MACD",
    "frame": "1m",
    "signal": "bullish",
    "conclusion": "Momentum reversal forming with improving histogram slope.",
    "confidence": 0.74,
    "observed_at": "2026-03-22T02:55:00+03:00",
    "source_window": {
      "from": "2026-03-22T02:54:00+03:00",
      "to": "2026-03-22T02:55:00+03:00"
    },
    "status": "ready",
    "result_code": "ok",
    "details": {
      "rsi_14": 10.653430137798,
      "macd_hist_slope": -21.563770180437
    }
  }
}
```

---

## Batch request example
```json
{
  "mode": "batch",
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a",
  "producer": "Ben_Kim",
  "analysis_results": [
    {
      "event_type": "analysis_result",
      "analysis_id": "benkim-btcusdc-rsi-1m-20260322T025500+0300",
      "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
      "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a",
      "producer": "Ben_Kim",
      "symbol": "BTCUSDC",
      "strategy_id": "rsi_macd",
    "strategy_name": "RSI + MACD",
      "frame": "1m",
      "signal": "bullish",
      "conclusion": "Momentum reversal forming.",
      "confidence": 0.74,
      "observed_at": "2026-03-22T02:55:00+03:00",
      "source_window": {
        "from": "2026-03-22T02:54:00+03:00",
        "to": "2026-03-22T02:55:00+03:00"
      },
      "status": "ready",
      "result_code": "ok",
      "details": {}
    }
  ]
}
```

---

## Batch size target
Minimum expected batch support:
- `18` results per ticker per snapshot

This corresponds to:
- `6 strategies × 3 frames`

---

## Acceptance for Step 2
This write schema is complete if it fixes:
- single mode
- batch mode
- required and optional fields
- alignment with `analysis_result.schema.json`
- envelope contract for future API implementation

---

## Next planned step
Step 3:
- define business key and idempotent upsert semantics
