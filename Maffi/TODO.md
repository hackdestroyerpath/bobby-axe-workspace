# MAFFI TODO

## Черновой финальный ТЗ-документ
**Проект:** Maffi — генератор оптимальной 5m grid setup по сырым тикам
**Репозиторий:** `hackdestroyerpath/bobby-axe-workspace`
**Статус:** final draft / рабочий черновик для старта реализации
**Цель:** дать чёткое ТЗ на первую фазу реализации и зафиксировать весь дальнейший pipeline

---

# 1. Задача

Нужно построить систему, которая на вход получает **сырые тики по одному тикеру** из хранилища Jack и на выходе возвращает **готовое решение для торговой сетки на таймфрейме 5m**.

Система **не занимается капиталом, размером позиции и аллокацией денег**.

Система обязана определить:
- тикер
- направление сетки: `Long` или `Short`
- верхнюю границу диапазона
- нижнюю границу диапазона
- середину диапазона
- количество сеток
- тейк-профит
- стоп-лосс
- confidence
- краткое текстовое rationale

Если рынок не подходит для качественной сетки, система **не должна выдумывать ответ**. Она должна вернуть `rejected` с причиной.

---

# 2. Главный принцип

Нужен не один «алгоритм сетки», а полный pipeline:

`raw ticks -> normalized ticks -> microstructure features -> market regime -> grid constructor -> validation gate -> final 5m grid proposal`

---

# 3. Входные данные

## 3.1. Минимальный обязательный контракт входа

На вход по тикеру должен приходить поток сырых тиков со следующими полями:

- `ticker: str`
- `ts_utc: datetime`
- `price: float`
- `qty: float`
- `side: str` (`buy` | `sell`)
- `trade_id: str | int` — уникальный идентификатор тика для дедупликации

## 3.2. Желательные дополнительные поля

Если возможно, добавить:

- `is_buyer_maker: bool`
- `notional: float`
- `exchange: str`
- `mark_price: float`
- `index_price: float`

Эти поля не обязательны для Phase 1, но полезны для Phase 2+.

---

# 4. Основные требования к качеству входа

Перед расчётом сетки система обязана проверить:

1. Тики отсортированы по времени.
2. Нет критической доли дублей.
3. Нет поломанных timestamp.
4. Нет невозможных ценовых выбросов.
5. Есть минимально достаточная история.
6. Текущий поток ликвиден enough для 5m-grid.

Если хотя бы одно из условий не выполняется — возвращаем reject.

---

# 5. Что система должна анализировать

Из одних тиков нужно построить полезные признаки.

## 5.1. Цена
- open/high/low/close на 1s
- open/high/low/close на 1m
- open/high/low/close на 5m
- локальные high/low
- текущая позиция цены внутри диапазона
- скорость смещения цены
- slope цены

## 5.2. Объём
- total volume
- buy volume
- sell volume
- volume per second
- trade count
- average trade size

## 5.3. Order-flow / tape logic
- delta = buy_volume - sell_volume
- cumulative delta
- buy/sell imbalance
- acceleration of delta
- persistence of directional pressure

## 5.4. Волатильность
- realized volatility
- rolling std of returns
- true range
- ATR-like short volatility
- percentile of current volatility vs recent history

## 5.5. Структура рынка
- chop/noise score
- trend score
- range score
- wick density
- reversal frequency
- bounce frequency from local zones
- distance to local support/resistance
- distance to VWAP

---

# 6. Рыночные режимы

Перед построением сетки тикер должен быть классифицирован в один из режимов:

- `trend_up`
- `trend_down`
- `range_balanced`
- `chaotic_high_risk`

## 6.1. Интерпретация режимов

### `trend_up`
Сильный восходящий импульс, положительная дельта, цена держится выше опорной средней, шум умеренный.

### `trend_down`
Сильный нисходящий импульс, отрицательная дельта, цена держится ниже опорной средней, шум умеренный.

### `range_balanced`
Цена ходит в коридоре, направление не доминирует, есть возвраты в среднюю, рынок подходит для аккуратной grid-логики.

### `chaotic_high_risk`
Слишком много шума, резкие выбросы, плохая структура, направление нестабильно. Для Phase 1 такой режим лучше reject.

---

# 7. Правила принятия направления

