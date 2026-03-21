# Orchestration architecture decision

## Status
Accepted.

## Context
Pipeline Bobby Axe уже разделён на raw ingestion и curated analytics, а производные сущности должны детерминированно пересчитываться из raw-слоя. Для этого нужен формальный orchestration contract: какие именно события переводят данные между этапами, кто их публикует и кто их читает, как обеспечивается идемпотентность, какие SLA допустимы, и как система ведёт себя при retry, dead-letter, backfill и replay.

Этот документ фиксирует минимально достаточную модель orchestration как для полноценной event-driven реализации, так и для fallback-режима без выделенного event bus.

## Scope
Документ покрывает только pipeline переходов между следующими стадиями:

1. ingest raw trade data;
2. build `second_bars`;
3. produce analysis output;
4. produce grid proposals;
5. produce capital allocation;
6. produce final report/export metadata.

Документ не навязывает конкретную технологию транспорта. Допустимы Kafka / Redpanda / NATS JetStream / SQS+SNS / Postgres queue table / файловый spool, если соблюдаются одинаковые контракты события.

## Canonical event envelope
Каждое событие должно иметь общий envelope независимо от транспорта.

| Field | Required | Description |
| --- | --- | --- |
| `event_name` | Yes | Одно из канонических имён, перечисленных ниже. |
| `event_version` | Yes | Версия контракта payload, начиная с `1`. |
| `event_id` | Yes | Уникальный technical UUID конкретной публикации. |
| `idempotency_key` | Yes | Стабильный бизнес-ключ события, одинаковый при повторной публикации того же результата. |
| `correlation_id` | Yes | Сквозной идентификатор пайплайна/джоба для трассировки одного запуска. |
| `causation_id` | No | `event_id` события-родителя, если этап был вызван другим событием. |
| `producer` | Yes | Компонент, опубликовавший событие. |
| `occurred_at_utc` | Yes | Время публикации события в UTC. |
| `mode` | Yes | `realtime`, `backfill` или `replay`. |
| `partition_key` | Yes | Обычно `symbol`, либо `symbol + date`, если транспорт требует явной партиции. |
| `payload` | Yes | Бизнес-данные этапа. |

## Processing window contract
Для всех событий фиксируется единая модель окна обработки:

- каждое событие обязано ссылаться на **детерминированный интервал данных**;
- окно задаётся полями `symbol`, `window_start_utc`, `window_end_utc` и при необходимости `as_of_utc`;
- границы окна трактуются как полуинтервал `[window_start_utc, window_end_utc)`;
- downstream-потребитель обязан пересобирать свой результат целиком для указанного окна, а не пытаться «допатчить» отдельные строки без переагрегации;
- повторная публикация того же окна с тем же `idempotency_key` считается нормальной и должна быть безопасной.

## Event catalog

### 1. `raw_data_ingested`

**Meaning.** Raw-layer гарантированно записал и закоммитил диапазон нормализованных сделок, готовый для построения секундных баров.

**Producer.** `raw-ingestion-service`.

**Consumers.**

- `second-bars-builder` — основной потребитель;
- `pipeline-monitor` / `audit-log` — наблюдаемость;
- `backfill-coordinator` — если запуск был инициирован историческим диапазоном.

**Required payload.**

| Field | Description |
| --- | --- |
| `source` | Источник данных, например Binance stream / REST batch. |
| `symbol` | Канонический инструмент. |
| `window_start_utc` | Начало окна записанных raw-сделок. |
| `window_end_utc` | Конец окна записанных raw-сделок. |
| `trade_count` | Количество raw trades после dedup/upsert. |
| `min_trade_ts_utc` | Минимальный business timestamp в окне. |
| `max_trade_ts_utc` | Максимальный business timestamp в окне. |
| `raw_commit_ref` | Ссылка на batch/job/run, подтверждающая commit в raw layer. |

**Idempotency key.**

`raw_data_ingested:{source}:{symbol}:{window_start_utc}:{window_end_utc}:{raw_commit_ref}`

Если `raw_commit_ref` недоступен, допускается fallback:

`raw_data_ingested:{source}:{symbol}:{window_start_utc}:{window_end_utc}:{payload_checksum}`

**Repeated delivery policy.**

- если consumer уже завершил обработку этого `idempotency_key`, событие подтверждается без повторного side effect;
- если обработка ещё выполняется, дубликат не запускает второй concurrent rebuild того же окна;
- если предыдущая попытка завершилась ошибкой, допускается повторный запуск строго для того же окна.

**Stage timeout / SLA.**

