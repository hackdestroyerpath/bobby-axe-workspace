# MAFFI TODO

Статус: полный TODO-лист, собранный на основе `WISH_LIST_ALGO.md`.
Дата: 2026-03-24

---

# Цель

Собрать полный production-flow для нового формата работы Maffi, где по триггеру вида:

- `Bing BTC, Maffi`

Maffi получает:
- `ticker`
- `timeframe`
- `request_ts_utc`
- `direction`
- `algo_payload`

после чего вызывает **отдельную LLM под конкретный тикер** и возвращает:
- `TP`
- `SL`
- `Grids`
- `Price_up`
- `Price_down`
- `Короткое заключение`

---

# PHASE 1 — Data contract for LLM payload

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

# PHASE 2 — Tick-to-feature algorithm layer

## 8. Собрать preprocessing pipeline под LLM-flow

### Что сделать
Подготовить слой преобразования сырых тиков в агрегированный feature-pack:
- очистка тиков
- дедупликация
- сортировка
- фильтрация аномалий
- обработка gaps

### Что должно быть на выходе
- стабильный preprocessing перед feature extraction
- trace качества входа
- отсутствие передачи грязых тиков дальше в LLM-слой

### Артефакт
- `Maffi/LLM_PREPROCESSING_SPEC.md`

---

## 9. Собрать market snapshot engine

### Что сделать
Считать базовые агрегаты текущего состояния рынка:
- `last_price`
- `mark_price`
- `index_price`
- `vwap_1m/5m/15m`
- `trade_count_1m/5m`
- `volume_1m/5m`
- `notional_1m/5m`

### Что должно быть на выходе
- компактный market snapshot block
- единый слой текущего контекста цены и активности

### Артефакт
- `Maffi/examples/market_snapshot_example.json`

---

## 10. Собрать price structure engine

### Что сделать
Считать краткосрочную геометрию рынка:
- OHLC для `1m` и `5m`
- локальные экстремумы `15m`
- диапазоны
- позицию цены внутри диапазона
- дистанцию до high/low

### Что должно быть на выходе
- price structure block
- база для определения рабочей геометрии сетки

### Артефакт
- `Maffi/examples/price_structure_example.json`

---

## 11. Собрать volatility engine

### Что сделать
Считать:
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

### Что должно быть на выходе
- volatility block
- база для диапазона, TP/SL и grid density

### Артефакт
- `Maffi/examples/volatility_example.json`

---

## 12. Собрать order flow engine

### Что сделать
Считать:
- buy/sell volumes
- delta
- cumulative delta
- imbalance ratios
- aggression score
- dominant side
- order flow confidence

### Что должно быть на выходе
- order flow block
- подтверждение или опровержение заданного direction

### Артефакт
- `Maffi/examples/order_flow_example.json`

---

## 13. Собрать regime engine

### Что сделать
Определять:
- `market_regime`
- `regime_confidence`
- `trend_strength_score`
- `trend_persistence_score`
- `mean_reversion_score`
- `chop_score`
- `noise_score`
- `reversal_frequency_score`

### Что должно быть на выходе
- regime block
- основа для интерпретации сетки LLM-моделью

### Артефакт
- `Maffi/examples/regime_example.json`

---

## 14. Собрать support/resistance engine

### Что сделать
На основе тиков и кратких агрегатов считать:
- support zones
- resistance zones
- invalidation distances
- boundary reaction
- bounce frequency
- wick rejection
- level respect

### Что должно быть на выходе
- zone block
- база для `Price_up`, `Price_down`, `TP`, `SL`

### Артефакт
- `Maffi/examples/support_resistance_example.json`

---

## 15. Собрать grid geometry hints engine

### Что сделать
Считать предварительные подсказки:
- `recommended_price_down`
- `recommended_price_up`
- `recommended_grid_step`
- `recommended_grid_count_min`
- `recommended_grid_count_max`
- `recommended_tp_zone`
- `recommended_sl_zone`
- `grid_width_hint`
- `grid_density_hint`

### Что должно быть на выходе
- geometry hints block
- сужение пространства решений для LLM

### Артефакт
- `Maffi/examples/grid_geometry_hints_example.json`

---

## 16. Собрать grid candidates scoring layer

### Что сделать
Генерировать 2–4 grid-кандидата, для каждого считать:
- `candidate_id`
- `price_down`
- `price_up`
- `grid_count`
- `grid_step`
- `efficiency_score`
- подскоринги
- `candidate_notes`

### Что должно быть на выходе
- ranked candidates block
- кандидаты, из которых LLM будет выбирать или доуточнять лучший вариант

### Артефакт
- `Maffi/examples/grid_candidates_ranked.json`

---

## 17. Собрать quality/trust block

### Что сделать
Считать:
- `input_quality_status`
- `data_quality_score`
- `coverage_ratio`
- `largest_gap_seconds`
- `outlier_ratio`
- `liquidity_quality_score`
- `payload_confidence`
- `degradation_flags`

### Что должно быть на выходе
- quality/trust block
- честная оценка надёжности входа

### Артефакт
- `Maffi/examples/quality_trust_example.json`

---

# PHASE 3 — Prompt and ticker-specific LLM routing

## 18. Собрать canonical prompt template

### Что сделать
Создать единый шаблон prompt для Maffi LLM-flow:
- system rules
- input format
- expected JSON-only output
- ограничения на стиль заключения
- запрет на капитал / аллокацию

### Что должно быть на выходе
- один canonical prompt template
- единое поведение всех тикерных моделей

### Артефакт
- `Maffi/PROMPT_TEMPLATE.md`