## 7.1. Long
Выбирается, если:
- режим `trend_up`
- либо `range_balanced`, но текущая цена ближе к нижней части диапазона и есть признаки отскока вверх

## 7.2. Short
Выбирается, если:
- режим `trend_down`
- либо `range_balanced`, но текущая цена ближе к верхней части диапазона и есть признаки отскока вниз

## 7.3. Reject
Выбирается, если:
- режим `chaotic_high_risk`
- низкая ликвидность
- недостаточно данных
- confidence ниже порога
- диапазон невозможно построить адекватно

---

# 8. Правила построения диапазона сетки

## 8.1. Для Long-сетки
- `grid_lower_price` = зона поддержки / локальный минимум / lower band
- `grid_upper_price` = зона вероятного возврата / локальное сопротивление / upper band

## 8.2. Для Short-сетки
- `grid_upper_price` = зона сопротивления / локальный максимум / upper band
- `grid_lower_price` = зона потенциального снижения / локальная поддержка / lower target zone

## 8.3. Источники диапазона
При расчёте диапазона использовать комбинацию:
- локальные экстремумы
- VWAP bands
- ATR bands
- high/low последних N минут
- microstructure support/resistance zones

## 8.4. Ограничения диапазона
Диапазон не должен быть:
- слишком узким (комиссии/шум убьют прибыль)
- слишком широким (сетка будет слишком тупой и медленной)

---

# 9. Правила расчёта количества сеток

## 9.1. Общий принцип
Количество сеток зависит от:
- ширины диапазона
- текущей волатильности
- ликвидности
- минимального meaningful step

## 9.2. Базовая логика

1. Считаем ширину диапазона:
   - `width = abs(grid_upper_price - grid_lower_price)`
2. Считаем рекомендованный шаг:
   - `grid_step = k * short_term_volatility`
3. Считаем число сеток:
   - `grid_count = floor(width / grid_step)`

## 9.3. Ограничения
На первой фазе зажать в безопасные рамки:
- `min_grid_count = 5`
- `max_grid_count = 25`

Если расчёт даёт меньше минимума или больше максимума — нормализовать до границ или reject, если конфигурация становится бессмысленной.

---

# 10. Правила расчёта mid / TP / SL

## 10.1. Mid

Обязательное поле:
- `grid_mid_price`

На Phase 1 можно брать простую середину:
- `grid_mid_price = (grid_upper_price + grid_lower_price) / 2`

Дополнительно можно считать:
- `reference_price = current_close` или `vwap`

## 10.2. Take Profit

TP должен ставиться в зоне, где идея логично заканчивается:
- Long: у верхнего возвратного таргета / чуть ниже сильного сопротивления
- Short: у нижнего возвратного таргета / чуть выше сильной поддержки

На Phase 1 можно использовать:
- target-zone на основе диапазона и short-term ATR

## 10.3. Stop Loss

SL ставится там, где идея сетки ломается:
- Long: ниже зоны поддержки + volatility buffer
- Short: выше зоны сопротивления + volatility buffer

На Phase 1 использовать формулу:
- `sl_buffer = c * atr_short`

---

# 11. Reject-логика

Если хотя бы один из пунктов выполняется — вернуть reject:

- недостаточно истории
- тиков слишком мало
- рыночная структура хаотична
- волатильность экстремальна
- ликвидность недостаточна
- confidence ниже порога
- диапазон получается нефункциональным
- direction не удаётся определить уверенно

Формат reject должен быть формальным и машинно-читаемым.

---

# 12. Выходной контракт

## 12.1. Успешный результат

```json
{
  "ticker": "BTCUSDC",
  "frame": "5m",
  "status": "ready",
  "direction": "Long",
  "grid_upper_price": 86500.0,
  "grid_lower_price": 84200.0,
  "grid_mid_price": 85350.0,
  "grid_count": 12,
  "tp": 86950.0,
  "sl": 83680.0,
  "confidence": 0.78,
  "market_regime": "trend_up",
  "rationale": "Positive delta, controlled volatility, local support held, recovery corridor favors Long grid."
}
```

## 12.2. Reject-результат

```json
{
  "ticker": "XYZUSDC",
  "frame": "5m",
  "status": "rejected",
  "reason": "Chaotic tape, unstable volatility, and insufficient structure for a reliable 5m grid."
}
```

