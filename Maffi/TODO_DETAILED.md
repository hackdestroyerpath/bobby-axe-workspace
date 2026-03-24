# TODO_DETAILED

Статус: локальный детальный TODO-документ.
Дата: 2026-03-24

---

# MAFFI — Detailed plan

Ниже детально расписаны первые 4 шага завершения Maffi.

---

# Шаг 1. Дожать core decision logic до реально торгуемой сетки

## Цель
Сделать так, чтобы Maffi не просто принимал payload и выбирал сторону, а стабильно выдавал торгуемое grid-решение:
- `direction`
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `grid_step`
- `tp`
- `sl`
- `confidence`
- `rationale`
- `decision_trace`

## Подзадачи

### 1.1. Свести contract и runtime в одну каноническую модель
Что сделать:
- сверить `CONTRACT_V1.md`
- сверить `contract_v1.json`
- сверить runtime dataclass / output model
- сверить examples
- убрать расхождения по обязательным и optional полям

Что должно быть на выходе:
- единый набор required полей
- единый набор optional полей
- единый shape для `validation_summary`
- единый shape для `decision_summary`
- единый shape для `decision_trace`

### 1.2. Дожать decision gate
Что сделать:
- формально описать, когда payload идёт в `Long`
- формально описать, когда payload идёт в `Short`
- формально описать, когда payload идёт в `Reject`
- выделить reject policy отдельно от direction logic

Что проверить:
- `input_quality_status`
- `reject_score`
- `confidence_hint`
- конфликт сигналов `long_score vs short_score`
- отсутствие годных grid candidates

### 1.3. Выделить direction resolver
Что сделать:
- собрать отдельный блок выбора направления
- использовать:
  - `long_score`
  - `short_score`
  - `market_regime`
  - `dominant_side`
  - `confidence_hint`
- описать conflict resolution, если сигналы спорят друг с другом

Что должно быть на выходе:
- `direction`
- reason выбора
- trace по directional logic

### 1.4. Выделить range resolver
Что сделать:
- отдельно рассчитывать:
  - `grid_lower_price`
  - `grid_upper_price`
- использовать:
  - `support_level`
  - `resistance_level`
  - `last_price`
  - market regime
  - future candidate scoring hooks

Что проверить:
- диапазон не инвертирован
- диапазон не слишком узкий
- диапазон не слишком широкий
- диапазон логичен относительно market structure

### 1.5. Выделить grid density resolver
Что сделать:
- отдельно рассчитывать:
  - `grid_count`
  - `grid_step`
- не держать это как побочный результат одной формулы

На что опираться:
- width диапазона
- ATR
- directional context
- future efficiency scoring

### 1.6. Дожать candidate scoring
Что сделать:
- рассчитывать несколько grid-кандидатов
- каждому кандидату считать:
  - `efficiency_score`
  - `grid_count`
  - `grid_step`
  - `candidate_notes`
- ранжировать кандидаты детерминированно

Подскоринги:
- range utilization
- oscillation quality
- step quality
- stability
- boundary respect

### 1.7. Формализовать TP/SL logic
Что сделать:
- вынести TP/SL policy в отдельную понятную логику
- не держать её только как ATR-эвристику

Для Long:
- TP в зоне завершения движения / сопротивления
- SL за support / structural invalidation

Для Short:
- TP в зоне поддержки / downside target
- SL за resistance / invalidation

### 1.8. Собрать полный decision trace
Что сделать:
- trace должен отражать этапы:
  1. gate
  2. direction
  3. range
  4. grid_count
  5. tp_sl
  6. confidence

Что должно быть в trace:
- status
- reason
- inputs
- outputs
- metrics
- warnings

### 1.9. Acceptance по шагу 1
Нужно прогнать сценарии:
- healthy long
- healthy short
- balanced range
- reject by bad quality
- reject by efficiency low
- degraded but usable
- malformed payload

## Definition of Done шага 1
Шаг 1 считается закрытым, если:
- decision engine выбирает не только сторону, но и геометрию сетки;
- grid candidate scoring стабилен;
- TP/SL воспроизводимы;
- trace детерминирован;
- выход соответствует contract v1.

---

# Шаг 2. Дожать preprocessing и feature hardening

## Цель
Сделать preprocessing устойчивым к реальным проблемам тикового потока и гарантировать стабильный feature layer для decision engine.

## Подзадачи

