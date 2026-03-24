# WISH_LIST_ALGO

Статус: updated for new LLM-per-ticker workflow.
Дата: 2026-03-24

---

# 0. Новый рабочий формат Maffi

## Trigger
Пользователь говорит: **"Bing BTC, Maffi"**.

## На вход Maffi приходит
- `ticker` — например `BTC`
- `timeframe` — сейчас базово `1m`
- `request_ts` — текущая временная метка
- `direction` — заранее заданное направление сетки, например `Long`
- `algo_payload` — подготовленные алгоритмами признаки, рассчитанные на основе тиков

## Что делает Maffi
Maffi **не строит всю сетку формулами сам**, а делает **LLM decision call** в отдельную LLM-модель для конкретного тикера.

## Что должна выдать LLM
- `TP`
- `SL`
- `Grids`
- `Price_up`
- `Price_down`
- `Короткое заключение`

---

# 1. Цель документа

Определить, **какие именно данные надо заранее вычислять из тиков**, чтобы LLM-анализ по конкретному тикеру был максимально эффективным, устойчивым и полезным для генерации параметров сетки.

Ключевой принцип:

**В LLM нельзя тащить сырые тики.**  
В LLM нужно подавать **сжатый, информативный, структурированный feature-pack**, который уже содержит только то, что реально влияет на TP / SL / диапазон / количество сеток / краткое заключение.

---

# 2. Главный вывод по текущему состоянию

Из того, что уже собрано в Maffi:
- contract-first слой уже есть;
- validator / preprocessing / scoring / traceability уже начали формироваться;
- значит, база для нового LLM-flow уже хорошая;
- менять нужно **не всё ядро**, а прежде всего **формат входа для LLM и состав algo_payload**.

То есть новый pipeline должен быть таким:

`ticks -> preprocessing -> feature extraction -> compact algo_payload -> LLM prompt per ticker -> final grid answer`

---

# 3. Какой должен быть принцип отбора данных для LLM

В payload должны входить только данные, которые отвечают на 6 вопросов:

1. Где цена сейчас?
2. В каком состоянии рынок: тренд, range, хаос?
3. Насколько рынок волатильный именно сейчас?
4. Кто доминирует по потоку: buyers или sellers?
5. Где ближайшие рабочие границы и зоны invalidation?
6. Насколько плотной или редкой должна быть сетка?

Если поле не помогает ответить хотя бы на один из этих вопросов, его не надо тащить в prompt.

---

# 4. Детальный wish-list данных для algo_payload

Ниже — **детальный список**, что нужно считать из тиков до вызова LLM.

## 4.1. Блок request context
Это служебный верхний блок.

Обязательные поля:
- `ticker`
- `timeframe`
- `request_ts_utc`
- `direction`
- `exchange`
- `lookback_window_minutes`
- `payload_version`

Зачем нужен:
- чтобы LLM понимала контекст запроса,
- для какого окна рассчитаны признаки,
- в какую сторону уже требуется строить сетку.

---

## 4.2. Блок market snapshot
Базовая картина рынка в момент запроса.

Поля:
- `last_price`
- `mark_price` (если есть)
- `index_price` (если есть)
- `vwap_1m`
- `vwap_5m`
- `vwap_15m`
- `trade_count_1m`
- `trade_count_5m`
- `volume_1m`
- `volume_5m`
- `notional_1m`
- `notional_5m`

Зачем нужен:
- чтобы LLM понимала текущую цену,
- активность рынка,
- и отклонение цены от средней зоны стоимости.

---

## 4.3. Блок short-term price structure
Это геометрия цены на коротком горизонте.

Поля:
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

Зачем нужен:
- LLM должна понять, находится ли цена у верхней части хода, у нижней или в середине;
- это прямо влияет на `Price_up`, `Price_down`, TP и плотность сетки.

---

## 4.4. Блок volatility
Один из самых важных блоков.

Поля:
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

