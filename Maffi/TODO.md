# MAFFI INPUT CONTRACT DRAFT

## Детальный входной контракт для Maffi
**Статус:** локальный черновик / готов к согласованию перед выгрузкой в GitHub  
**Назначение:** определить точный набор данных, которые внешние алгоритмы должны подготавливать для Maffi перед каждым пингом по тикеру, чтобы Maffi мог выдать финальные параметры grid setup на таймфрейме 5m.

---

# 1. Цель документа

Этот документ фиксирует **не итоговую сетку**, а именно **входной пакет признаков**, который должен приходить в Maffi от внешнего контура расчётов.

Maffi не должен получать в сообщении миллионы сырых тиков.  
Maffi должен получать **сжатый, структурированный, детальный decision-package**, уже рассчитанный алгоритмами поверх тикового потока.

После получения этого пакета Maffi обязан по тикеру вернуть:
- `ticker`
- `frame=5m`
- `direction` (`Long` / `Short`)
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `tp`
- `sl`
- желательно также: `grid_mid_price`, `efficiency_score`, `rationale`

---

# 2. Общая логика pipeline

## Что происходит до Maffi

До пинга Maffi внешний слой должен:
1. прочитать сырые тики из хранилища Jack
2. очистить поток
3. агрегировать тики
4. посчитать волатильность
5. посчитать структуру движения
6. посчитать order-flow признаки
7. определить режим рынка
8. посчитать кандидаты диапазона сетки
9. подготовить единый input-payload

## Что делает Maffi

Maffi получает готовый payload и на его основе:
1. проверяет качество данных
2. определяет пригодность рынка под сетку
3. принимает `Long` / `Short` / `Reject`
4. выбирает `lower` / `upper`
5. выбирает `grid_count`
6. рассчитывает `tp` / `sl`
7. возвращает итоговый grid proposal

---

# 3. Общие требования к входному payload

## 3.1. Главные принципы

Входной payload должен быть:
- **одним объектом на один тикер**
- **полностью самодостаточным**
- **машинно-читаемым**
- **стабильным по полям**
- **без двусмысленности в единицах измерения**

## 3.2. Формат

Рекомендуемый формат — JSON object.

## 3.3. Тип вызова

Один запрос = один тикер.

## 3.4. Обязательная политика

Если каких-то обязательных данных нет, payload должен содержать явный статус неполноты, а не молча пропускать поле.

---

# 4. Верхнеуровневая структура payload

```json
{
  "schema_version": "1.0",
  "generated_at_utc": "2026-03-24T00:00:00Z",
  "ticker": "BTCUSDC",
  "frame": "5m",
  "data_quality": { ... },
  "market_snapshot": { ... },
  "price_structure": { ... },
  "volatility": { ... },
  "order_flow": { ... },
  "trend_structure": { ... },
  "market_regime": { ... },
  "support_resistance": { ... },
  "grid_candidates": { ... },
  "decision_hints": { ... }
}
```

---

# 5. Раздел data_quality

Этот раздел нужен, чтобы Maffi понимал, можно ли доверять входным данным.

## 5.1. Обязательные поля

- `status: str`
  - `ok`
  - `degraded`
  - `bad`

- `ticks_count_raw: int`
- `ticks_count_clean: int`
- `duplicate_ticks_removed: int`
- `bad_ticks_removed: int`
- `coverage_ratio: float`
- `time_span_seconds: int`
- `largest_gap_seconds: float`
- `outlier_ratio: float`
- `liquidity_quality_score: float`
- `data_quality_score: float`

## 5.2. Смысл полей

### `coverage_ratio`
Доля заполненности наблюдаемого окна.

### `largest_gap_seconds`
Максимальная дыра во времени между соседними валидными тиками.

### `liquidity_quality_score`
Оценка того, насколько поток вообще пригоден для анализа сетки.

### `data_quality_score`
Итоговая оценка качества входных данных от 0 до 100.

## 5.3. Для чего Maffi использует этот блок

- reject при плохом качестве данных
- понижение confidence
- понимание, можно ли доверять параметрам диапазона и направлению

---

# 6. Раздел market_snapshot

Этот блок описывает текущую базовую рыночную картину по тикеру.

## 6.1. Обязательные поля

