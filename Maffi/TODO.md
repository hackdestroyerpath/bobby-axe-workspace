# MAFFI — DETAILED TECH SPEC FOR IMPLEMENTATION

## Status
Рабочее ТЗ для кодинга на основе `Maffi/TODO.md`.

## Purpose
Этот документ превращает входной контракт для `Maffi` в практическую инструкцию по реализации кода.

Цель: чтобы ты мог писать систему не абстрактно, а поэтапно:
- какие модули создать;
- какие структуры данных ввести;
- какие проверки обязательны;
- какие признаки должны быть рассчитаны до вызова `Maffi`;
- как `Maffi` принимает финальное решение;
- что считается готовым MVP, а что production-ready версией.

---

# 1. SYSTEM ROLE OF MAFFI

## 1.1. What Maffi is
`Maffi` — это не тик-движок и не сырой аналитический пайплайн.

`Maffi` — это **decision engine for 5m grid setup**.

Он не должен:
- читать сырые тики напрямую из чата;
- принимать неструктурированные куски анализа;
- сам заново пересчитывать весь рынок с нуля;
- зависеть от свободного текста.

Он должен:
- получать **один строго структурированный payload на один тикер**;
- валидировать полноту и качество входа;
- оценивать пригодность рынка для grid-setup;
- выбирать направление: `Long`, `Short` или `Reject`;
- выбирать один grid candidate;
- рассчитывать финальные поля grid proposal;
- возвращать понятный и детерминированный результат.

---

# 2. TARGET OUTPUT OF MAFFI

## 2.1. Minimal output
Минимальный выход `Maffi`:

```json
{
  "ticker": "BTCUSDC",
  "frame": "5m",
  "decision": "Long",
  "grid_upper_price": 84580.0,
  "grid_lower_price": 84020.0,
  "grid_count": 11,
  "tp": 84720.0,
  "sl": 83880.0
}
```

## 2.2. Recommended full output
Рекомендуемый production-output:

```json
{
  "schema_version": "1.0",
  "generated_at_utc": "2026-03-24T00:00:00Z",
  "ticker": "BTCUSDC",
  "frame": "5m",
  "decision": "Long",
  "selected_candidate_id": "A",
  "grid_lower_price": 84020.0,
  "grid_upper_price": 84580.0,
  "grid_mid_price": 84300.0,
  "grid_width": 560.0,
  "grid_count": 11,
  "grid_step": 51.0,
  "tp": 84720.0,
  "sl": 83880.0,
  "efficiency_score": 74.0,
  "confidence": 0.81,
  "reject": false,
  "reject_reason": null,
  "rationale": "Long grid selected inside active upward corridor with positive order-flow and acceptable volatility.",
  "input_quality_status": "ok",
  "input_quality_score": 92.0,
  "market_regime": "trend_up"
}
```

---

# 3. HIGH-LEVEL ARCHITECTURE

## 3.1. Logical pipeline
Общий pipeline должен выглядеть так:

1. **tick ingestion / access layer**
2. **tick cleaning + normalization**
3. **feature aggregation layer**
4. **payload builder**
5. **payload validator**
6. **Maffi decision engine**
7. **result formatter**
8. **tests + fixtures + deterministic replay**

## 3.2. Separation of responsibilities

### External preprocessing layer
Этот слой отвечает за:
- чтение сырых тиков;
- очистку;
- агрегацию;
- расчёт признаков;
- подготовку `payload`.

### Maffi layer
Этот слой отвечает за:
- валидацию payload;
- decision logic;
- candidate selection;
- final grid output.

### Important rule
Не смешивать preprocessing и final decision в одном хаотичном модуле.

---

# 4. RECOMMENDED PROJECT STRUCTURE