Зачем нужен:
- для выбора ширины диапазона;
- для выбора TP и SL буферов;
- для выбора grid count;
- для фильтрации слишком хаотичных участков.

---

## 4.5. Блок order flow
LLM нужно видеть, кто давит рынок по тикам.

Поля:
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

Зачем нужен:
- если направление заранее задано как `Long`, LLM должна понимать, подтверждает ли поток этот direction или нет;
- это влияет на confidence ответа, глубину сетки и аккуратность TP/SL.

---

## 4.6. Блок trend / regime
LLM нельзя заставлять самой угадывать режим только по описанию цены. Ей лучше дать уже собранную оценку режима.

Поля:
- `market_regime`
  - `trend_up`
  - `trend_down`
  - `range_balanced`
  - `chaotic_high_risk`
- `regime_confidence`
- `trend_strength_score`
- `trend_persistence_score`
- `mean_reversion_score`
- `chop_score`
- `noise_score`
- `reversal_frequency_score`

Зачем нужен:
- если рынок range — LLM строит одну геометрию;
- если трендовый — другую;
- если chaotic — может сузить диапазон или резко понизить confidence.

---

## 4.7. Блок support / resistance / invalidation zones
Это критично для `Price_up`, `Price_down`, TP и SL.

Поля:
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

Зачем нужен:
- LLM должна понимать, где рынок реально реагирует;
- именно эти зоны станут базой для нижней/верхней границы и stop invalidation.

---

## 4.8. Блок grid geometry hints
Это уже не готовая сетка, а именно algorithmic hints для LLM.

Поля:
- `recommended_price_down`
- `recommended_price_up`
- `recommended_grid_step`
- `recommended_grid_count_min`
- `recommended_grid_count_max`
- `recommended_tp_zone`
- `recommended_sl_zone`
- `grid_width_hint`
- `grid_density_hint`

Зачем нужен:
- LLM не должна с нуля придумывать математику диапазона;
- алгоритмы должны заранее сузить пространство решений.

---

## 4.9. Блок grid candidate scoring
Лучше всего подавать в LLM не одну подсказку, а 2–4 готовых кандидата.

Для каждого кандидата:
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

Зачем нужен:
- LLM будет не «фантазировать», а выбирать/докручивать лучший из качественных вариантов.

---

## 4.10. Блок quality / trust
LLM обязательно должна знать, насколько надёжны данные.

Поля:
- `input_quality_status`
- `data_quality_score`
- `coverage_ratio`
- `largest_gap_seconds`
- `outlier_ratio`
- `liquidity_quality_score`
- `payload_confidence`
- `degradation_flags`

Зачем нужен:
- чтобы LLM не выдавала слишком уверенный ответ на плохом входе;
- чтобы заключение было честным.

---

## 4.11. Блок prompt-control fields
Это поля специально для качества ответа модели.

Поля:
- `response_mode` = `grid_generation`
- `must_return_fields`
- `language`
- `max_rationale_sentences`
- `style_hint`
- `risk_mode`
- `no_capital_allocation = true`

Зачем нужен:
- чтобы каждая тикерная LLM отвечала строго в нужном формате и не растекалась.

---

# 5. Минимальный payload, без которого LLM уже неэффективна

Если совсем уж сокращать до минимального полезного набора, то я бы считал обязательными:
- `ticker`
- `timeframe`
- `request_ts_utc`
- `direction`
- `last_price`
- `vwap_5m`
- `local_high_15m`
- `local_low_15m`
- `atr_like_5m`
- `realized_vol_5m`
- `delta_5m`
- `cumulative_delta_5m`
- `dominant_side`
- `market_regime`
- `regime_confidence`
- `support_zone_low`
- `support_zone_high`
- `resistance_zone_low`
- `resistance_zone_high`
- `recommended_price_down`
- `recommended_price_up`
- `recommended_grid_count_min`
- `recommended_grid_count_max`
- `recommended_tp_zone`
- `recommended_sl_zone`
- `2-4 grid_candidates`
- `input_quality_status`
- `payload_confidence`

