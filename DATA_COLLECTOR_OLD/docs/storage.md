# Storage architecture decision

## Status
Accepted.

## Context
Система Bobby Axe должна одновременно решать две разные задачи хранения:

1. Надёжно принимать и сохранять high-volume поток входящих сделок из Binance без потери событий.
2. Предоставлять стабильный и удобный слой данных для аналитики, генерации grid-предложений, аллокации капитала и экспорта отчётов.

Ранее естественным, но неудачным вариантом выглядело решение «одна база на тикер». Для текущей системы этот вариант создаёт слишком высокую операционную сложность:

- усложняет онбординг новых `symbol`;
- дробит мониторинг, резервное копирование и миграции;
- затрудняет межсимвольную аналитику и отчётность;
- делает retention и партиционирование менее предсказуемыми;
- увеличивает стоимость сопровождения.

Поэтому storage architecture должна быть разделена не по отдельным базам на каждый тикер, а по назначению данных: raw ingestion и curated analytics.

## Decision

### 1. Два слоя хранения

Принимается двухслойная архитектура:

- **Raw layer** — отдельная СУБД для приёма и первичного хранения входящих сделок и других событий ingest.
- **Curated layer** — отдельная СУБД **или** отдельная схема в аналитической СУБД для агрегатов, аналитических результатов, grid-предложений, аллокаций и экспортов.

### 2. Не использовать модель «1 база на тикер»

Вместо «1 база на тикер» фиксируется следующее решение:

- **одна СУБД на raw ingestion**;
- **одна СУБД или схема на curated analytics**;
- **логическое разделение по `symbol` внутри таблиц**, а не физическое выделение отдельной базы под каждый тикер.

### 3. Границы ответственности слоёв

#### Raw layer
Raw layer отвечает за:

- запись входящих сделок в исходном или почти исходном виде;
- deduplication и idempotent upsert при повторной доставке;
- восстановление агрегатов при переигрывании диапазона дат;
- короткий или средний retention для high-volume данных.

#### Curated layer
Curated layer отвечает за:

- секундные бары и таймфреймы `1m`, `5m`, `60m`;
- результаты аналитики;
- grid proposals;
- capital allocations;
- metadata по сформированным отчётам.

## Timezone policy

Во всех таблицах canonical timezone — **UTC**.

Правила:

- все timestamp-поля хранятся как UTC;
- имена временных полей в рыночных данных должны явно отражать UTC-семантику (`event_time_utc`, `ts_second_utc`); для остальных доменов UTC-требование также сохраняется, но конкретное имя фиксируется их собственным контрактом;
- при чтении в UI/отчёты допускается локальная конверсия, но source of truth в БД всегда UTC;
- границы партиций и retention считаются в UTC.


## Storage fields vs transport fields

Канонический словарь для storage и transport единый. База данных, документация и JSON-схемы должны использовать одинаковые имена полей, чтобы исключить двусмысленность при агрегации, мониторинге и отладке.

Если на границе конкретного API понадобится компактный JSON, он должен рассматриваться как слой совместимости, а не как альтернативная каноническая модель. В таком случае адаптер обязан явно маппить compact aliases в canonical fields до записи в storage или публикации в основной контракт.

| Семантика | Canonical storage field | Canonical transport field | Legacy compact alias | Комментарий |
| --- | --- | --- | --- | --- |
| Время сделки | `event_time_utc` | `event_time_utc` | `trade_ts` | UTC business timestamp сделки |
| Количество сделки | `quantity` | `quantity` | `qty` | Размер сделки в базовом активе |
| Секундный timestamp | `ts_second_utc` | `ts_second_utc` | `second_ts` | Начало календарной секунды UTC |
| Общий объём | `base_volume` | `base_volume` | `volume` | `volume` слишком неоднозначно без указания единиц |
| Объём buy aggressor | `buy_volume` | `buy_volume` | `bid_volume` | Не эквивалентно book bid liquidity |
| Объём sell aggressor | `sell_volume` | `sell_volume` | `ask_volume` | Не эквивалентно book ask liquidity |

Отдельно фиксируется семантическое правило: `buy_volume` / `sell_volume` — это объёмы исполненных сделок по стороне агрессора, а `bid_volume` / `ask_volume` в терминологии микроструктуры обычно относятся к пассивной ликвидности стакана или к стороне котировки. Поэтому эти пары терминов **не взаимозаменяемы**.

## Idempotency and deduplication policy

### Входящие сделки
Для входящих сделок фиксируются следующие правила:

- ingest должен быть **idempotent**;
- повторная доставка одного и того же trade event не должна приводить к дублированию в `raw_trades`;
- базовый natural key для дедупликации: `source + symbol + trade_id`;
- если внешний `trade_id` недоступен или ненадёжен, fallback-ключ: `source + symbol + event_time_utc + price + quantity + side_aggressor`;
- все повторные загрузки диапазона должны выполняться через `upsert`/`merge`, а не через blind insert;
- агрегаты в curated-слое должны быть детерминированно пересчитываемыми из raw-слоя.