- `last_price: float`
- `last_trade_ts_utc: str`
- `mid_reference_price: float`
- `vwap_1m: float`
- `vwap_5m: float`
- `vwap_15m: float`
- `trade_count_1m: int`
- `trade_count_5m: int`
- `trade_count_15m: int`
- `volume_1m: float`
- `volume_5m: float`
- `volume_15m: float`
- `avg_trade_size_1m: float`
- `avg_trade_size_5m: float`

## 6.2. Для чего нужен раздел

Даёт Maffi моментальный контекст:
- где цена сейчас
- насколько рынок живой
- есть ли достаточная торговая активность

---

# 7. Раздел price_structure

Это базовый блок геометрии рынка.

## 7.1. Обязательные поля

- `open_1m: float`
- `high_1m: float`
- `low_1m: float`
- `close_1m: float`
- `open_5m: float`
- `high_5m: float`
- `low_5m: float`
- `close_5m: float`
- `open_15m: float`
- `high_15m: float`
- `low_15m: float`
- `close_15m: float`
- `local_high_5m: float`
- `local_low_5m: float`
- `local_high_15m: float`
- `local_low_15m: float`
- `range_width_1m: float`
- `range_width_5m: float`
- `range_width_15m: float`
- `close_position_in_5m_range: float`
- `close_position_in_15m_range: float`
- `distance_to_5m_high: float`
- `distance_to_5m_low: float`
- `distance_to_15m_high: float`
- `distance_to_15m_low: float`

## 7.2. Нормализация

Позиционные коэффициенты (`close_position_in_5m_range`, и т.п.) лучше давать в диапазоне `0..1`.

## 7.3. Для чего нужен раздел

Нужен для ответа на вопросы:
- цена у верхней части диапазона или у нижней?
- рынок растянут или сбалансирован?
- есть ли место для Long или Short grid?

---

# 8. Раздел volatility

Один из самых важных блоков.

## 8.1. Обязательные поля

- `atr_like_30s: float`
- `atr_like_1m: float`
- `atr_like_5m: float`
- `realized_vol_30s: float`
- `realized_vol_1m: float`
- `realized_vol_5m: float`
- `return_std_30s: float`
- `return_std_1m: float`
- `return_std_5m: float`
- `volatility_percentile_1h: float`
- `volatility_regime: str`
  - `low`
  - `normal`
  - `elevated`
  - `extreme`
- `impulse_size_last_move: float`
- `impulse_duration_seconds: float`
- `volatility_stability_score: float`

## 8.2. Для чего нужен раздел

Maffi использует его для:
- выбора ширины диапазона
- выбора плотности сетки
- выбора буферов для TP и SL
- фильтрации хаотических режимов

---

# 9. Раздел order_flow

Этот блок нужен для выбора направления.

## 9.1. Обязательные поля

- `buy_volume_30s: float`
- `sell_volume_30s: float`
- `buy_volume_1m: float`
- `sell_volume_1m: float`
- `buy_volume_5m: float`
- `sell_volume_5m: float`
- `delta_30s: float`
- `delta_1m: float`
- `delta_5m: float`
- `cumulative_delta_5m: float`
- `imbalance_ratio_30s: float`
- `imbalance_ratio_1m: float`
- `imbalance_ratio_5m: float`
- `aggression_score_buy: float`
- `aggression_score_sell: float`
- `dominant_side: str`
  - `buy`
  - `sell`
  - `neutral`
- `order_flow_confidence: float`

## 9.2. Для чего нужен раздел

Позволяет понять:
- кто реально давит рынок
- есть ли подтверждение движения объёмом
- подтверждается ли выбранное направление реальным потоком сделок

---

# 10. Раздел trend_structure

Этот блок помогает понять характер движения.

## 10.1. Обязательные поля

- `price_slope_30s: float`
- `price_slope_1m: float`
- `price_slope_5m: float`
- `vwap_slope_1m: float`
- `vwap_slope_5m: float`
- `higher_highs_score: float`
- `higher_lows_score: float`
- `lower_highs_score: float`
- `lower_lows_score: float`
- `trend_strength_score: float`
- `trend_persistence_score: float`
- `mean_reversion_score: float`
- `chop_score: float`
- `noise_score: float`
- `reversal_frequency_score: float`

## 10.2. Для чего нужен раздел

Maffi использует его, чтобы:
- отличить тренд от шума
- не спутать range c impulse
- выбрать Long/Short более уверенно

