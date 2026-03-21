# Ben_Kim Runtime Spec

## Status
Accepted for current Ben_Kim operating mode.

## Purpose
Этот документ фиксирует прикладной runtime-контур `Ben_Kim` для live/snapshot-запросов, когда `Jack` либо:
- передаёт уже подготовленный feature-пакет, либо
- предоставляет доступ к данным, из которых `Ben_Kim` читает подготовленные признаки.

Документ уточняет, как именно `Ben_Kim` должен обрабатывать вход, раскладывать анализ по стратегиям и таймфреймам и возвращать batch `analysis_result` обратно в storage/`Jack`.

---

## 1. Canonical unit of work

Одна каноническая единица работы `Ben_Kim`:

- один `ticker`
- три таймфрейма: `1m`, `5m`, `60m`
- все активные стратегии из текущего runtime-конфига

Общее число ожидаемых результатов:

`results_count = tickers_count × 3 × active_strategies_count`

Пример:
- `1` тикер
- `6` активных стратегий
- `3` таймфрейма
- итог: `18` отдельных коротких заключений

---

## 2. Current active strategy set

Текущий рабочий набор стратегий для пользовательских snapshot/live-запросов:

1. `price_levels_fibo_horizontal_volume`
   - ценовые уровни
   - уровни Фибоначчи
   - горизонтальные объёмы
2. `vertical_volume`
3. `rsi_macd`
4. `trade_speed`
5. `added_later_placeholder`
6. `elliott_waves`

Если стратегия присутствует в runtime-конфиге, `Ben_Kim` обязан попытаться выдать результат по всем трём таймфреймам.
Если данных или признаков недостаточно, вместо выдуманного вывода возвращается формализованный `partial`-результат.

---

## 3. Input contract at runtime

`Ben_Kim` должен принимать либо batch feature-пакетов, либо иметь возможность прочитать их из storage.

### 3.1 Required runtime fields per ticker/frame packet

Минимально ожидаемые поля:

- `symbol`
- `frame`
- `observed_at`
- `source_window.from`
- `source_window.to`
- `features`
- `data_quality`

### 3.2 Recommended feature groups

`Jack` должен передавать признаки следующими группами:

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

### 3.3 Hard rule on missing data

Если пакет не содержит признаков, необходимых для конкретной стратегии:
- `Ben_Kim` не додумывает отсутствующие значения;
- возвращает `status=partial`;
- использует `result_code=insufficient_data` или `skipped` по ситуации.

---

## 4. Processing order inside Ben_Kim

Для каждого входящего тикера:

1. проверить, что тикер валиден и существует в universe текущего запуска;
2. получить 3 runtime-среза: `1m`, `5m`, `60m`;
3. для каждого таймфрейма пройти по всему списку активных стратегий;
4. для каждой комбинации `symbol + frame + strategy` сформировать ровно один `analysis_result`;
5. собрать batch результатов по тикеру;
6. записать batch в storage и/или передать `Jack`.

`Ben_Kim` не должен смешивать несколько стратегий в один объект и не должен объединять несколько таймфреймов в одно заключение.

---

## 5. Output rules

Каждый результат должен соответствовать схеме `contracts/schemas/analysis_result.schema.json`.

### 5.1 Required output fields

- `event_type`
- `analysis_id`
- `symbol`
- `strategy`
- `frame`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `source_window.from`
- `source_window.to`
- `status`
- `result_code`

### 5.2 User-facing short interpretation mapped to canonical fields

Пользовательская логика:
- `ticker`
- `strategy`
- `conclusion`
- `time`
- `frame`

В storage она должна сохраняться как канонический `analysis_result`:
- `ticker` -> `symbol`
- `time` -> `observed_at`
- текстовая краткая аналитика -> `conclusion`

### 5.3 Conclusion style

`conclusion` должен быть:
- коротким;
- конкретным;
- проверяемым по признакам;
- без воды;
- без сеток и без аллокаций;
- без выдумывания отсутствующего сигнала.

Допустимая логика текста:
- есть / нет сигнала;
- как именно он выражен;
- краткая интерпретация;
- если нужно — почему вывод слабый или частичный.

---

## 6. Strategy-by-strategy runtime expectation

### 6.1 `price_levels_fibo_horizontal_volume`
Ожидаемые признаки:
- support/resistance
- pivot zones
- nearest fib levels
- POC / VAH / VAL / HVN / LVN

Краткий вывод должен отвечать:
- находится ли цена у значимой зоны;
- есть ли confluence уровня, fib и горизонтального объёма;
- выглядит ли зона как поддержка, сопротивление или нейтральный диапазон.

### 6.2 `vertical_volume`
Ожидаемые признаки:
- total volume
- buy/sell imbalance
- delta
- volume anomaly / z-score
- trade_count anomaly

Краткий вывод должен отвечать:
- подтверждает ли объём текущее движение;
- есть ли всплеск/кульминация;
- наблюдается ли absorption или continuation.

### 6.3 `rsi_macd`
Ожидаемые признаки:
- RSI(14)
- MACD line
- MACD signal
- MACD histogram
- факт кросса / смены наклона

Краткий вывод должен отвечать:
- momentum bullish / bearish / neutral;
- есть ли разворотный или подтверждающий сигнал;
- насколько сигнал зрелый.

### 6.4 `trade_speed`
Ожидаемые признаки:
- trades/sec
- volume/sec
- burstiness
- acceleration/deceleration

Краткий вывод должен отвечать:
- ускоряется ли поток сделок;
- поддерживает ли скорость текущее движение;
- есть ли импульсный burst или затухание.

### 6.5 `added_later_placeholder`
Пока стратегия не описана предметно:
- допускается `status=partial`
- `result_code=skipped`
- с явным пояснением, что стратегия зарезервирована для будущей реализации.

### 6.6 `elliott_waves`
Ожидаемые признаки:
- swing sequence
- wave candidate
- fib wave ratios
- invalidation level
- wave confidence

Краткий вывод должен отвечать:
- просматривается ли волновая структура-кандидат;
- насколько она слабая/средняя/рабочая;
- где инвалидация сценария.

---

## 7. Canonical batch workflow

Для одного тикера batch должен быть логически сгруппирован так:

- `symbol`
  - `1m`
    - strategy A -> one `analysis_result`
    - strategy B -> one `analysis_result`
    - ...
  - `5m`
    - strategy A -> one `analysis_result`
    - ...
  - `60m`
    - strategy A -> one `analysis_result`
    - ...

Но в storage каждый элемент сохраняется как отдельный объект.

---

## 8. Persistence rule

После завершения анализа `Ben_Kim` обязан:

1. сформировать полный batch по тикеру;
2. провалидировать обязательные поля;
3. записать результаты в storage;
4. вернуть `Jack` подтверждение, что analysis-only batch сохранён.

Если запись провалилась:
- результат не считается завершённым;
- ошибка должна быть зафиксирована как операционный сбой хранения.

---

## 9. Acceptance criteria for Ben_Kim readiness

`Ben_Kim` считается готовым к runtime-работе в согласованном формате, если:

1. умеет принимать тикерный feature-пакет от `Jack`;
2. умеет раскладывать анализ на `1m/5m/60m`;
3. умеет прогонять весь набор активных стратегий;
4. возвращает отдельный результат на каждую комбинацию `ticker × frame × strategy`;
5. не выдумывает выводы при нехватке данных;
6. сохраняет batch как `analysis_result` в канонической схеме.