- publish timeout у ingestion producer: `<= 5s` после commit в raw layer;
- end-to-end SLA до старта downstream обработки: `<= 30s` в realtime;
- для backfill допустимо `<= 5m` до постановки в очередь.

### 2. `second_bars_ready`

**Meaning.** Канонические секундные бары для окна полностью пересобраны и materialized в curated layer.

**Producer.** `second-bars-builder`.

**Consumers.**

- `analysis-engine` — основной потребитель;
- `quality-checker` — контроль полноты и дыр в секундах;
- `pipeline-monitor`.

**Required payload.**

| Field | Description |
| --- | --- |
| `symbol` | Канонический инструмент. |
| `window_start_utc` | Начало окна секундных баров. |
| `window_end_utc` | Конец окна секундных баров. |
| `second_count_expected` | Ожидаемое количество секунд в сетке окна. |
| `second_count_materialized` | Фактически пересчитанное количество строк. |
| `source_trade_count` | Количество raw trades, вошедших в расчёт. |
| `build_version` | Версия логики агрегации. |
| `rebuilt_at_utc` | Время завершения materialization. |

**Idempotency key.**

`second_bars_ready:{symbol}:{window_start_utc}:{window_end_utc}:{build_version}`

**Repeated delivery policy.**

- consumer обязан проверить registry обработанных ключей;
- если `build_version` не изменился и окно уже обработано, событие игнорируется как harmless duplicate;
- если пришло то же окно, но с новым `build_version`, это не duplicate, а осознанный reprocess, который должен пройти downstream заново.

**Stage timeout / SLA.**

- processing timeout на rebuild окна до `15m`: `<= 60s`;
- realtime SLA от `raw_data_ingested` до публикации `second_bars_ready`: `P95 <= 90s`, `P99 <= 180s`;
- backfill SLA на одно окно: `<= 10m`.

### 3. `analysis_ready`

**Meaning.** Аналитический слой для окна рассчитан и записан в curated tables / feature store.

**Producer.** `analysis-engine`.

**Consumers.**

- `grid-engine` — основной потребитель;
- `model-monitor` / `pipeline-monitor`.

**Required payload.**

| Field | Description |
| --- | --- |
| `symbol` | Канонический инструмент. |
| `window_start_utc` | Начало окна входных second bars / higher bars. |
| `window_end_utc` | Конец окна. |
| `analysis_set_id` | Стабильный идентификатор набора аналитических результатов. |
| `feature_version` | Версия аналитического пайплайна / feature schema. |
| `input_build_version` | Версия upstream second-bars build. |
| `computed_at_utc` | Время завершения расчёта. |

**Idempotency key.**

`analysis_ready:{symbol}:{window_start_utc}:{window_end_utc}:{analysis_set_id}:{feature_version}`

**Repeated delivery policy.**

- duplicate delivery не должна пересоздавать второй набор analysis rows;
- запись downstream делается через upsert/replace по `analysis_set_id` или эквивалентному business key;
- если downstream cache уже содержит готовый analysis result, допускается fast-ack без пересчёта.

**Stage timeout / SLA.**

- timeout одного job: `<= 120s`;
- realtime SLA от `second_bars_ready` до `analysis_ready`: `P95 <= 3m`, `P99 <= 5m`;
- backfill SLA на окно: `<= 15m`.

### 4. `grid_ready`

**Meaning.** Grid proposals для окна и symbol построены и готовы к аллокации капитала.

**Producer.** `grid-engine`.

**Consumers.**

- `allocation-engine` — основной потребитель;
- `approval-workflow` / `pipeline-monitor`.

**Required payload.**

| Field | Description |
| --- | --- |
| `symbol` | Канонический инструмент. |
| `window_start_utc` | Начало окна, на котором строилась grid. |
| `window_end_utc` | Конец окна. |
| `grid_set_id` | Стабильный идентификатор набора grid proposals. |
| `grid_version` | Версия grid logic. |
| `analysis_set_id` | Upstream analysis reference. |
| `proposal_count` | Количество сгенерированных proposals. |
| `computed_at_utc` | Время завершения расчёта. |

**Idempotency key.**

`grid_ready:{symbol}:{window_start_utc}:{window_end_utc}:{grid_set_id}:{grid_version}`

**Repeated delivery policy.**

- дубликат не должен создавать вторую пачку grid proposals;
- allocation step обязан использовать `grid_set_id` как business reference и отбрасывать вторую обработку того же набора;
- если grid пересчитан новой версией, публикуется новый ключ и downstream считает это новым событием.

**Stage timeout / SLA.**