```text
maffi/
  __init__.py
  schemas.py
  enums.py
  models.py
  validator.py
  scoring.py
  decision_engine.py
  candidate_selector.py
  tp_sl.py
  formatter.py
  errors.py
  utils.py

  preprocessing/
    __init__.py
    tick_cleaning.py
    aggregation.py
    volatility.py
    order_flow.py
    trend_structure.py
    regime.py
    support_resistance.py
    grid_candidates.py
    payload_builder.py

  tests/
    test_validator.py
    test_scoring.py
    test_decision_engine.py
    test_candidate_selector.py
    test_tp_sl.py
    test_payload_builder.py
    fixtures/
      payload_ok.json
      payload_degraded.json
      payload_bad.json
      payload_long.json
      payload_short.json
      payload_reject.json
```

---

# 5. IMPLEMENTATION PHASES

## PHASE 1 — SCHEMA, ENUMS, MODELS, VALIDATION

### Goal
Сначала зафиксировать стабильную структуру данных. Не начинать с decision logic.

## Step 1. Define enums and constants
Создать перечисления:
- `Frame`: `5m`
- `QualityStatus`: `ok`, `degraded`, `bad`
- `VolatilityRegime`: `low`, `normal`, `elevated`, `extreme`
- `DominantSide`: `buy`, `sell`, `neutral`
- `MarketRegime`: `trend_up`, `trend_down`, `range_balanced`, `chaotic_high_risk`
- `DirectionHint`: `Long`, `Short`, `Neutral`
- `Decision`: `Long`, `Short`, `Reject`

### Result
- единые enum-типы для всех модулей;
- устранение строкового хаоса.

## Step 2. Define data models
Создать typed-модели для всех секций payload:
- `DataQuality`
- `MarketSnapshot`
- `PriceStructure`
- `Volatility`
- `OrderFlow`
- `TrendStructure`
- `MarketRegimeBlock`
- `SupportResistance`
- `GridCandidate`
- `GridCandidatesBlock`
- `DecisionHints`
- `MaffiInputPayload`
- `MaffiOutput`

Лучше делать через `pydantic` или dataclasses + явная валидация.

### Result
- стабильный контракт в коде;
- машиночитаемая структура;
- база для тестов.

## Step 3. Build payload validator
Нужно реализовать валидацию трёх уровней:

### 3.1 Structural validation
Проверяет:
- все обязательные блоки присутствуют;
- типы корректны;
- обязательные поля не пустые;
- `ticker` и `frame` заданы.

### 3.2 Semantic validation
Проверяет:
- `grid_upper_price > grid_lower_price`;
- `grid_count >= 2`;
- `coverage_ratio` в диапазоне `0..1`;
- `confidence` в диапазоне `0..1`;
- score в диапазоне `0..100`;
- timestamp в ISO UTC;
- позиционные коэффициенты в `0..1`.

### 3.3 Cross-field validation
Проверяет:
- `ticks_count_clean <= ticks_count_raw`;
- `buy_volume + sell_volume` логически не конфликтуют с `volume_*`;
- `local_high >= local_low`;
- `distance_to_high/low >= 0`;
- `candidate_count == len(candidates)`;
- `recommended_candidate_id` существует в списке candidates, если payload не degraded до критического состояния.

### Result
- жёсткий фильтр кривых входов.

## Step 4. Define validation result model
Сделать отдельный объект результата валидации:

```python
ValidationResult(
    is_valid: bool,
    severity: str,
    errors: list[str],
    warnings: list[str],
    normalized_payload: MaffiInputPayload | None,
)
```

### Result
- `Maffi` не работает напрямую с сырым JSON.

---

## PHASE 2 — PREPROCESSING / FEATURE BUILDING LAYER

### Goal
Построить слой, который из тиков делает правильный payload для Maffi.

## Step 5. Build tick cleaning module
Модуль `tick_cleaning.py` должен:
- удалять дубли;
- удалять явно битые тики;
- сортировать поток по времени;
- считать статистику очистки;
- возвращать clean ticks + cleaning report.

### Output
- `ticks_count_raw`
- `ticks_count_clean`
- `duplicate_ticks_removed`
- `bad_ticks_removed`
- `largest_gap_seconds`
- `outlier_ratio`

## Step 6. Build aggregation module
Модуль `aggregation.py` должен строить:
- 1m OHLC
- 5m OHLC
- 15m OHLC
- count/volume stats
- средние размеры сделок
- локальные high/low