---

# 13. Архитектура по фазам

## Phase 1 — foundation / minimum tradable pipeline
**Это фаза, которую нужно делать сейчас.**

## Phase 2 — regime hardening / reject hardening
Усиление качества определения тренда/рейнджа/хаоса и стабильности reject-логики.

## Phase 3 — adaptive tuning by ticker
Адаптивные пороги по тикерам, калибровка для BTC / ETH / midcap / low-liquidity names.

## Phase 4 — backtest / replay / scoring
Прогон на исторических данных, проверка устойчивости и регрессии.

## Phase 5 — production handoff / orchestration contract
Жёсткая интеграция с Jack / Bobby Axe / хранилищем / run-scoped contract.

---

# 14. Сколько фаз осталось

После текущей стартовой работы остаётся:
- **Phase 2**
- **Phase 3**
- **Phase 4**
- **Phase 5**

Итого после первой реализации останется **4 следующие фазы**.

---

# 15. Подробная спецификация только для Phase 1

## 15.1. Цель Phase 1

Собрать рабочий минимальный pipeline, который:
- читает сырые тики по тикеру
- чистит их
- агрегирует в короткие бары
- считает базовые признаки
- определяет направление
- строит диапазон и количество сеток
- отдаёт готовый 5m grid proposal или reject

Это должна быть **первая версия, которую уже можно гонять на реальных данных**.

---

## 15.2. Что именно должно войти в Phase 1

### A. Tick Reader
Нужен модуль чтения данных из хранилища Jack.

#### Должен уметь:
- взять тикер
- взять окно истории
- выгрузить тики за нужный период
- вернуть данные в стабильном формате

#### Вход Tick Reader:
- `ticker`
- `from_ts`
- `to_ts`

#### Выход Tick Reader:
массив тиков стандартизированного формата

---

### B. Tick Normalizer
Нужен модуль очистки и нормализации.

#### Должен делать:
- сортировку по времени
- дедупликацию по `trade_id`
- удаление пустых / битых записей
- фильтр аномальных тиков
- проверку монотонности timestamp

#### Должен возвращать:
- нормализованный массив тиков
- отчёт по качеству данных

---

### C. Tick -> 1s Aggregator
Нужен модуль, который преобразует поток тиков в 1-second bars.

#### Для каждой секунды посчитать:
- `open`
- `high`
- `low`
- `close`
- `buy_volume`
- `sell_volume`
- `total_volume`
- `trade_count`
- `delta`
- `vwap`

Это базовый фундамент для всех следующих вычислений.

---

### D. Rolling Features Engine
Поверх 1s структуры посчитать rolling features.

#### Минимальный набор features для Phase 1:
- rolling return
- realized volatility short
- atr-like short range
- vwap distance
- delta rolling
- cumulative delta
- trend slope
- range width
- current close location in local range
- trade activity intensity

#### Окна:
Минимум использовать:
- 30s
- 60s
- 300s

---

### E. Market Regime Classifier V1
На Phase 1 это может быть score-based rule engine, не ML.

#### Нужно считать score:
- `trend_up_score`
- `trend_down_score`
- `range_score`
- `chaos_score`

#### Примерная логика:
- если slope вверх, cumulative delta положительная, цена выше VWAP, вола контролируема -> `trend_up`
- если slope вниз, cumulative delta отрицательная, цена ниже VWAP, вола контролируема -> `trend_down`
- если диапазон устойчив, частые возвраты в середину, directional pressure слабый -> `range_balanced`
- если вола слишком рваная, много выбросов, direction unstable -> `chaotic_high_risk`

#### Выход:
- `market_regime`
- `confidence`
- `direction_candidate`

---

### F. Grid Constructor V1
На базе режима строится сетка.

#### Для Long:
- найти support zone
- найти upper recovery zone
- задать lower/upper
- задать grid_count
- задать TP
- задать SL

#### Для Short:
- найти resistance zone
- найти downside target zone
- задать upper/lower
- задать grid_count
- задать TP
- задать SL

---

### G. Validation Gate
Перед возвратом результата проверить:
- `grid_upper_price > grid_lower_price`
- `grid_count >= min_grid_count`
- `grid_count <= max_grid_count`
- `tp` находится по логике идеи
- `sl` находится по логике слома идеи
- confidence >= threshold
- режим не хаотичный

