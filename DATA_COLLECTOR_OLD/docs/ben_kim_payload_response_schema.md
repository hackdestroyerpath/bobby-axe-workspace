# Ben_Kim Payload Response Schema

## Status
Step 2 of 10 for Ben_Kim centralized execution path.

## Purpose
Define the exact response contract for the future read endpoint that returns the full feature payload bundle for a given:
- `snapshot_id`
- `symbol`

The response must provide a snapshot-scoped analysis input bundle for:
- `1m`
- `5m`
- `60m`

Source of truth:
- `collector.snapshot_bundle`
- `collector.feature_packet_tf`

---

## Endpoint goal
Return the best snapshot-scoped frame payload for each required frame, where:
- frame is one of `1m`, `5m`, `60m`
- row is selected with `observed_at <= as_of_utc`
- row may be `ready`, `partial`, or missing

This endpoint is for Ben_Kim read-path consumption only.

---

## Top-level response shape
```json
{
  "snapshot_id": "snapshot_...",
  "bundle_id": "snapshot_...",
  "correlation_id": "snapshot_run_...",
  "symbol": "BTCUSDC",
  "as_of_utc": "2026-03-21T23:55:03.656893Z",
  "payload_status": "ready",
  "result_code": "ok",
  "frames": {
    "1m": { ... },
    "5m": { ... },
    "60m": { ... }
  },
  "notes": []
}
```

---

## Top-level required fields
- `snapshot_id`
- `bundle_id`
- `correlation_id`
- `symbol`
- `as_of_utc`
- `payload_status`
- `result_code`
- `frames`
- `notes`

---

## Top-level status semantics
### `payload_status`
- `ready` — all required frames returned and all are usable (`packet_status=ready`, `packet_result_code=ok`)
- `partial` — at least one frame is partial or missing
- `blocked` — snapshot/symbol resolution failed or request is inconsistent

### `result_code`
- `ok`
- `partial`
- `not_found`
- `error`

---

## `frames` block
`frames` must contain exactly these keys:
- `1m`
- `5m`
- `60m`

Each frame key must resolve to one object.

---

## Frame object shape
```json
{
  "status": "ready",
  "selected_by": "best_observed_at_lte_as_of_utc",
  "payload": {
    "symbol": "BTCUSDC",
    "frame": "1m",
    "observed_at": "2026-03-22T02:55:00+03:00",
    "packet_status": "ready",
    "packet_result_code": "ok",
    "data_quality_status": "ready",
    "data_quality_result_code": "ok",
    "stale": false,
    "insufficient_history_flag": false,
    "open": 0,
    "high": 0,
    "low": 0,
    "close": 0,
    "volume_total": 0,
    "buy_volume": 0,
    "sell_volume": 0,
    "delta_volume": 0,
    "trade_count": 0,
    "lvl_nearest_support_px": 0,
    "lvl_nearest_resistance_px": 0,
    "lvl_distance_to_support_pct": 0,
    "lvl_distance_to_resistance_pct": 0,
    "lvl_support_touch_count": 0,
    "lvl_resistance_touch_count": 0,
    "lvl_is_breakout": false,
    "lvl_is_false_breakout": false,
    "fib_leg_dir": "up",
    "fib_nearest_ratio": 0.618,
    "fib_nearest_level_px": 0,
    "fib_swing_low": 0,
    "fib_swing_high": 0,
    "fib_236": 0,
    "fib_382": 0,
    "fib_500": 0,
    "fib_618": 0,
    "fib_786": 0,
    "fib_distance_to_nearest_pct": 0,
    "hv_poc_px": 0,
    "hv_val_px": 0,
    "hv_vah_px": 0,
    "hv_inside_value_area": false,
    "hv_nearest_hvn_px": 0,
    "hv_nearest_lvn_px": 0,
    "hv_distance_to_poc_pct": 0,
    "vv_vol_z": 0,
    "vv_delta_z": 0,
    "vv_buy_share": 0,
    "vv_pressure_to_move_z": 0,
    "vv_divergence_3": 0,
    "vv_exhaustion_flag": false,
    "rsi_14": 0,
    "rsi_state": "neutral",
    "macd_12_26_9_line": 0,
    "macd_12_26_9_signal": 0,
    "macd_12_26_9_hist": 0,
    "macd_cross_up": false,
    "macd_cross_down": false,
    "macd_hist_slope": 0,
    "trade_speed_now": 0,
    "trade_speed_ma": 0,
    "trade_speed_ratio": 0,
    "volume_per_sec": 0,
    "avg_trade_size": 0,
    "aggressive_buy_rate": 0,
    "aggressive_sell_rate": 0,
    "buy_sell_imbalance": 0,
    "burst_detected": false,
    "flow_accelerating": false,
    "flow_decelerating": false,
    "flow_absorption_flag": false,
    "flow_exhaustion_flag": false,
    "elliott_direction": "up",
    "elliott_pattern_family": "impulse",
    "elliott_candidate_wave": "3",
    "elliott_wave_count": 3,
    "elliott_swing_sequence": "impulse>3>3",
    "elliott_confidence": 0.61,
    "elliott_invalidation_price": 0,
    "elliott_status": "usable",
    "atr_14": 0,
    "atr_pct": 0,
    "realized_volatility": 0,
    "vol_regime": "normal",
    "range_expansion_detected": false,
    "impulse_efficiency_ratio": 0
  }
}
```