### Important
Все окна и формулы должны быть детерминированными и воспроизводимыми.

## Step 7. Build volatility module
Модуль `volatility.py` должен считать:
- `atr_like_30s`
- `atr_like_1m`
- `atr_like_5m`
- `realized_vol_*`
- `return_std_*`
- `volatility_percentile_1h`
- `volatility_regime`
- `impulse_size_last_move`
- `impulse_duration_seconds`
- `volatility_stability_score`

### Important
Нужно заранее унифицировать:
- что именно значит `atr_like`;
- на каком окне считается volatility percentile;
- как определяется `extreme volatility`.

## Step 8. Build order-flow module
Модуль `order_flow.py` должен считать:
- buy/sell volume for `30s`, `1m`, `5m`
- `delta_*`
- `cumulative_delta_5m`
- `imbalance_ratio_*`
- `aggression_score_buy`
- `aggression_score_sell`
- `dominant_side`
- `order_flow_confidence`

### Important
До кода утвердить:
- как определяется buy/sell side;
- формулу imbalance ratio;
- формулу aggression score.

## Step 9. Build trend structure module
Модуль `trend_structure.py` должен считать:
- price slopes
- VWAP slopes
- higher-highs / higher-lows scores
- lower-highs / lower-lows scores
- `trend_strength_score`
- `trend_persistence_score`
- `mean_reversion_score`
- `chop_score`
- `noise_score`
- `reversal_frequency_score`

## Step 10. Build market regime classifier
Модуль `regime.py` должен классифицировать рынок в одно из:
- `trend_up`
- `trend_down`
- `range_balanced`
- `chaotic_high_risk`

### Important
Нужен не black box, а explainable scoring.

Рекомендуемая логика:
- score each regime separately;
- choose dominant regime;
- attach `regime_notes`.

## Step 11. Build support/resistance module
Модуль `support_resistance.py` должен считать:
- support/resistance zones;
- distances to nearest zones;
- boundary reaction metrics;
- wick rejection metrics;
- level respect score.

### Important
Нужно заранее определить:
- как строятся зоны;
- фиксированная ширина или адаптивная;
- как считается reaction score;
- как считается level respect.

## Step 12. Build grid candidates generator
Модуль `grid_candidates.py` должен:
- генерировать 1–N кандидатов сетки;
- ранжировать их;
- считать score каждого кандидата;
- не возвращать одну “магическую” сетку.

### Each candidate must include
- `candidate_id`
- `grid_lower_price`
- `grid_upper_price`
- `grid_width`
- `grid_step`
- `grid_count`
- `range_utilization_score`
- `oscillation_score`
- `step_quality_score`
- `stability_score`
- `boundary_respect_score`
- `grid_efficiency_score`
- `candidate_notes`

## Step 13. Build payload builder
`payload_builder.py` должен собрать итоговый `MaffiInputPayload` из всех модулей.

### Important
Builder должен:
- валидировать консистентность блоков;
- уметь строить degraded payload;
- явно маркировать критические отсутствия данных.

---

## PHASE 3 — DECISION ENGINE OF MAFFI

### Goal
Теперь на базе уже нормального payload построить decision engine.

## Step 14. Define rejection rules first
До выбора Long/Short сначала описать reject policy.

### Reject conditions should include
- `data_quality.status == bad`
- слишком низкий `data_quality_score`
- слишком низкий `coverage_ratio`
- слишком высокий `largest_gap_seconds`
- `market_regime == chaotic_high_risk` при высоком `chaos_score`
- нет валидных `grid_candidates`
- противоречивый сигнал: direction hint высокий, но order-flow/trend/volatility это не подтверждают

### Output
Если reject:
- `decision = Reject`
- `reject = true`
- заполненный `reject_reason`

## Step 15. Build direction scoring engine
Создать `scoring.py`, где рассчитываются отдельно:
- `long_score`
- `short_score`
- `reject_score`

### Recommended inputs
Для `long_score` использовать:
- positive order flow
- bullish trend structure
- price location in range
- market regime `trend_up`
- candidate quality
- acceptable volatility