- timeout одного job: `<= 60s`;
- realtime SLA от `analysis_ready` до `grid_ready`: `P95 <= 2m`, `P99 <= 4m`;
- backfill SLA: `<= 10m`.

### 5. `allocation_ready`

**Meaning.** Капитал распределён по готовому grid set и сохранён как детерминированный allocation result.

**Producer.** `allocation-engine`.

**Consumers.**

- `report-builder` — основной потребитель;
- `execution-gateway` — если есть отдельный этап исполнения;
- `risk-monitor` / `pipeline-monitor`.

**Required payload.**

| Field | Description |
| --- | --- |
| `symbol` | Канонический инструмент. |
| `window_start_utc` | Начало окна, для которого релевантна аллокация. |
| `window_end_utc` | Конец окна. |
| `allocation_set_id` | Стабильный идентификатор allocation result. |
| `allocation_version` | Версия логики аллокации. |
| `grid_set_id` | Upstream grid reference. |
| `capital_profile_id` | Идентификатор профиля капитала / лимитов. |
| `computed_at_utc` | Время готовности результата. |

**Idempotency key.**

`allocation_ready:{symbol}:{window_start_utc}:{window_end_utc}:{allocation_set_id}:{allocation_version}:{capital_profile_id}`

**Repeated delivery policy.**

- report-builder обязан быть идемпотентным по `allocation_set_id`;
- повторная доставка не инициирует второе резервирование капитала или повторную запись тех же allocation rows;
- любые side effects вне БД выполняются только после проверки dedup registry/outbox.

**Stage timeout / SLA.**

- timeout одного job: `<= 60s`;
- realtime SLA от `grid_ready` до `allocation_ready`: `P95 <= 2m`, `P99 <= 4m`;
- backfill SLA: `<= 10m`.

### 6. `report_ready`

**Meaning.** Отчётный артефакт или metadata export для окна сформированы и доступны потребителям.

**Producer.** `report-builder`.

**Consumers.**

- `report-distributor` / UI / API;
- `audit-log`;
- `pipeline-monitor`.

**Required payload.**

| Field | Description |
| --- | --- |
| `symbol` | Канонический инструмент. |
| `window_start_utc` | Начало окна, покрытого отчётом. |
| `window_end_utc` | Конец окна. |
| `report_id` | Стабильный идентификатор отчёта. |
| `report_version` | Версия схемы отчёта / экспорта. |
| `allocation_set_id` | Upstream allocation reference. |
| `artifact_uri` | URI файла, записи или export object. |
| `generated_at_utc` | Время генерации. |

**Idempotency key.**

`report_ready:{symbol}:{window_start_utc}:{window_end_utc}:{report_id}:{report_version}`

**Repeated delivery policy.**

- повторная доставка не должна создавать duplicate report metadata;
- если файл уже существует по `artifact_uri`, допустим verify-and-ack без повторной генерации;
- если репорт пересобран новой версией или в новый URI, публикуется новый `idempotency_key`.

**Stage timeout / SLA.**

- timeout одного job: `<= 120s`;
- realtime SLA от `allocation_ready` до `report_ready`: `P95 <= 3m`, `P99 <= 5m`;
- полный realtime SLA цепочки `raw_data_ingested -> report_ready`: `P95 <= 15m`, `P99 <= 30m`;
- backfill SLA: `<= 20m` на окно.

## Producer / consumer responsibility matrix

| Event | Producer | Primary consumer | Secondary consumers |
| --- | --- | --- | --- |
| `raw_data_ingested` | `raw-ingestion-service` | `second-bars-builder` | `pipeline-monitor`, `audit-log`, `backfill-coordinator` |
| `second_bars_ready` | `second-bars-builder` | `analysis-engine` | `quality-checker`, `pipeline-monitor` |
| `analysis_ready` | `analysis-engine` | `grid-engine` | `model-monitor`, `pipeline-monitor` |
| `grid_ready` | `grid-engine` | `allocation-engine` | `approval-workflow`, `pipeline-monitor` |
| `allocation_ready` | `allocation-engine` | `report-builder` | `execution-gateway`, `risk-monitor`, `pipeline-monitor` |
| `report_ready` | `report-builder` | `report-distributor` / API / UI | `audit-log`, `pipeline-monitor` |

## Idempotency and duplicate handling policy

### General rules

