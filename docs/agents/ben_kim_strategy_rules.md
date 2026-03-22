# Ben_Kim Strategy Rules

## Status
Final baseline.

## Purpose
Канонический operational document для strategy-level execution `Ben_Kim`.

Документ фиксирует:
- approved strategy set;
- required core fields;
- usable / partial rules;
- allowed signal range;
- allowed conclusion shape;
- forbidden overclaims.

Этот файл является базовым reference для:
- strategy execution;
- conclusion building;
- pre-write validation;
- downstream interpretation discipline.

---

## Canonical strategy set

Для `Ben_Kim` approved set состоит из 6 стратегий:

1. `price_levels_fibo_horizontal_volume`
2. `vertical_volume`
3. `rsi_macd`
4. `trade_speed`
5. `added_later_placeholder`
6. `elliott_waves`

Strategy identity должна браться только из canonical registry mapping.

---

## 1. price_levels_fibo_horizontal_volume

### Strategy identity
- `strategy_id`: `price_levels_fibo_horizontal_volume`
- `strategy_name`: `Price Levels + Fibo + Horizontal Volume`

### Core dependency
- `lvl_nearest_support_px`
- `lvl_nearest_resistance_px`
- `fib_leg_dir`
- `fib_nearest_ratio`
- `fib_nearest_level_px`
- `hv_poc_px`
- `hv_val_px`
- `hv_vah_px`

### Extended support fields
- `lvl_distance_to_support_pct`
- `lvl_distance_to_resistance_pct`
- `lvl_support_touch_count`
- `lvl_resistance_touch_count`
- `lvl_is_breakout`
- `lvl_is_false_breakout`
- `fib_swing_low`
- `fib_swing_high`
- `fib_236`
- `fib_382`
- `fib_500`
- `fib_618`
- `fib_786`
- `fib_distance_to_nearest_pct`
- `hv_inside_value_area`
- `hv_nearest_hvn_px`
- `hv_nearest_lvn_px`
- `hv_distance_to_poc_pct`

### Usable rule
Использовать, если:
- levels block читается;
- fib block читается;
- horizontal volume block читается;
- цена может быть осмысленно сопоставлена с support/resistance, fib и POC/value area.

### Partial rule
Считать `partial`, если:
- любой из core blocks отсутствует или сломан;
- structural context неполный;
- proximity есть, но meaningful interpretation не собирается.

### Signal range
- `bullish`
- `bearish`
- `neutral`

### Allowed conclusion shape
Говорить только о:
- structural context;
- confluence / lack of confluence;
- price relative to support/resistance/fib/POC/value area;
- structural weakness / support / mixed balance.

### Forbidden overclaims
Запрещено:
- “уровень точно удержится”;
- “пробой подтверждён” без достаточного подтверждения;
- “разворот гарантирован”; 
- торговые параметры (`entry`, `sl`, `tp`, `grid`) как часть strategy conclusion.

---

## 2. vertical_volume

### Strategy identity
- `strategy_id`: `vertical_volume`
- `strategy_name`: `Vertical Volume`

### Core dependency
- `vv_vol_z`
- `vv_delta_z`
- `vv_buy_share`
- `buy_sell_imbalance`

### Extended support fields
- `vv_pressure_to_move_z`
- `vv_divergence_3`
- `vv_exhaustion_flag`
- `volume_total`
- `delta_volume`

### Usable rule
Использовать, если:
- volume context читается;
- delta context читается;
- buyer/seller dominance можно определить;
- можно понять, подтверждает ли объём текущее движение.

### Partial rule
Считать `partial`, если:
- volume block неполный;
- delta отсутствует;
- dominance unclear;
- values есть, но не дают usable interpretation.

### Signal range
- `bullish`
- `bearish`
- `neutral`

### Allowed conclusion shape
Говорить только о:
- подтверждении/неподтверждении движения объёмом;
- buyer dominance / seller dominance;
- mixed flow;
- exhaustion candidate / no exhaustion confirmation.

### Forbidden overclaims
Запрещено:
- “большой объём = гарантированное продолжение”;
- трактовать одну только дельту как полноценный торговый сценарий.

---

## 3. rsi_macd

### Strategy identity
- `strategy_id`: `rsi_macd`
- `strategy_name`: `RSI + MACD`

### Core dependency
- `rsi_14`
- `rsi_state`
- `macd_12_26_9_line`
- `macd_12_26_9_signal`
- `macd_12_26_9_hist`

