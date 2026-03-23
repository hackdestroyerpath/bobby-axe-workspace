# Ben_Kim Live Write Contract

## Status
Controlled-runtime materialized contract.

## Purpose
Зафиксировать точный live contract для:
- `POST /analysis/write`

Контракт основан не на предположениях, а на live validator behavior и runtime-debugging.

---

# 1. Endpoint

## Method
- `POST`

## Path
- `/analysis/write`

## Auth
- `X-API-Key: <Ben_Kim API key>`

---

# 2. Top-level mode

Поле `mode` обязательно.

## Allowed values
- `single`
- `batch`

## If missing
Server-side validator падает с ошибкой:
- `ValueError: mode must be single or batch`

---

# 3. Request shape by mode

## Single mode
Для `mode = single` top-level payload должен содержать:
- `analysis_result`

## Batch mode
Для `mode = batch` top-level payload должен содержать:
- `analysis_results`

## Important
Batch validator ожидает именно:
- `analysis_results`

а не:
- `results`
- `rows`
- произвольное имя массива

Если ключ неверный, live validator возвращает:
- `ValueError: no analysis_result payloads provided`

---

# 4. Top-level fields

## Single mode top-level
Минимально допустимо:
- `mode`
- `analysis_result`

Рекомендуется также передавать:
- `snapshot_id`
- `correlation_id`
- `producer`

## Batch mode top-level
Минимально допустимо:
- `mode`
- `analysis_results`

Рекомендуется также передавать:
- `snapshot_id`
- `correlation_id`
- `producer`

## Inheritance rule
Live validator умеет наследовать из top-level в item-level:
- `snapshot_id`
- `correlation_id`
- `producer`

Но безопаснее считать, что item должен быть самодостаточным, особенно для replay/debug use.

---

# 5. Required item fields

Каждый `analysis_result` item должен содержать:
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

Это подтверждено live validator-ом.

---

# 6. Item field semantics

## event_type
Должен быть:
- `analysis_result`

## analysis_id
Уникальный row-level identifier.

## symbol
Например:
- `BTCUSDC`

## strategy_id
Должен быть каноническим registry id, например:
- `price_levels_fibo_horizontal_volume`
- `vertical_volume`
- `rsi_macd`
- `trade_speed`
- `added_later_placeholder`
- `elliott_waves`

## strategy_name
Должен соответствовать registry display name, например:
- `Price Levels + Fibo + Horizontal Volume`
- `Vertical Volume`
- `RSI + MACD`
- `Trade Speed`
- `Added Later Placeholder`
- `Elliott Waves`

## frame
Допустимые значения:
- `1m`
- `5m`
- `60m`

## signal
Live storage check допускает:
- `bullish`
- `bearish`
- `neutral`
- `ignore`

## confidence
Число в диапазоне:
- `0..1`

## source_window
Объект вида:
- `from`
- `to`

## status
Допустимые значения:
- `ready`
- `partial`
- `rejected`

## result_code
Допустимые значения:
- `ok`
- `skipped`
- `insufficient_data`
- `error`

---

# 7. Required status/result_code pairing

## Valid pairings
- `ready` + `ok`
- `partial` + `skipped`
- `partial` + `insufficient_data`
- `rejected` + `error`

## Practical rule
Ben_Kim usable analysis row:
- `status = ready`
- `result_code = ok`

Placeholder/skipped row:
- `status = partial`
- `result_code = skipped`
- `signal = ignore`

---

# 8. Live uniqueness behavior

Storage enforces unique key on:
- `(snapshot_id, symbol, strategy, frame)`

## Consequence
Duplicate same logical row may trigger:
- unique constraint violation
- transaction aborted cascade for the rest of batch

## Practical rule
Current write path is not yet safe to treat as clean replay-idempotent batch API.

---

# 9. Trusted vs not-yet-trusted behavior

## Trusted
- required `mode`
- required `analysis_results` for batch
- required item fields
- signal enum
- status/result_code enum
- unique key exists

## Not yet fully trusted
- response counters as perfect reflection of durable DB outcome
- duplicate handling semantics under mixed batches

---

# 10. Canonical single example

```json
{
  "mode": "single",
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_362a59f7",
  "producer": "Ben_Kim",
  "analysis_result": {
    "event_type": "analysis_result",
    "analysis_id": "an_BTCUSDC_added_later_placeholder_20260322T025500_1m",
    "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
    "correlation_id": "snapshot_run_20260321T235503Z_362a59f7",
    "symbol": "BTCUSDC",
    "strategy_id": "added_later_placeholder",
    "strategy_name": "Added Later Placeholder",
    "frame": "1m",
    "signal": "ignore",
    "conclusion": "Placeholder strategy is not implemented for live analytical use; no canonical analytical conclusion is produced.",
    "confidence": 0.1,
    "observed_at": "2026-03-22T02:55:00+03:00",
    "source_window": {
      "from": "2026-03-22T02:54:00+03:00",
      "to": "2026-03-22T02:55:00+03:00"
    },
    "status": "partial",
    "result_code": "skipped"
  }
}
```

---

# 11. Canonical batch example

```json
{
  "mode": "batch",
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_362a59f7",
  "producer": "Ben_Kim",
  "analysis_results": [
    {
      "event_type": "analysis_result",
      "analysis_id": "an_BTCUSDC_price_levels_fibo_horizontal_volume_20260322T025500_1m",
      "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
      "correlation_id": "snapshot_run_20260321T235503Z_362a59f7",
      "symbol": "BTCUSDC",
      "strategy_id": "price_levels_fibo_horizontal_volume",
      "strategy_name": "Price Levels + Fibo + Horizontal Volume",
      "frame": "1m",
      "signal": "bearish",
      "conclusion": "Price is below the nearest fib level and below the local value-area center; structure remains weak and does not show a confirmed reversal yet.",
      "confidence": 0.64,
      "observed_at": "2026-03-22T02:55:00+03:00",
      "source_window": {
        "from": "2026-03-22T02:54:00+03:00",
        "to": "2026-03-22T02:55:00+03:00"
      },
      "status": "ready",
      "result_code": "ok"
    },
    {
      "event_type": "analysis_result",
      "analysis_id": "an_BTCUSDC_added_later_placeholder_20260322T025500_1m",
      "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
      "correlation_id": "snapshot_run_20260321T235503Z_362a59f7",
      "symbol": "BTCUSDC",
      "strategy_id": "added_later_placeholder",
      "strategy_name": "Added Later Placeholder",
      "frame": "1m",
      "signal": "ignore",
      "conclusion": "Placeholder strategy is not implemented for live analytical use; no canonical analytical conclusion is produced.",
      "confidence": 0.1,
      "observed_at": "2026-03-22T02:55:00+03:00",
      "source_window": {
        "from": "2026-03-22T02:54:00+03:00",
        "to": "2026-03-22T02:55:00+03:00"
      },
      "status": "partial",
      "result_code": "skipped"
    }
  ]
}
```

---

# 12. Operational rule until write hardening is complete

Пока write-path hardening не завершён:
- использовать только этот live contract shape;
- после важных batch writes делать reconcile;
- не считать response counters достаточным доказательством durable success.