1. Каждый consumer обязан вести **processed-event registry** с уникальным индексом по `idempotency_key` и `consumer_name`.
2. Side effects разрешены только после atomically successful записи в бизнес-таблицы и registry/outbox.
3. Для каждого этапа запись результата должна выполняться через `upsert`, `merge`, `replace partition` или другой детерминированный overwrite-механизм.
4. Duplicate delivery считается штатным сценарием, а не ошибкой.
5. Consumer должен различать:
   - **same key + same version** → harmless duplicate, ack without effect;
   - **same window + new version** → intentional reprocess, process again;
   - **same key + payload mismatch** → data contract violation, route to dead-letter и поднять alert.

### Minimal processed-event registry

Минимальная SQL-таблица registry:

- `consumer_name`
- `idempotency_key`
- `event_name`
- `event_version`
- `payload_checksum`
- `first_seen_at_utc`
- `last_seen_at_utc`
- `processing_status` (`processing`, `completed`, `failed`, `dead_lettered`)
- `last_error`

Уникальный ключ: `consumer_name + idempotency_key`.

### What to do on redelivery

При повторной доставке consumer действует так:

1. вычисляет checksum payload и ищет запись по `consumer_name + idempotency_key`;
2. если найдена запись со статусом `completed` и тем же checksum, делает `ack + no-op`;
3. если запись в статусе `processing`, не запускает второй конкурентный job, а requeue/ack зависит от транспорта;
4. если запись в статусе `failed`, может повторить обработку в пределах retry policy;
5. если checksum отличается, переносит сообщение в dead-letter как конфликтующий duplicate.

## Timeouts, retries, and dead-letter policy

### Consumer timeout defaults

Если этап не зафиксировал свой timeout отдельно, действует дефолт:

- lock/lease на обработку: `2 x` ожидаемого job timeout;
- heartbeat в orchestration store: каждые `15s`;
- событие считается stalled, если heartbeat отсутствует `> 45s`.

### Retry policy

Для всех этапов используется bounded retry с exponential backoff и jitter:

- attempt `1`: immediately;
- attempt `2`: через `30s`;
- attempt `3`: через `2m`;
- attempt `4`: через `10m`;
- attempt `5`: через `30m`.

После 5 неуспешных попыток событие переводится в dead-letter.

### Error classes

**Retryable:**

- временно недоступна БД/шина;
- lock timeout / transient network error;
- upstream dependency не успела materialize данные;
- rate limit внешнего сервиса.

**Non-retryable:**

- schema mismatch payload;
- отсутствует обязательное поле события;
- checksum conflict для одинакового `idempotency_key`;
- нарушен invariant окна (`window_end_utc <= window_start_utc`);
- бизнес-версия результата неизвестна системе и не поддерживается.

### Dead-letter policy

Для dead-letter должен существовать отдельный канал/таблица `pipeline_dead_letter` c полями:

- `dead_lettered_at_utc`
- `event_name`
- `event_id`
- `idempotency_key`
- `consumer_name`
- `payload`
- `payload_checksum`
- `failure_class`
- `failure_reason`
- `attempt_count`
- `correlation_id`
- `mode`

Правила:

- dead-letter событие не удаляется автоматически до ручного разбора;
- для каждого dead-letter создаётся alert в monitoring;
- replay из dead-letter допускается только отдельной операторской командой после устранения причины.

## Backfill and replay policy

### Definitions

- **Backfill** — первичное построение исторического диапазона, который ранее не был рассчитан или был рассчитан не полностью.
- **Replay** — повторный прогон уже рассчитанного диапазона из-за смены логики, исправления данных или восстановления после сбоя.

### Control principles

1. Backfill и replay всегда запускаются как **явный orchestration job** с собственным `correlation_id` и `mode`.
2. Исторический диапазон режется на детерминированные окна фиксированного размера, например по `5m`, `1h` или `1d`, в зависимости от этапа.
3. Для одного `symbol` окна выполняются последовательно по времени, если downstream зависит от полного порядка; для независимых окон допускается ограниченный parallelism.
4. Каждый этап публикует те же canonical events, но с `mode = backfill` или `mode = replay`.
5. Потребители не должны иметь отдельную бизнес-логику для backfill/replay кроме отличий по SLA и rate limiting.

### Backfill procedure

1. Оператор или scheduler создаёт `backfill_job` c диапазоном `from_utc` / `to_utc`, списком `symbols`, размером окна и целевыми этапами.
2. `backfill-coordinator` строит очередь окон: например `BTCUSDT` × каждый `1h` bucket.
3. Для каждого окна coordinator инициирует ingest/rebuild начиная с самого раннего требуемого этапа:
   - если raw уже присутствует и валиден, можно стартовать с `raw_data_ingested` synthetic event;
   - если raw отсутствует, сначала загружается raw batch.