---

## Allowed frame-level `status`
- `ready`
- `partial`
- `missing`

### Rules
- `ready` => `payload` present and `packet_status=ready` and `packet_result_code=ok`
- `partial` => `payload` present but packet not fully usable
- `missing` => `payload = null`

---

## Frame-level required fields
- `status`
- `selected_by`
- `payload`

### `selected_by`
Fixed value for v1:
- `best_observed_at_lte_as_of_utc`

---

## Required payload fields per frame
### Service/status
- `symbol`
- `frame`
- `observed_at`
- `packet_status`
- `packet_result_code`
- `data_quality_status`
- `data_quality_result_code`
- `stale`
- `insufficient_history_flag`

### Price / market
- `open`
- `high`
- `low`
- `close`
- `volume_total`
- `buy_volume`
- `sell_volume`
- `delta_volume`
- `trade_count`

### Levels
- `lvl_nearest_support_px`
- `lvl_nearest_resistance_px`
- `lvl_distance_to_support_pct`
- `lvl_distance_to_resistance_pct`
- `lvl_support_touch_count`
- `lvl_resistance_touch_count`
- `lvl_is_breakout`
- `lvl_is_false_breakout`

### Fibonacci
- `fib_leg_dir`
- `fib_nearest_ratio`
- `fib_nearest_level_px`
- `fib_swing_low`
- `fib_swing_high`
- `fib_236`
- `fib_382`
- `fib_500`
- `fib_618`
- `fib_786`
- `fib_distance_to_nearest_pct`

### Horizontal volume
- `hv_poc_px`
- `hv_val_px`
- `hv_vah_px`
- `hv_inside_value_area`
- `hv_nearest_hvn_px`
- `hv_nearest_lvn_px`
- `hv_distance_to_poc_pct`

### Vertical volume
- `vv_vol_z`
- `vv_delta_z`
- `vv_buy_share`
- `vv_pressure_to_move_z`
- `vv_divergence_3`
- `vv_exhaustion_flag`

### RSI / MACD
- `rsi_14`
- `rsi_state`
- `macd_12_26_9_line`
- `macd_12_26_9_signal`
- `macd_12_26_9_hist`
- `macd_cross_up`
- `macd_cross_down`
- `macd_hist_slope`

### Trade speed / flow
- `trade_speed_now`
- `trade_speed_ma`
- `trade_speed_ratio`
- `volume_per_sec`
- `avg_trade_size`
- `aggressive_buy_rate`
- `aggressive_sell_rate`
- `buy_sell_imbalance`
- `burst_detected`
- `flow_accelerating`
- `flow_decelerating`
- `flow_absorption_flag`
- `flow_exhaustion_flag`

### Elliott
- `elliott_direction`
- `elliott_pattern_family`
- `elliott_candidate_wave`
- `elliott_wave_count`
- `elliott_swing_sequence`
- `elliott_confidence`
- `elliott_invalidation_price`
- `elliott_status`

### Volatility
- `atr_14`
- `atr_pct`
- `realized_volatility`
- `vol_regime`
- `range_expansion_detected`
- `impulse_efficiency_ratio`

---

## Missing-frame contract
If no usable or partial row exists for a frame at or before `as_of_utc`:

```json
{
  "status": "missing",
  "selected_by": "best_observed_at_lte_as_of_utc",
  "payload": null
}
```

---

## Notes semantics
`notes[]` may include:
- snapshot resolved via bundle_id/correlation_id
- one or more frames are partial
- one or more frames are missing
- payload is snapshot-scoped by `as_of_utc`

---

## Acceptance for Step 2
This schema is complete if it fixes:
- top-level envelope
- frame-level object structure
- exact field coverage expected by Ben_Kim
- behavior for ready/partial/missing frames
- snapshot-scoped selection semantics

---

## Next planned step
Step 3:
- implement the read endpoint using this schema and current snapshot lookup backend