---

# 6. Рекомендуемый формат ответа LLM

LLM должна возвращать строго:

```json
{
  "ticker": "BTC",
  "timeframe": "1m",
  "direction": "Long",
  "tp": 87250.0,
  "sl": 86420.0,
  "grids": 9,
  "price_up": 87080.0,
  "price_down": 86610.0,
  "conclusion": "Long grid favored inside active support-to-resistance corridor; bullish flow confirms controlled upside continuation."
}
```

---

# 7. План по шагам — 5 фаз

## Phase 1 — Data contract for LLM payload

### Цель
Построить **канонический входной контракт** для нового LLM-flow, чтобы любая тикерная модель получала одинаково структурированный, короткий и полезный payload.

### Подзадачи

#### 1. Зафиксировать новый trigger contract
Определить жёсткий формат запроса:
- `ticker`
- `timeframe`
- `request_ts_utc`
- `direction`
- `algo_payload`

#### 2. Определить обязательные блоки payload
Зафиксировать, что в payload всегда должны быть:
- request context
- market snapshot
- price structure
- volatility
- order flow
- market regime
- support/resistance
- grid geometry hints
- grid candidates
- quality/trust block

#### 3. Разделить поля на обязательные и расширенные
Разбить поля на:
- `required`
- `recommended`
- `optional`
- `prompt-control`

#### 4. Убрать из payload всё лишнее
Сделать правило:
- сырые тики не передавать;
- длинные массивы не передавать;
- только агрегаты, score, hints и zones.

#### 5. Зафиксировать единицы измерения
Для каждого поля определить:
- price units
- volume units
- score scale
- confidence scale
- timestamp format

#### 6. Определить output contract LLM
Фиксировать жёсткий JSON output:
- `TP`
- `SL`
- `Grids`
- `Price_up`
- `Price_down`
- `Короткое заключение`

#### 7. Подготовить примеры
Собрать минимум:
- healthy long payload
- healthy short payload
- weak/low-confidence payload
- chaotic payload

### Definition of Done Phase 1
Фаза считается закрытой, если:
- есть канонический входной контракт для LLM;
- есть минимальный и расширенный набор полей;
- есть примеры payload;
- есть жёсткий output contract LLM.

---

## Phase 2 — Tick-to-feature algorithm layer
- Реализовать и/или дожать алгоритмы преобразования тиков в compact feature-pack.
- Зафиксировать preprocessing, volatility, order-flow, regime и zone engines.
- Утвердить quality/degradation logic.

## Phase 3 — Prompt and ticker-specific LLM routing
- Определить prompt-template для каждой тикерной LLM.
- Зафиксировать правила подачи direction и algo_payload в модель.
- Утвердить строгий режим ответа JSON-only.

## Phase 4 — Validation and post-LLM control
- Проверять ответ LLM на shape, диапазоны, логичность TP/SL и сетки.
- Добавить fallback/reject policy при плохом ответе модели.
- Добавить traceability для LLM output.

## Phase 5 — Runtime integration and production handoff
- Встроить новый flow в live trigger `Bing BTC, Maffi`.
- Подключить orchestration и логирование.
- Подготовить acceptance/regression suite для production-режима.

---

# 8. Итог

Для нового формата работы Maffi ключевой вопрос уже не «как передать сырые тики», а **какой compact algo_payload дать LLM, чтобы она качественно сгенерировала TP / SL / Grids / Price_up / Price_down / conclusion**.

Лучший вариант — подавать в модель:
- текущий контекст запроса,
- агрегированную структуру цены,
- волатильность,
- order flow,
- market regime,
- уровни поддержки/сопротивления,
- готовые grid geometry hints,
- несколько grid candidates со score,
- и quality flags.

Именно такой вход даст наиболее сильный и контролируемый LLM-ответ.
