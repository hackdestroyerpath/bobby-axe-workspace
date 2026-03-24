# MAFFI TODO

Статус: TODO-лист, собранный на основе `WISH_LIST_ALGO.md / Phase 1`.
Дата: 2026-03-24

---

# Цель

Собрать **канонический входной контракт для нового LLM-flow Maffi**, чтобы по триггеру вида:

- `Bing BTC, Maffi`

Maffi получал на вход:
- `ticker`
- `timeframe`
- `request_ts_utc`
- `direction`
- `algo_payload`

и мог передавать в отдельную LLM по тикеру **структурированный и эффективный payload**, на основе которого модель будет генерировать:
- `TP`
- `SL`
- `Grids`
- `Price_up`
- `Price_down`
- `Короткое заключение`

---

# PHASE 1 TODO

## 1. Зафиксировать новый trigger contract

### Что сделать
Определить жёсткий формат запроса в Maffi:
- `ticker`
- `timeframe`
- `request_ts_utc`
- `direction`
- `algo_payload`

### Что должно быть на выходе
- единый контракт входа для runtime
- единый shape для trigger-вызова
- отсутствие двусмысленности по обязательным полям

### Артефакт
- `Maffi/LLM_TRIGGER_CONTRACT.md`

---

## 2. Зафиксировать обязательные блоки payload

### Что сделать
Определить, что в `algo_payload` всегда должны входить следующие блоки:
- `request_context`
- `market_snapshot`
- `price_structure`
- `volatility`
- `order_flow`
- `market_regime`
- `support_resistance`
- `grid_geometry_hints`
- `grid_candidates`
- `quality_trust`
- `prompt_control`

### Что должно быть на выходе
- список обязательных секций payload
- канонический порядок секций
- понятный каркас для prompt-building

### Артефакт
- `Maffi/LLM_PAYLOAD_BLOCKS.md`

---

## 3. Разделить поля payload на required / recommended / optional

### Что сделать
Для каждого блока определить поля трёх уровней:
- `required`
- `recommended`
- `optional`

Дополнительно отдельно отметить:
- `prompt_control` поля
- поля, которые нельзя передавать как сырые массивы

### Что должно быть на выходе
- таблица обязательности полей
- минимальный payload
- расширенный payload

### Артефакт
- `Maffi/LLM_PAYLOAD_FIELD_MATRIX.md`

---

## 4. Убрать из payload всё лишнее

### Что сделать
Зафиксировать правило минимизации:
- не передавать сырые тики в LLM
- не передавать длинные массивы сделок
- не передавать лишние технические поля
- передавать только агрегаты, score, zones, hints и quality flags

### Что должно быть на выходе
- compact payload standard
- список запрещённых/нежелательных полей
- правило сокращения prompt noise

### Артефакт
- `Maffi/LLM_PAYLOAD_MINIMIZATION_RULES.md`

---

## 5. Зафиксировать единицы измерения

### Что сделать
Для каждого поля определить единицы измерения:
- цены
- объёмы
- notional
- score
- confidence
- timestamps
- процентили

### Что должно быть на выходе
- единый unit-policy
- отсутствие путаницы по шкалам
- единый формат времени и confidence

### Артефакт
- `Maffi/LLM_PAYLOAD_UNITS.md`

---

## 6. Зафиксировать output contract LLM

### Что сделать
Определить жёсткий формат ответа LLM.

Обязательные поля ответа:
- `ticker`
- `timeframe`
- `direction`
- `tp`
- `sl`
- `grids`
- `price_up`
- `price_down`
- `conclusion`

### Что должно быть на выходе
- JSON output contract
- единый shape ответа для всех тикеров
- правила reject/fallback при плохом ответе LLM

### Артефакт
- `Maffi/LLM_OUTPUT_CONTRACT.md`
- при необходимости `Maffi/llm_output_contract.json`

---

## 7. Собрать примеры payload

### Что сделать
Подготовить минимум 4 эталонных примера:
- `healthy_long_payload`
- `healthy_short_payload`
- `weak_confidence_payload`
- `chaotic_payload`