---

# 11. Раздел market_regime

Это уже результат отдельной классификации, если внешний контур умеет её делать.

## 11.1. Обязательные поля

- `regime: str`
  - `trend_up`
  - `trend_down`
  - `range_balanced`
  - `chaotic_high_risk`
- `confidence: float`
- `trend_up_score: float`
- `trend_down_score: float`
- `range_score: float`
- `chaos_score: float`
- `regime_notes: str`

## 11.2. Для чего нужен раздел

Это сокращает пространство решения.  
Maffi не обязан слепо принимать этот режим, но должен учитывать его как сильную подсказку.

---

# 12. Раздел support_resistance

Этот раздел нужен для выбора границ сетки и постановки TP/SL.

## 12.1. Обязательные поля

- `support_zone_low: float`
- `support_zone_high: float`
- `resistance_zone_low: float`
- `resistance_zone_high: float`
- `nearest_support_distance: float`
- `nearest_resistance_distance: float`
- `boundary_reaction_score: float`
- `bounce_frequency_score: float`
- `wick_rejection_score_upper: float`
- `wick_rejection_score_lower: float`
- `level_respect_score: float`

## 12.2. Для чего нужен раздел

Помогает решить:
- где ставить нижнюю границу
- где ставить верхнюю границу
- где идея ломается
- где фиксировать take profit

---

# 13. Раздел grid_candidates

Это важнейший блок для сужения выбора.

## 13.1. Идея блока

Внешние алгоритмы не должны отдавать одну якобы “идеальную” сетку.  
Они должны считать **несколько кандидатов** и их score.

## 13.2. Формат

```json
{
  "candidate_count": 3,
  "candidates": [
    {
      "candidate_id": "A",
      "grid_lower_price": 84020.0,
      "grid_upper_price": 84580.0,
      "grid_width": 560.0,
      "grid_step": 51.0,
      "grid_count": 11,
      "range_utilization_score": 76,
      "oscillation_score": 68,
      "step_quality_score": 74,
      "stability_score": 71,
      "boundary_respect_score": 79,
      "grid_efficiency_score": 74,
      "candidate_notes": "Balanced active corridor"
    }
  ]
}
```

## 13.3. Обязательные поля каждого кандидата

- `candidate_id: str`
- `grid_lower_price: float`
- `grid_upper_price: float`
- `grid_width: float`
- `grid_step: float`
- `grid_count: int`
- `range_utilization_score: float`
- `oscillation_score: float`
- `step_quality_score: float`
- `stability_score: float`
- `boundary_respect_score: float`
- `grid_efficiency_score: float`
- `candidate_notes: str`

## 13.4. Для чего нужен раздел

Maffi должен выбирать не “из воздуха”, а из ранжированного списка реальных кандидатов.

---

# 14. Раздел decision_hints

Это слой итоговых подсказок от внешнего контура, но не финальное решение.

## 14.1. Обязательные поля

- `preferred_direction_hint: str`
  - `Long`
  - `Short`
  - `Neutral`
- `direction_hint_confidence: float`
- `recommended_candidate_id: str`
- `recommended_tp_zone: float`
- `recommended_sl_zone: float`
- `reject_risk_score: float`
- `final_payload_confidence: float`
- `notes_for_maffi: str`

## 14.2. Для чего нужен раздел

Позволяет твоим алгоритмам заранее сузить решение, но не забирает у Maffi право финального выбора.

---

# 15. Какие поля строго обязательны для минимально рабочего Maffi

Если резать до минимального MVP, то перед каждым пингом должны быть хотя бы:

- `ticker`
- `last_price`
- `vwap_5m`
- `local_high_5m`
- `local_low_5m`
- `atr_like_5m`
- `delta_5m`
- `imbalance_ratio_5m`
- `trend_strength_score`
- `market_regime.regime`
- `market_regime.confidence`
- `support_zone_low`
- `support_zone_high`
- `resistance_zone_low`
- `resistance_zone_high`
- хотя бы 1-3 `grid_candidates`
- `preferred_direction_hint`
- `direction_hint_confidence`
- `recommended_tp_zone`
- `recommended_sl_zone`

Но это **минимум**, а не желательный production-вход.

---

# 16. Рекомендуемые единицы измерения

Чтобы не было путаницы:

