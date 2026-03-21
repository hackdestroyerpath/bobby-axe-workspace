# Contract: Ben_Kim Feature Packet

## Status
Accepted for Jack -> Ben_Kim integration.

## Purpose
Контракт описывает прикладной входной объект, который `Jack` передаёт в `Ben_Kim` для анализа.

Этот контракт не заменяет `second_bar` как канонический рыночный слой, а задаёт **runtime-ready feature packet**, чтобы `Ben_Kim` не считал big data заново и не тянул сырой поток в LLM/аналитический слой.

---

## 1. Producer и consumer
- **Producer:** `Jack / Data_collector / feature builder`
- **Consumer:** `Ben_Kim`
- **Downstream usage:** только для analysis-only генерации `analysis_result`

---

## 2. Unit of transfer

Один feature packet = одна комбинация:
- `symbol`
- `frame`
- `observed_at`

То есть для одного тикера в полном запросе обычно передаются 3 packet:
- `1m`
- `5m`
- `60m`

---

## 3. Required top-level fields

- `event_type`: всегда `ben_kim_feature_packet`
- `packet_id`
- `correlation_id`
- `symbol`
- `frame`
- `observed_at`
- `source_window.from`
- `source_window.to`
- `price`
- `levels`
- `fibonacci`
- `horizontal_volume`
- `vertical_volume`
- `rsi_macd`
- `trade_speed`
- `volatility`
- `elliott`
- `data_quality`

---

## 4. Top-level schema description

### 4.1 Identity and timing
- `event_type`: fixed string `ben_kim_feature_packet`
- `packet_id`: уникальный id packet
- `correlation_id`: id текущего run/request
- `symbol`: тикер, например `BTCUSDC`
- `frame`: `1m` | `5m` | `60m`
- `observed_at`: точка анализа в UTC
- `source_window.from`
- `source_window.to`

### 4.2 Feature groups
#### `price`
Должен включать минимум:
- `open`
- `high`
- `low`
- `close`
- `base_volume`
- `trade_count`
- `buy_volume`
- `sell_volume`
- `delta_volume`
- `vwap`

#### `levels`
Должен включать минимум:
- `nearest_support`
- `nearest_resistance`
- `distance_to_support_pct`
- `distance_to_resistance_pct`
- `support_touch_count`
- `resistance_touch_count`
- `is_breakout`
- `is_false_breakout`

#### `fibonacci`
Должен включать минимум:
- `swing_direction`
- `swing_low`
- `swing_high`
- `fib_236`
- `fib_382`
- `fib_500`
- `fib_618`
- `fib_786`
- `nearest_fib_level`
- `distance_to_nearest_fib_pct`

#### `horizontal_volume`
Должен включать минимум:
- `poc_price`
- `vah_price`
- `val_price`
- `inside_value_area`
- `nearest_hvn`
- `nearest_lvn`
- `distance_to_poc_pct`

#### `vertical_volume`
Должен включать минимум:
- `volume_total`
- `volume_zscore`
- `delta_volume`
- `delta_zscore`
- `trade_count_zscore`
- `buy_sell_imbalance`
- `climax_volume`
- `effort_result_ratio`

#### `rsi_macd`
Должен включать минимум:
- `rsi_14`
- `rsi_state`
- `macd_line`
- `macd_signal`
- `macd_hist`
- `macd_cross_up`
- `macd_cross_down`
- `macd_hist_slope`

#### `trade_speed`
Должен включать минимум:
- `trade_speed_now`
- `trade_speed_ma`
- `trade_speed_ratio`
- `volume_per_sec`
- `avg_trade_size`
- `burst_detected`
- `flow_accelerating`
- `flow_decelerating`

#### `volatility`
Должен включать минимум:
- `atr_14`
- `atr_pct`
- `realized_volatility`
- `volatility_regime`
- `range_expansion_detected`

#### `elliott`
Должен включать минимум:
- `pattern_candidate`
- `wave_confidence`
- `wave_invalidation_level`
- `swing_sequence`
- `fib_wave_ratios`

#### `data_quality`
Должен включать минимум:
- `missing_bars`
- `stale`
- `schema_ok`
- `feature_build_version`
- `warnings`

---

## 5. Hard rules

1. `frame` допускается только из набора: `1m`, `5m`, `60m`.
2. Все timestamps должны быть в UTC.
3. Один packet не может содержать несколько таймфреймов одновременно.
4. Если feature group недоступна, это должно быть отражено явно:
   - либо объектом с флагом доступности,
   - либо через `data_quality.warnings`.
5. Отсутствующие признаки нельзя маскировать фиктивными нулями без явного смысла.

---

## 6. Mapping to Ben_Kim strategies

| Strategy | Required feature groups |
| --- | --- |
| `price_levels_fibo_horizontal_volume` | `levels`, `fibonacci`, `horizontal_volume` |
| `vertical_volume` | `vertical_volume` |
| `rsi_macd` | `rsi_macd` |
| `trade_speed` | `trade_speed` |
| `added_later_placeholder` | none |
| `elliott_waves` | `elliott`, `fibonacci`, `levels` |

---

## 7. Minimal acceptance rule

Feature packet считается пригодным для анализа, если:
- top-level fields присутствуют;
- `frame` валиден;
- `source_window` задан;
- `data_quality.schema_ok=true`;
- packet относится к одному тикеру и одному таймфрейму.

Если часть feature groups отсутствует, packet всё ещё может быть принят, но `Ben_Kim` обязан вернуть `partial` по затронутым стратегиям.