Для `short_score` симметрично:
- selling pressure
- bearish trend shape
- market regime `trend_down`
- candidate quality
- acceptable volatility

### Important
Не делать выбор на одном поле. Нужен weighted composite score.

## Step 16. Add confidence policy
После direction scoring ввести confidence policy:
- base confidence from regime + order flow + trend alignment;
- downgrade by degraded data quality;
- downgrade by unstable volatility;
- downgrade by weak candidate quality;
- downgrade by contradictory hints.

## Step 17. Build candidate selector
`candidate_selector.py` должен:
- фильтровать непригодные candidates;
- выбирать лучший candidate с учётом выбранного направления;
- учитывать `recommended_candidate_id`, но не слепо;
- уметь объяснить, почему выбран именно этот candidate.

### Candidate rejection examples
- width too narrow;
- width too wide;
- poor boundary respect;
- unstable oscillation score;
- слишком плохой efficiency score.

## Step 18. Build TP/SL policy
`tp_sl.py` должен выбирать:
- `tp`
- `sl`

### Inputs
- selected candidate;
- direction;
- support/resistance;
- volatility;
- market regime;
- recommended hint zones.

### Important
Правила должны быть детерминированными:
- `Long`: TP выше upper boundary, SL ниже lower boundary;
- `Short`: TP ниже lower boundary, SL выше upper boundary;
- буферы должны зависеть от volatility, а не быть всегда фиксированными.

## Step 19. Build final decision engine
`decision_engine.py` должен объединить:
- validation result;
- reject policy;
- direction scores;
- selected candidate;
- TP/SL policy;
- rationale builder.

### Final output rules
Если `Reject`:
- candidate may be null;
- TP/SL optional or null;
- rationale обязательно.

Если `Long/Short`:
- candidate обязателен;
- `grid_lower_price < grid_upper_price`;
- `grid_count >= 2`;
- TP/SL обязаны быть логически согласованы с direction.

---

## PHASE 4 — FORMATTERS, EXPLAINABILITY, STABILITY

### Goal
Сделать результат пригодным для интеграции и отладки.

## Step 20. Build rationale generator
`formatter.py` должен собирать human-readable rationale:
- почему выбран Long/Short;
- почему выбран candidate;
- как data quality повлияла на confidence;
- какие риски есть.

### Example rationale
- “Long selected because order-flow buy pressure and positive 5m trend are aligned; candidate A offers best balance between width, boundary respect, and efficiency under normal volatility.”

## Step 21. Add machine-readable decision trace
Рекомендуется возвращать дополнительный блок:

```json
{
  "decision_trace": {
    "long_score": 78.2,
    "short_score": 24.1,
    "reject_score": 12.0,
    "selected_candidate_id": "A",
    "confidence_adjustments": [
      "-0.05 due to elevated volatility",
      "+0.07 due to strong order_flow alignment"
    ]
  }
}
```

Это очень поможет при дебаге.

## Step 22. Add deterministic replay support
Нужно уметь:
- сохранить payload в файл;
- повторно прогнать решение на том же payload;
- получить тот же результат.

Это критично для анализа спорных случаев.

---

## PHASE 5 — TESTING

### Goal
Без тестов этот контур будет выглядеть умным, но будет нестабилен.

## Step 23. Unit tests for validation
Проверить:
- корректный payload проходит;
- отсутствующий обязательный блок валится;
- неверные диапазоны (`confidence > 1`) валятся;
- candidate_count mismatch ловится.

## Step 24. Unit tests for scoring
Проверить:
- bullish payload даёт higher `long_score`;
- bearish payload даёт higher `short_score`;
- chaotic payload поднимает `reject_score`.

## Step 25. Unit tests for candidate selection
Проверить:
- лучший candidate выбирается корректно;
- invalid candidate отбрасывается;
- `recommended_candidate_id` учитывается, но не доминирует при плохом качестве.

## Step 26. Unit tests for TP/SL logic
Проверить:
- `Long`: `tp > upper`, `sl < lower`;
- `Short`: `tp < lower`, `sl > upper`;
- buffers scale with volatility.