---

## 19. Развести ticker-specific LLM routing

### Что сделать
Зафиксировать правило: каждому тикеру соответствует свой LLM execution context.

Нужно определить:
- как маппится `ticker -> model/context`
- как хранится конфиг по тикеру
- как задаются overrides по prompt или risk-mode

### Что должно быть на выходе
- ticker routing policy
- конфигурация LLM per ticker

### Артефакт
- `Maffi/TICKER_LLM_ROUTING.md`

---

## 20. Собрать prompt-control policy

### Что сделать
Определить управление режимом ответа:
- `response_mode`
- `must_return_fields`
- `language`
- `max_rationale_sentences`
- `style_hint`
- `risk_mode`
- `no_capital_allocation`

### Что должно быть на выходе
- prompt control block
- строгое управление форматом LLM-ответа

### Артефакт
- `Maffi/PROMPT_CONTROL_POLICY.md`

---

## 21. Подготовить prompt-ready examples

### Что сделать
Собрать примеры полного входа в LLM:
- long case
- short case
- weak case
- chaotic case

### Что должно быть на выходе
- набор эталонных prompt payloads
- база для ручной и автоматической проверки prompt quality

### Артефакт
- `Maffi/examples/prompt_ready_long.json`
- `Maffi/examples/prompt_ready_short.json`
- `Maffi/examples/prompt_ready_weak.json`
- `Maffi/examples/prompt_ready_chaotic.json`

---

# PHASE 4 — Validation and post-LLM control

## 22. Собрать LLM output validator

### Что сделать
Проверять, что LLM всегда возвращает:
- валидный JSON
- все обязательные поля
- корректные числовые значения
- логичный диапазон `price_down < price_up`
- адекватный `grids`
- осмысленные `tp/sl`

### Что должно быть на выходе
- post-LLM validator
- защита от плохих или битых ответов модели

### Артефакт
- `Maffi/LLM_OUTPUT_VALIDATOR.md`

---

## 23. Собрать fallback / reject policy

### Что сделать
Определить, что делать если:
- JSON битый
- поля отсутствуют
- TP/SL нелогичны
- диапазон инвертирован
- grids невалидны
- conclusion пустой или противоречивый

### Что должно быть на выходе
- fallback policy
- reject policy
- режим повторного вызова или отказа

### Артефакт
- `Maffi/LLM_FALLBACK_POLICY.md`

---

## 24. Собрать traceability for LLM output

### Что сделать
Для каждого вызова фиксировать:
- исходный trigger
- payload version
- prompt version
- ticker/model mapping
- raw response
- normalized response
- validator result
- final accepted output

### Что должно быть на выходе
- audit trail по каждому LLM-вызову
- воспроизводимость решений

### Артефакт
- `Maffi/LLM_TRACEABILITY_SPEC.md`

---

## 25. Нормализовать final response envelope

### Что сделать
Собрать единый финальный объект ответа для внешнего контура.

Должны быть:
- request metadata
- chosen ticker/direction/timeframe
- normalized TP/SL/Grids/Price_up/Price_down
- conclusion
- output validity status
- confidence / trust indicators

### Что должно быть на выходе
- единый output envelope
- стабильный handoff для orchestration

### Артефакт
- `Maffi/FINAL_RESPONSE_ENVELOPE.md`

---

# PHASE 5 — Runtime integration and production handoff

## 26. Собрать live trigger flow

### Что сделать
Связать trigger вида:
- `Bing BTC, Maffi`
с runtime flow:
- parse trigger
- fetch algo_payload
- route to ticker LLM
- validate output
- return final result

### Что должно быть на выходе
- живой end-to-end runtime path
- ясная схема вызова Maffi по триггеру

### Артефакт
- `Maffi/LIVE_TRIGGER_FLOW.md`

---

## 27. Связать orchestration и payload delivery

### Что сделать
Определить, как именно внешний слой доставляет `algo_payload` в Maffi:
- API / session / queue / file / internal call
- версия payload
- контроль целостности
- таймауты и retry behavior

### Что должно быть на выходе
- runtime delivery contract
- orchestration handoff spec

### Артефакт
- `Maffi/RUNTIME_DELIVERY_CONTRACT.md`

---

## 28. Собрать acceptance / regression suite для нового LLM-flow

### Что сделать
Автоматизировать сценарии:
- healthy long
- healthy short
- weak confidence
- chaotic market
- bad payload
- invalid LLM output
- fallback path
- full end-to-end trigger flow

### Что должно быть на выходе
- regression suite
- acceptance suite
- защита от деградации при следующих изменениях

### Артефакт
- `Maffi/LLM_FLOW_ACCEPTANCE.md`

---

## 29. Подготовить production release checklist

### Что сделать
Собрать финальный список готовности:
- contracts approved
- payload examples ready
- prompt template ready
- ticker routing ready
- validators ready
- fallback policy ready
- audit trail ready
- trigger flow ready
- tests green

### Что должно быть на выходе
- единый go-live checklist
- критерий готовности production release

### Артефакт
- `Maffi/PRODUCTION_RELEASE_CHECKLIST.md`

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

Весь TODO считается закрытым, если:
1. собран канонический LLM trigger contract;
2. собран полный compact algo_payload standard;
3. реализован tick-to-feature layer;
4. собран prompt layer и ticker-specific routing;
5. есть post-LLM validation и fallback policy;
6. есть final response envelope;
7. есть live trigger flow;
8. orchestration handoff работает;
9. acceptance/regression suite зелёная;
10. production release checklist закрыт.