### Extended support fields
- `macd_cross_up`
- `macd_cross_down`
- `macd_hist_slope`
- `rsi_macd_bullish_cluster_flag`
- `rsi_macd_bearish_cluster_flag`
- `rsi_macd_bullish_reversal_flag`
- `rsi_macd_bearish_reversal_flag`

### Usable rule
Использовать, если:
- RSI валиден;
- MACD валиден;
- histogram валидна;
- momentum regime можно классифицировать.

### Partial rule
Считать `partial`, если:
- RSI или MACD отсутствуют;
- значения нулевые/сломанные;
- histogram/slope отсутствуют настолько, что interpretation ломается.

### Signal range
- `bullish`
- `bearish`
- `neutral`

### Allowed conclusion shape
Говорить только о:
- momentum state;
- oversold / overbought;
- reversal candidate / no confirmation;
- histogram improving / weakening.

### Forbidden overclaims
Запрещено:
- `oversold = reversal`;
- `overbought = reversal`;
- `positive histogram = fully confirmed continuation`;
- один индикатор как полноценный рынок-прогноз.

---

## 4. trade_speed

### Strategy identity
- `strategy_id`: `trade_speed`
- `strategy_name`: `Trade Speed`

### Core dependency
- `trade_speed_ratio`
- `aggressive_buy_rate`
- `aggressive_sell_rate`
- `buy_sell_imbalance`

### Extended support fields
- `trade_speed_now`
- `trade_speed_ma`
- `volume_per_sec`
- `avg_trade_size`
- `burst_detected`
- `flow_accelerating`
- `flow_decelerating`
- `flow_absorption_flag`
- `flow_exhaustion_flag`

### Usable rule
Использовать, если:
- speed сравнима с baseline;
- direction потока читается;
- imbalance and flow context позволяют понять подтверждение движения.

### Partial rule
Считать `partial`, если:
- speed есть, но нет direction;
- baseline comparison отсутствует;
- flow block неполный.

### Signal range
- `bullish`
- `bearish`
- `neutral`

### Allowed conclusion shape
Говорить только о:
- повышенной/пониженной активности;
- direction of flow;
- whether flow supports current move;
- burst / no burst;
- acceleration / deceleration.

### Forbidden overclaims
Запрещено:
- `high speed = bullish/bearish` без direction;
- `burst = breakout confirmed`;
- любой speed-only signal.

---

## 5. added_later_placeholder

### Strategy identity
- `strategy_id`: `added_later_placeholder`
- `strategy_name`: `Added Later Placeholder`

### Core dependency
- none

### Usable rule
Не использовать как аналитическую стратегию до реальной реализации.

### Partial rule
Всегда:
- `partial`
или
- `skipped`

### Signal range
- `ignore`

### Allowed conclusion shape
Говорить только:
- стратегия не реализована;
- аналитический вывод не формируется.

### Forbidden overclaims
Запрещено:
- любые реальные аналитические сигналы;
- заполнение “для полноты”.

---

## 6. elliott_waves

### Strategy identity
- `strategy_id`: `elliott_waves`
- `strategy_name`: `Elliott Waves`

### Core dependency
- `elliott_direction`
- `elliott_pattern_family`
- `elliott_candidate_wave`
- `elliott_confidence`
- `elliott_status`

### Extended support fields
- `elliott_wave_count`
- `elliott_swing_sequence`
- `elliott_invalidation_price`
- structural fib context
- levels context

### Usable rule
Использовать, если:
- Elliott block существует;
- candidate/unclear structure можно честно описать;
- status читается осмысленно.

### Partial rule
Считать `partial`, если:
- Elliott block неполный;
- structure распадается;
- interpretation semantically unusable.

### Signal range
- чаще `neutral`
- иногда weak `bullish`
- иногда weak `bearish`

### Allowed conclusion shape
Говорить только о:
- correction;
- candidate structure;
- unclear structure;
- no confirmed impulse;
- tentative scenario only.

### Forbidden overclaims
Запрещено:
- deterministic wave forecast;
- “подтверждённая волна” без очень сильного evidence;
- сильный сценарный claim по weak candidate.

---

## Global rules

### Rule G1
Если core dependency невалиден — стратегия не usable.

### Rule G2
`partial` нельзя маскировать под `ready` сильным текстом.

### Rule G3
`signal` и `conclusion` должны быть согласованы.

### Rule G4
Heuristic strategies автоматически требуют более осторожного языка.

### Rule G5
`added_later_placeholder` не участвует в реальной аналитике.

---

## Operational baseline use

Этот документ является baseline для:
- strategy execution;
- decision schema;
- pre-run validation;
- pre-write validation;
- downstream consistency.