### Агрегаты и производные таблицы

- `second_bars` и OHLC-таблицы должны пересобираться идемпотентно для конкретного окна времени;
- uniqueness для агрегатов обеспечивается ключом `symbol + frame + bar_ts` или специализированным PK на таблицу;
- `analysis_results`, `grid_proposals`, `capital_allocations` и `report_exports` должны поддерживать повторную запись одного бизнес-результата без появления дублей через стабильные business IDs.

## Partitioning policy

Для high-volume таблиц применяется партиционирование по **дате** и `symbol`.

Базовое правило:

- первичный уровень — партиционирование по дате/времени (`trade_date`, `bar_date` или диапазон по timestamp);
- вторичный уровень — subpartition или логическое кластеризованное разбиение по `symbol`, если это поддерживает выбранная СУБД;
- если субпартиции по `symbol` недоступны, обязательны составные индексы с первым ключом по времени и вторым по `symbol` либо наоборот, в зависимости от паттерна запроса.

Это требование обязательно как минимум для:

- `raw_trades`;
- `second_bars`;
- `ohlc_1m`;
- `ohlc_5m`;
- `ohlc_60m`.

## Physical layout

Пример логической раскладки:

- `raw` database/schema
  - `raw_trades`
- `curated` database/schema
  - `second_bars`
  - `ohlc_1m`
  - `ohlc_5m`
  - `ohlc_60m`
  - `analysis_results`
  - `grid_proposals`
  - `capital_allocations`
  - `report_exports`

Конкретная технология СУБД может быть выбрана отдельно, но сама storage decision остаётся неизменной: **разделение по слоям, а не по тикерам**.

## Table design

### `raw_trades`
Назначение: неизменяемый или append-mostly журнал входящих сделок, достаточный для переагрегации.

| Field | Decision |
| --- | --- |
| Layer | raw |
| Primary key | `source, symbol, trade_id` |
| Secondary unique key | `source, symbol, event_time_utc, price, quantity, side_aggressor` как fallback, если `trade_id` ненадёжен |
| Main indexes | `(symbol, event_time_utc DESC)`, `(event_time_utc DESC)`, при необходимости `(symbol, ingested_at_utc DESC)` |
| Partitioning | обязательно по `trade_date` с под-разделением или кластеризацией по `symbol` |
| Retention | `30-90` дней online; более старые данные — в холодный архив/объектное хранилище |

Рекомендуемые поля:

- `source`
- `symbol`
- `trade_id`
- `event_time_utc`
- `price`
- `quantity`
- `side_aggressor`
- `ingested_at_utc`
- `payload_checksum` или аналогичный technical hash

### `second_bars`
Назначение: канонический секундный агрегат для последующего построения таймфреймов и анализа.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `symbol, ts_second_utc` |
| Main indexes | `(ts_second_utc DESC)`, `(symbol, ts_second_utc DESC)` |
| Partitioning | обязательно по `bar_date`/дате `ts_second_utc` с под-разделением или кластеризацией по `symbol` |
| Retention | `180-365` дней online |

Рекомендуемые поля:

- `symbol`
- `ts_second_utc`
- `open`
- `high`
- `low`
- `close`
- `base_volume`
- `quote_volume`
- `trade_count`
- `buy_volume`
- `sell_volume`
- `delta_volume`
- `vwap`
- `build_version`
- `rebuilt_at`

### `ohlc_1m`
Назначение: минутный OHLC-слой для аналитики и пересчёта старших таймфреймов при необходимости.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `symbol, bar_ts` |
| Main indexes | `(bar_ts DESC)`, `(symbol, bar_ts DESC)` |
| Partitioning | обязательно по `bar_date` с под-разделением или кластеризацией по `symbol` |
| Retention | `2` года online |

Рекомендуемые поля:

- `symbol`
- `bar_ts`
- `open`
- `high`
- `low`
- `close`
- `base_volume`
- `quote_volume`
- `trade_count`
- `source_second_count`
- `build_version`

### `ohlc_5m`
Назначение: основной торговый таймфрейм для grid proposals.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `symbol, bar_ts` |
| Main indexes | `(bar_ts DESC)`, `(symbol, bar_ts DESC)` |
| Partitioning | обязательно по `bar_date` с под-разделением или кластеризацией по `symbol` |
| Retention | `3` года online |

Рекомендуемые поля:

- `symbol`
- `bar_ts`
- `open`
- `high`
- `low`
- `close`
- `base_volume`
- `quote_volume`
- `trade_count`
- `source_1m_count`
- `build_version`

### `ohlc_60m`
Назначение: старший таймфрейм для аналитических стратегий и контекстных фильтров.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `symbol, bar_ts` |
| Main indexes | `(bar_ts DESC)`, `(symbol, bar_ts DESC)` |
| Partitioning | обязательно по `bar_date` с под-разделением или кластеризацией по `symbol` |
| Retention | бессрочно online либо минимум `5` лет |