Если проверка не проходит — reject.

---

### H. Explanation Layer
Нужен отдельный генератор краткого rationale.

#### Формат rationale:
1. какая структура рынка увидена
2. почему выбран Long / Short
3. почему диапазон именно такой
4. почему сеток столько
5. где логика TP / SL

Коротко. Без воды. Человек должен за 1 абзац понять решение.

---

# 16. Что писать в коде на Phase 1

Ниже рекомендованная структура модулей.

```text
maffi/
  tick_reader.py
  tick_normalizer.py
  tick_aggregator.py
  features.py
  regime_classifier.py
  grid_builder.py
  validator.py
  rationale.py
  contracts.py
  runner.py
```

## 16.1. `tick_reader.py`
Код чтения тиков из Jack storage.

## 16.2. `tick_normalizer.py`
Код очистки, дедупликации и sanity checks.

## 16.3. `tick_aggregator.py`
Код перевода raw ticks в 1s bars.

## 16.4. `features.py`
Код расчёта признаков и rolling metrics.

## 16.5. `regime_classifier.py`
Код score-based определения режима рынка.

## 16.6. `grid_builder.py`
Код построения grid range, direction, grid_count, TP, SL.

## 16.7. `validator.py`
Код reject-логики и финальной валидации.

## 16.8. `rationale.py`
Код генерации краткого объяснения.

## 16.9. `contracts.py`
Pydantic/dataclass-схемы входа и выхода.

## 16.10. `runner.py`
Главная orchestration-функция по тикеру:
- load
- normalize
- aggregate
- feature build
- classify
- build grid
- validate
- output

---

# 17. Минимальные контракты Python-уровня

## 17.1. TickInput
```python
class TickInput:
    ticker: str
    ts_utc: datetime
    price: float
    qty: float
    side: str
    trade_id: str
```

## 17.2. GridProposal
```python
class GridProposal:
    ticker: str
    frame: str
    status: str
    direction: str | None
    grid_upper_price: float | None
    grid_lower_price: float | None
    grid_mid_price: float | None
    grid_count: int | None
    tp: float | None
    sl: float | None
    confidence: float | None
    market_regime: str | None
    rationale: str | None
    reason: str | None
```

---

# 18. Acceptance criteria для Phase 1

Фаза считается готовой, если:

1. По одному тикеру можно загрузить сырой поток тиков.
2. Тики проходят нормализацию без падений.
3. Из тиков строятся 1s bars.
4. Считаются базовые rolling-features.
5. Классификатор возвращает один из 4 режимов.
6. Grid builder возвращает valid `Long` или `Short`, либо reject.
7. Выход соответствует контракту.
8. Есть минимум 5-10 тест-кейсов на типовые сценарии.
9. Ни один тикер не пропускается молча: либо `ready`, либо `rejected`.

---

# 19. Что не нужно делать в Phase 1

Чтобы не расползтись, в первую фазу **не включать**:
- machine learning
- capital allocation
- portfolio optimization
- cross-ticker ranking
- execution engine
- order placement
- multi-exchange routing
- ultra-complex clustering

---

# 20. Практический порядок реализации

## Step 1
Сделать контракты и тестовый loader тиков.

## Step 2
Сделать normalizer.

## Step 3
Сделать tick -> 1s aggregation.

## Step 4
Сделать базовые features.

## Step 5
Сделать regime classifier V1.

## Step 6
Сделать grid builder V1.

## Step 7
Сделать validator + reject.

## Step 8
Сделать rationale layer.

## Step 9
Собрать runner.

## Step 10
Прогнать на нескольких тикерах и исправить пороги.

---

# 21. Итоговое резюме

На входе у Maffi есть только тики. Этого достаточно.

Но чтобы из них получить **действительно рабочую и объяснимую 5m-сетку**, нужен строгий pipeline:

1. чтение тиков
2. очистка
3. агрегация
4. вычисление признаков
5. классификация режима
6. построение сетки
7. reject/validation
8. возврат контракта

Стартовать нужно с **Phase 1**, потому что именно она создаёт минимальную рабочую основу, поверх которой уже потом можно усиливать качество, адаптивность и точность.