4. Каждый downstream этап пишет результат через overwrite/upsert на своё окно.
5. После завершения диапазона фиксируется `job_manifest` с количеством окон, успехов, ошибок и dead-letter записей.

### Replay procedure

Replay используется в двух случаях:

1. изменилась логика (`build_version`, `feature_version`, `grid_version`, `allocation_version`, `report_version`);
2. upstream данные были исправлены и downstream нужно пересчитать.

Правила replay:

- replay обязан стартовать с **самого раннего повреждённого или изменённого этапа**;
- для replay публикуются новые idempotency keys за счёт новой версии результата или нового job reference;
- старые результаты не должны silently смешиваться с новыми: применяется либо versioned storage, либо атомарный replace результата окна;
- по завершении replay рекомендуется верификация row counts / checksums для диапазона.

### Safe ordering for historical ranges

Для диапазона `[from_utc, to_utc)` порядок должен быть таким:

1. raw ingestion / validation;
2. `raw_data_ingested`;
3. rebuild `second_bars` и публикация `second_bars_ready`;
4. recompute analysis и публикация `analysis_ready`;
5. recompute grid и публикация `grid_ready`;
6. recompute allocation и публикация `allocation_ready`;
7. recompute reports и публикация `report_ready`.

Нельзя запускать downstream replay до подтверждения готовности upstream окна для того же `symbol` и времени.

## Minimal fallback mode without event bus

Если полноценного event bus нет, pipeline всё равно должен сохранить те же контракты через один из минимальных транспортов.

### Option A: SQL queue table

Минимальный fallback — таблица `pipeline_queue` в SQL.

Рекомендуемые поля:

- `queue_id`
- `event_name`
- `event_version`
- `event_id`
- `idempotency_key`
- `correlation_id`
- `causation_id`
- `producer`
- `mode`
- `partition_key`
- `payload_json`
- `payload_checksum`
- `visible_after_utc`
- `status` (`queued`, `leased`, `completed`, `failed`, `dead_lettered`)
- `attempt_count`
- `leased_until_utc`
- `consumer_name`
- `created_at_utc`
- `updated_at_utc`
- `last_error`

Правила работы:

1. Producer пишет событие в `pipeline_queue` в той же транзакции, что и бизнес-результат, либо через outbox-table pattern.
2. Consumer выбирает сообщения `FOR UPDATE SKIP LOCKED`, проставляет lease и обрабатывает пакет.
3. Dedup делается по тем же `idempotency_key` + registry.
4. Retry реализуется через увеличение `attempt_count` и перенос `visible_after_utc` вперёд.
5. После достижения лимита попыток строка переводится в `dead_lettered` и копируется в `pipeline_dead_letter`.

### Option B: File artifact spool

Если даже SQL queue недоступна, допускается файловый spool в shared filesystem / object storage prefix.

Минимальная структура:

- `spool/pending/<event_name>/<idempotency_key>.json`
- `spool/processing/<consumer_name>/<idempotency_key>.json`
- `spool/completed/<consumer_name>/<idempotency_key>.json`
- `spool/dead-letter/<consumer_name>/<idempotency_key>.json`

Правила:

1. Producer сначала атомарно пишет временный файл, затем делает `rename` в `pending`.
2. Consumer захватывает событие через атомарный move из `pending` в `processing`.
3. Duplicate detection выполняется по имени файла и локальному/SQL registry обработанных ключей.
4. Retry реализуется обратным перемещением в `pending` с записью `attempt_count` в JSON metadata.
5. Dead-letter — перемещение в `dead-letter` после превышения лимита попыток.

### Fallback limitations

Fallback-режим допустим только как минимальное решение и имеет ограничения:

- ниже throughput и выше latency;
- сложнее гарантировать ordering между несколькими инстансами;
- выше риск ручных операционных ошибок;
- наблюдаемость и replay менее удобны, чем у полноценного event bus.

Поэтому fallback должен сохранять те же event names, envelope и idempotency semantics, чтобы поздний переход на шину не требовал переписывания бизнес-логики этапов.

## Operational requirements

Минимально обязательны следующие метрики и алерты:

- lag от публикации события до начала обработки;
- lag от начала обработки до completion;
- количество duplicate deliveries;
- retry count по этапам;
- dead-letter count по этапам и по `symbol`;
- backfill/replay progress по окнам;
- full pipeline latency от `raw_data_ingested` до `report_ready`.

Любой этап, превышающий свой `P99` SLA более чем на 2 последовательных окна, должен поднимать alert.