Рекомендуемые поля:

- `symbol`
- `bar_ts`
- `open`
- `high`
- `low`
- `close`
- `base_volume`
- `quote_volume`
- `trade_count`
- `source_5m_count`
- `build_version`

### `analysis_results`
Назначение: сохранённые результаты стратегий `Ben_Kim` по таймфреймам `1m`, `5m`, `60m`.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `analysis_id` |
| Unique key | `symbol, strategy, frame, observed_at` |
| Main indexes | `(symbol, frame, observed_at DESC)`, `(status, observed_at DESC)` |
| Partitioning | по месяцу `observed_at`; для больших объёмов дополнительно по `symbol` |
| Retention | бессрочно, так как это audit trail аналитики |

Рекомендуемые поля согласованы с контрактом `analysis_result`:

- `analysis_id`
- `symbol`
- `strategy`
- `frame`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `source_window_from`
- `source_window_to`
- `status`
- `details_json`
- `created_at`

### `grid_proposals`
Назначение: торговые grid-предложения `Maffi` для таймфрейма `5m`.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `proposal_id` |
| Unique key | `symbol, frame, proposal_id` |
| Main indexes | `(symbol, created_at DESC)`, `(status, created_at DESC)` |
| Partitioning | по месяцу `created_at`; по `symbol` при росте объёма |
| Retention | бессрочно, минимум `3` года online |

Рекомендуемые поля:

- `proposal_id`
- `symbol`
- `frame`
- `direction`
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `sl`
- `tp`
- `rationale`
- `analysis_ids`
- `signal_summary_json`
- `status`
- `created_at`

### `capital_allocations`
Назначение: результаты распределения капитала от `1$_Dollar_Bill`.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `allocation_id` |
| Unique key | `proposal_id` или `symbol, approved_at`, в зависимости от бизнес-режима |
| Main indexes | `(approved_at DESC)`, `(symbol, approved_at DESC)`, `(risk_bucket, approved_at DESC)` |
| Partitioning | по месяцу `approved_at`; по `symbol` при росте истории |
| Retention | бессрочно |

Рекомендуемые поля:

- `allocation_id`
- `symbol`
- `proposal_id`
- `allocation_pct`
- `risk_bucket`
- `rationale`
- `supporting_analysis_ids`
- `approved_at`
- `status`
- `created_at`

### `report_exports`
Назначение: журнал экспортов и артефактов отчётности `Jusetta`.

| Field | Decision |
| --- | --- |
| Layer | curated |
| Primary key | `job_id` |
| Main indexes | `(requested_at DESC)`, `(status, requested_at DESC)` |
| Partitioning | по месяцу `requested_at`; разделение по `symbol` не требуется как обязательное |
| Retention | metadata бессрочно; сами файлы отчётов — по отдельной policy, например `180-365` дней online |

Рекомендуемые поля:

- `job_id`
- `requested_at`
- `report_from`
- `report_to`
- `symbols_json`
- `pdf_path`
- `table_path`
- `delivery_channel`
- `delivery_recipient`
- `status`
- `exported_at`
- `error_message`

## Query model

Ожидаемые паттерны запросов:

- по одному `symbol` за интервал времени;
- по множеству `symbol` за фиксированный интервал для отчёта;
- чтение последних баров по `symbol`;
- выборка последних аналитических результатов и grid-предложений;
- аудит расчётов и повторная сборка агрегатов за конкретную дату.

Именно поэтому `symbol` должен быть логическим ключом фильтрации и индексирования во всех основных таблицах, но не границей физического выделения отдельной базы.

## Consequences

### Positive

- проще эксплуатация, миграции и backup/restore;
- легче добавлять новые `symbol` без provisioning новой БД;
- проще делать межсимвольные отчёты и аллокации;
- понятнее lifecycle management и retention;
- сохраняется возможность масштабировать high-volume таблицы через партиционирование.

### Trade-offs

- потребуется дисциплина по индексам и partition pruning;
- multi-tenant-like нагрузка по разным `symbol` должна контролироваться на уровне запросов и batch job scheduling;
- при экстремальном росте числа символов может понадобиться шардирование, но это отдельное решение и не часть текущего baseline.

## Final storage decision

Итоговое архитектурное решение фиксируется так:

1. **Raw ingestion хранится в одной общей СУБД raw-слоя.**
2. **Curated analytics хранится в одной общей СУБД или одной общей схеме curated-слоя.**
3. **Разделение между тикерами выполняется логически через поле `symbol`, индексы и партиции, а не через отдельные базы на тикер.**
4. **High-volume таблицы обязаны поддерживать партиционирование по дате и `symbol`.**
5. **Все timestamps хранятся в UTC.**
6. **Ingest и производные агрегации обязаны быть idempotent и поддерживать deduplication.**