### Что должно быть на выходе
- набор готовых reference examples
- база для prompt-тестов
- база для future validator/acceptance checks

### Артефакт
- `Maffi/examples/healthy_long_payload.json`
- `Maffi/examples/healthy_short_payload.json`
- `Maffi/examples/weak_confidence_payload.json`
- `Maffi/examples/chaotic_payload.json`

---

# Дополнительный список данных, которые особенно важны для algo_payload

## Request context
- `ticker`
- `timeframe`
- `request_ts_utc`
- `direction`
- `exchange`
- `lookback_window_minutes`
- `payload_version`

## Market snapshot
- `last_price`
- `mark_price`
- `index_price`
- `vwap_1m`
- `vwap_5m`
- `vwap_15m`
- `trade_count_1m`
- `trade_count_5m`
- `volume_1m`
- `volume_5m`
- `notional_1m`
- `notional_5m`

## Price structure
- `open_1m`
- `high_1m`
- `low_1m`
- `close_1m`
- `open_5m`
- `high_5m`
- `low_5m`
- `close_5m`
- `local_high_15m`
- `local_low_15m`
- `range_width_1m`
- `range_width_5m`
- `close_position_in_1m_range`
- `close_position_in_5m_range`
- `distance_to_local_high`
- `distance_to_local_low`

## Volatility
- `atr_like_1m`
- `atr_like_5m`
- `realized_vol_1m`
- `realized_vol_5m`
- `return_std_1m`
- `return_std_5m`
- `volatility_percentile_1h`
- `volatility_regime`
- `impulse_size_last_move`
- `impulse_duration_seconds`
- `volatility_stability_score`

## Order flow
- `buy_volume_1m`
- `sell_volume_1m`
- `buy_volume_5m`
- `sell_volume_5m`
- `delta_1m`
- `delta_5m`
- `cumulative_delta_5m`
- `imbalance_ratio_1m`
- `imbalance_ratio_5m`
- `aggression_score_buy`
- `aggression_score_sell`
- `dominant_side`
- `order_flow_confidence`

## Market regime
- `market_regime`
- `regime_confidence`
- `trend_strength_score`
- `trend_persistence_score`
- `mean_reversion_score`
- `chop_score`
- `noise_score`
- `reversal_frequency_score`

## Support / resistance
- `support_zone_low`
- `support_zone_high`
- `resistance_zone_low`
- `resistance_zone_high`
- `nearest_support_distance`
- `nearest_resistance_distance`
- `boundary_reaction_score`
- `bounce_frequency_score`
- `wick_rejection_score_upper`
- `wick_rejection_score_lower`
- `level_respect_score`

## Grid geometry hints
- `recommended_price_down`
- `recommended_price_up`
- `recommended_grid_step`
- `recommended_grid_count_min`
- `recommended_grid_count_max`
- `recommended_tp_zone`
- `recommended_sl_zone`
- `grid_width_hint`
- `grid_density_hint`

## Grid candidates
- `candidate_id`
- `price_down`
- `price_up`
- `grid_count`
- `grid_step`
- `efficiency_score`
- `range_utilization_score`
- `oscillation_score`
- `step_quality_score`
- `stability_score`
- `boundary_respect_score`
- `candidate_notes`

## Quality / trust
- `input_quality_status`
- `data_quality_score`
- `coverage_ratio`
- `largest_gap_seconds`
- `outlier_ratio`
- `liquidity_quality_score`
- `payload_confidence`
- `degradation_flags`

## Prompt control
- `response_mode`
- `must_return_fields`
- `language`
- `max_rationale_sentences`
- `style_hint`
- `risk_mode`
- `no_capital_allocation`

---

# Definition of Done

Phase 1 считается закрытой, если:
1. есть канонический trigger contract;
2. есть список обязательных блоков payload;
3. поля разделены на required / recommended / optional;
4. зафиксированы правила minimization;
5. зафиксированы units;
6. есть жёсткий output contract LLM;
7. собраны reference payload examples.