## Step 27. End-to-end tests
Нужны как минимум сценарии:
- `good long`
- `good short`
- `reject due to bad data`
- `reject due to chaotic regime`
- `degraded but usable`

---

# 6. MVP VS PRODUCTION

## 6.1. MVP
Для MVP достаточно реализовать:
- схемы;
- валидатор;
- базовый payload builder;
- базовую direction logic;
- candidate selector;
- TP/SL;
- итоговый output.

### Minimal required fields for MVP
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
- `grid_candidates`
- `preferred_direction_hint`
- `direction_hint_confidence`
- `recommended_tp_zone`
- `recommended_sl_zone`

## 6.2. Production-ready
Production-ready значит дополнительно есть:
- explainable scoring;
- degraded payload handling;
- deterministic replay;
- full tests;
- decision trace;
- stable field semantics;
- documented formulas.

---

# 7. CRITICAL CODING RULES

## Rule 1
Не кодить Long/Short decision раньше схемы и валидатора.

## Rule 2
Не позволять свободным словарям гулять по коду без typed-models.

## Rule 3
Не смешивать payload building и final decision logic.

## Rule 4
Все score должны иметь единый масштаб.

## Rule 5
Все confidence должны быть в `0..1`.

## Rule 6
Все timestamps только UTC ISO-8601.

## Rule 7
Все reject cases должны быть явными и объяснимыми.

## Rule 8
Нельзя выбирать candidate “из воздуха” — только из списка candidates.

## Rule 9
Любой degraded input должен явно понижать confidence.

## Rule 10
Любое финальное решение должно быть воспроизводимым на том же payload.

---

# 8. RECOMMENDED ORDER OF CODING

1. `enums.py`
2. `models.py` / `schemas.py`
3. `validator.py`
4. `preprocessing/payload_builder.py`
5. `preprocessing/volatility.py`
6. `preprocessing/order_flow.py`
7. `preprocessing/trend_structure.py`
8. `preprocessing/regime.py`
9. `preprocessing/support_resistance.py`
10. `preprocessing/grid_candidates.py`
11. `scoring.py`
12. `candidate_selector.py`
13. `tp_sl.py`
14. `decision_engine.py`
15. `formatter.py`
16. tests

---

# 9. DEFINITION OF DONE

`Maffi` implementation can be considered ready only if all below are true:

- есть формальная typed-schema для входа и выхода;
- есть validator с structural + semantic + cross-field checks;
- preprocessing layer собирает payload детерминированно;
- payload builder умеет собирать как `ok`, так и `degraded` input;
- Maffi умеет вернуть `Long`, `Short` или `Reject`;
- выбор direction делается через composite scoring, а не через одно поле;
- candidate selection работает только по переданному списку candidates;
- TP/SL согласованы с direction и candidate;
- output содержит rationale;
- output воспроизводим на одном и том же payload;
- есть unit tests на validator, scoring, candidate selection и TP/SL;
- есть end-to-end tests минимум на 5 сценариев.

---

# 10. PRACTICAL NEXT MOVE

Если начинать прямо сейчас, лучший старт такой:

## First coding sprint
1. сделать `enums.py`
2. сделать `models.py`
3. сделать `validator.py`
4. зафиксировать один пример `payload_ok.json`
5. написать первый `decision_engine.py` без сложной магии, но уже с `Reject/Long/Short`

## Second sprint
1. добавить scoring
2. добавить candidate selector
3. добавить TP/SL policy
4. добавить rationale

## Third sprint
1. довести preprocessing modules
2. добавить degraded handling
3. добавить полный test suite
4. сделать replay/debug trace

---

# 11. FINAL MANAGEMENT NOTE

Правильный подход для `Maffi` — это не “написать умный промпт”, а построить:
- жёсткий входной контракт;
- прозрачный scoring;
- детерминированный decision engine;
- воспроизводимый output.

Если хочешь сильную реализацию, код должен быть построен как **contract-driven decision system**, а не как куча эвристик в одном файле.