### 2.1. Harden sanitize/clean pipeline
Что сделать:
- дедупликация
- сортировка
- отсев битых тиков
- защита от отрицательных/нулевых цен
- защита от кривых volume значений

### 2.2. Дожать работу на sparse input
Что сделать:
- корректно обрабатывать редкие тики
- не падать на малом числе точек
- прогнозируемо отдавать degrade

### 2.3. Дожать работу на noisy input
Что сделать:
- фильтровать шумовые выбросы
- не ломать trend/range classification из-за одиночных аномалий
- учитывать outlier sensitivity

### 2.4. Дожать обработку gaps
Что сделать:
- фиксировать временные дыры
- считать их в degradation logic
- отражать в trace и summary

### 2.5. Усилить OHLCV extraction
Что сделать:
- стабильно строить свечи `1m`, `5m`, `15m`
- проверять границы бакетов
- проверить deterministic behavior на одинаковых входах

### 2.6. Усилить feature extraction
Должны стабильно считаться:
- realized volatility
- range width
- buy/sell split
- imbalance
- trend structure
- support/resistance
- market regime hints
- volatility regime hints
- entry candidates

### 2.7. Добавить degradation trace
Что сделать:
- явно писать, что ухудшило payload quality
- собирать причины degradation в machine-readable виде

## Definition of Done шага 2
Шаг 2 считается закрытым, если:
- preprocessing стабилен на healthy/degraded/noisy/sparse/gapped input;
- feature layer не падает и даёт предсказуемый результат;
- degradation trace присутствует и объясним.

---

# Шаг 3. Дожать formatter, contract output и traceability

## Цель
Сделать финальный output Maffi полностью стабильным, пригодным для orchestration parsing и удобным для downstream handoff.

## Подзадачи

### 3.1. Зафиксировать финальный output shape
Что сделать:
- убедиться, что output строго соответствует `contract v1`
- проверить required/optional поля
- проверить shape на `long / short / reject`

### 3.2. Дожать formatter
Что сделать:
- сериализация должна быть deterministic
- порядок top-level ключей должен быть стабилен
- enum значения должны быть нормализованы
- trace должен быть JSON-friendly

### 3.3. Дожать `validation_summary`
Что сделать:
- counts
- errors
- warnings
- degrade block
- top reasons

### 3.4. Дожать `decision_summary`
Что сделать:
- `direction`
- `selected_candidate_id`
- `tp_sl_logic_digest`
- короткая explainability-выжимка

### 3.5. Дожать `decision_trace`
Что сделать:
- шаги должны быть ordered
- у каждого шага должен быть status/reason
- trace должен быть пригоден для audit и replay

### 3.6. Snapshot checks
Что сделать:
- завести стабильные fixture outputs
- сверять shape и ключевые значения

## Definition of Done шага 3
Шаг 3 считается закрытым, если:
- финальный output стабилен;
- long/short/reject shape соответствует contract v1;
- formatter выдаёт deterministic output;
- trace пригоден для audit downstream.

---

# Шаг 4. Дожать acceptance/regression coverage

## Цель
Собрать проверочный контур, который не даст Maffi деградировать при дальнейших изменениях.

## Подзадачи

### 4.1. Закрыть acceptance matrix тестами
Нужно автоматизировать:
- healthy long trend
- healthy short trend
- balanced range
- chaotic reject
- degraded but usable
- bad input hard reject
- conflicting signal set
- weak confidence reject
- malformed payload
- bridge e2e

### 4.2. Добавить deterministic replay coverage
Что сделать:
- многократный прогон одинакового payload
- проверка identical output
- проверка identical decision trace

### 4.3. Добавить regression fixtures
Что сделать:
- canonical payloads
- canonical outputs
- validator fixtures
- grid scoring fixtures

### 4.4. Добавить edge-case coverage
Что сделать:
- инвертированные уровни
- пустые candidates
- ATR near zero
- near-equal long/short scores
- degraded + high reject score
- conflicting market regime and dominant side

### 4.5. Проверить bridge e2e
Что сделать:
- Ben_Kim symbol object -> payload -> Maffi decision
- batch bridge
- partial/degraded status handling

## Definition of Done шага 4
Шаг 4 считается закрытым, если:
- acceptance matrix автоматизирована;
- regression suite зелёная;
- deterministic replay подтверждён;
- bridge e2e проходит без ручного вмешательства.

---

# Следующие шаги

## Шаг 5. Собрать live orchestration bridge и runtime entrypoint

## Шаг 6. Провести final hardening и подготовить production-ready release