- цены — `float`, в абсолютной цене инструмента
- объёмы — `float`, в единицах инструмента
- коэффициенты / score — `0..100`, если это score
- confidence — `0..1`
- timestamp — ISO-8601 UTC
- процентили — `0..1` или `0..100`, но единообразно по всей схеме

Рекомендация:
- score → `0..100`
- confidence → `0..1`
- positional ratios → `0..1`

---

# 17. Правила для недостающих данных

Если какое-то поле временно недоступно:
- не скрывать это
- передавать `null`, если поле допустимо nullable
- поднимать `data_quality.status = degraded`
- обновлять `final_payload_confidence`

Если отсутствует критический блок:
- payload должен маркироваться как непригодный
- Maffi должен иметь право вернуть `rejected`

---

# 18. Рекомендуемый полный пример payload

```json
{
  "schema_version": "1.0",
  "generated_at_utc": "2026-03-24T00:00:00Z",
  "ticker": "BTCUSDC",
  "frame": "5m",
  "data_quality": {
    "status": "ok",
    "ticks_count_raw": 182340,
    "ticks_count_clean": 181902,
    "duplicate_ticks_removed": 311,
    "bad_ticks_removed": 127,
    "coverage_ratio": 0.997,
    "time_span_seconds": 3600,
    "largest_gap_seconds": 1.4,
    "outlier_ratio": 0.0012,
    "liquidity_quality_score": 88,
    "data_quality_score": 92
  },
  "market_snapshot": {
    "last_price": 84250.0,
    "last_trade_ts_utc": "2026-03-24T00:00:00Z",
    "mid_reference_price": 84240.0,
    "vwap_1m": 84210.0,
    "vwap_5m": 84190.0,
    "vwap_15m": 84080.0,
    "trade_count_1m": 460,
    "trade_count_5m": 2280,
    "trade_count_15m": 6740,
    "volume_1m": 31.2,
    "volume_5m": 142.8,
    "volume_15m": 436.5,
    "avg_trade_size_1m": 0.068,
    "avg_trade_size_5m": 0.062
  },
  "price_structure": {
    "open_1m": 84190.0,
    "high_1m": 84270.0,
    "low_1m": 84172.0,
    "close_1m": 84250.0,
    "open_5m": 84090.0,
    "high_5m": 84290.0,
    "low_5m": 84060.0,
    "close_5m": 84250.0,
    "open_15m": 83870.0,
    "high_15m": 84290.0,
    "low_15m": 83820.0,
    "close_15m": 84250.0,
    "local_high_5m": 84290.0,
    "local_low_5m": 84060.0,
    "local_high_15m": 84290.0,
    "local_low_15m": 83820.0,
    "range_width_1m": 98.0,
    "range_width_5m": 230.0,
    "range_width_15m": 470.0,
    "close_position_in_5m_range": 0.83,
    "close_position_in_15m_range": 0.91,
    "distance_to_5m_high": 40.0,
    "distance_to_5m_low": 190.0,
    "distance_to_15m_high": 40.0,
    "distance_to_15m_low": 430.0
  },
  "volatility": {
    "atr_like_30s": 28.0,
    "atr_like_1m": 55.0,
    "atr_like_5m": 180.0,
    "realized_vol_30s": 0.003,
    "realized_vol_1m": 0.006,
    "realized_vol_5m": 0.014,
    "return_std_30s": 0.0028,
    "return_std_1m": 0.0054,
    "return_std_5m": 0.0131,
    "volatility_percentile_1h": 0.67,
    "volatility_regime": "normal",
    "impulse_size_last_move": 140.0,
    "impulse_duration_seconds": 220.0,
    "volatility_stability_score": 72
  },
  "order_flow": {
    "buy_volume_30s": 11.8,
    "sell_volume_30s": 8.1,
    "buy_volume_1m": 19.5,
    "sell_volume_1m": 11.7,
    "buy_volume_5m": 87.6,
    "sell_volume_5m": 55.2,
    "delta_30s": 3.7,
    "delta_1m": 7.8,
    "delta_5m": 32.4,
    "cumulative_delta_5m": 49.1,
    "imbalance_ratio_30s": 1.46,
    "imbalance_ratio_1m": 1.67,
    "imbalance_ratio_5m": 1.58,
    "aggression_score_buy": 74,
    "aggression_score_sell": 39,
    "dominant_side": "buy",
    "order_flow_confidence": 0.79
  },
  "trend_structure": {
    "price_slope_30s": 0.41,
    "price_slope_1m": 0.62,
    "price_slope_5m": 0.71,
    "vwap_slope_1m": 0.52,
    "vwap_slope_5m": 0.66,
    "higher_highs_score": 77,
    "higher_lows_score": 74,
    "lower_highs_score": 18,
    "lower_lows_score": 12,
    "trend_strength_score": 76,
    "trend_persistence_score": 71,
    "mean_reversion_score": 32,
    "chop_score": 28,
    "noise_score": 24,
    "reversal_frequency_score": 29
  },
  "market_regime": {
    "regime": "trend_up",
    "confidence": 0.81,
    "trend_up_score": 82,
    "trend_down_score": 11,
    "range_score": 33,
    "chaos_score": 19,
    "regime_notes": "Positive pressure with controlled volatility and stable upward slope."
  },
  "support_resistance": {
    "support_zone_low": 83980.0,
    "support_zone_high": 84060.0,
    "resistance_zone_low": 84490.0,
    "resistance_zone_high": 84610.0,
    "nearest_support_distance": 190.0,
    "nearest_resistance_distance": 240.0,
    "boundary_reaction_score": 76,
    "bounce_frequency_score": 69,
    "wick_rejection_score_upper": 63,
    "wick_rejection_score_lower": 74,
    "level_respect_score": 72
  },
  "grid_candidates": {
    "candidate_count": 3,
    "candidates": [
      {
        "candidate_id": "A",
        "grid_lower_price": 84020.0,
        "grid_upper_price": 84580.0,
        "grid_width": 560.0,
        "grid_step": 51.0,
        "grid_count": 11,
        "range_utilization_score": 76,
        "oscillation_score": 68,
        "step_quality_score": 74,
        "stability_score": 71,
        "boundary_respect_score": 79,
        "grid_efficiency_score": 74,
        "candidate_notes": "Balanced active corridor"
      },
      {
        "candidate_id": "B",
        "grid_lower_price": 83990.0,
        "grid_upper_price": 84620.0,
        "grid_width": 630.0,
        "grid_step": 57.0,
        "grid_count": 11,
        "range_utilization_score": 72,
        "oscillation_score": 63,
        "step_quality_score": 70,
        "stability_score": 75,
        "boundary_respect_score": 77,
        "grid_efficiency_score": 72,
        "candidate_notes": "Wider safety corridor"
      },
      {
        "candidate_id": "C",
        "grid_lower_price": 84060.0,
        "grid_upper_price": 84510.0,
        "grid_width": 450.0,
        "grid_step": 41.0,
        "grid_count": 11,
        "range_utilization_score": 61,
        "oscillation_score": 71,
        "step_quality_score": 58,
        "stability_score": 62,
        "boundary_respect_score": 66,
        "grid_efficiency_score": 63,
        "candidate_notes": "Dense but slightly fragile"
      }
    ]
  },
  "decision_hints": {
    "preferred_direction_hint": "Long",
    "direction_hint_confidence": 0.79,
    "recommended_candidate_id": "A",
    "recommended_tp_zone": 84720.0,
    "recommended_sl_zone": 83880.0,
    "reject_risk_score": 18,
    "final_payload_confidence": 0.84,
    "notes_for_maffi": "Best candidate remains long-biased inside active uptrend corridor."
  }
}
```

---

# 19. Что Maffi будет делать с этим payload

На основе такого входа Maffi сможет:
1. понять, валидны ли данные
2. проверить режим рынка
3. сравнить grid candidates
4. принять Long/Short
5. выбрать лучший диапазон
6. определить grid_count
7. поставить TP
8. поставить SL
9. написать rationale
10. вернуть итоговый ответ по тикеру

---

# 20. Итог

Для качественного решения по сетке Maffi нужен **не поток сырых тиков в чат**, а **многоуровневый входной контракт признаков**.

Ключевые блоки, без которых качество резко падает:
- `data_quality`
- `price_structure`
- `volatility`
- `order_flow`
- `trend_structure`
- `market_regime`
- `support_resistance`
- `grid_candidates`
- `decision_hints`

Если этот контракт соблюдён, Maffi сможет стабильно выдавать финальные параметры grid setup по каждому пингу тикера.
