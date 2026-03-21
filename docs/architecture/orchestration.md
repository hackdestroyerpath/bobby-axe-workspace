# Orchestration architecture decision

## Status
Accepted.

## Context
Pipeline Bobby Axe уже разделён на raw ingestion и curated analytics, а производные сущности должны детерминированно пересчитываться из raw-слоя. Для этого нужен формальный orchestration contract: какие именно события переводят данные между этапами, кто их публикует и кто их читает, как обеспечивается идемпотентность, какие SLA допустимы, и как система ведёт себя при retry, dead-letter, backfill и replay.

Дополнительно система должна чётко разделять:
- **analysis-only / preview artifacts** — ранние промежуточные артефакты после `Ben_Kim`;
- **final user-facing report artifacts** — `report_job`, пользовательский PDF и сопутствующий package только после `Maffi` и `1$_Dollar_Bill`.

Этот документ фиксирует минимально достаточную модель orchestration как для полноценной event-driven реализации, так и для fallback-режима без выделенного event bus.

## Scope
Документ покрывает только pipeline переходов между следующими стадиями:

0. ingest raw trade data;
1. build `second_bars`;
2. produce analysis-only output;
3. optionally produce `analysis_preview`;
4. produce grid proposals;
5. produce capital allocation;
6. produce final report/export metadata.

Документ не навязывает конкретную технологию транспорта. Допустимы Kafka / Redpanda / NATS JetStream / SQS+SNS / Postgres queue table / файловый spool, если соблюдаются одинаковые контракты события.

## Canonical stage order and artifact classes

| Stage | Producer | Artifact / event | Class | Final? | May be sent to user? | Blocked when allocations are missing? |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | `Jack` / ingestion | raw + `second_bars` | Upstream operational | No | No | No |
| 1 | `Ben_Kim` | `analysis_result` / `analysis_ready` | Intermediate analysis-only | No | No, not as a final report | No |
| 2 | `Jusetta` (optional) | `analysis_preview` / `analysis_preview_ready` | Intermediate draft | No | Yes, only if explicitly labeled preview/draft | No |
| 3 | `Maffi` | `grid_proposal` / `grid_ready` | Intermediate trading | No | No, not as a final report | No |
| 4 | `1$_Dollar_Bill` | `capital_allocation` / `allocation_ready` | Final upstream control artifact | Yes, for orchestration | Not as a user PDF/report package | No |
| 5 | `Jusetta` | `report_job` / `report_ready` | Final user-facing artifact | Yes | Yes | **Yes** |

**Normative rule:** `analysis_preview` не является `report_job` и не должен использовать те же имена, статусы publish или каналы доставки, которые предназначены для финального отчёта.

**Normative rule:** `report_job`, пользовательский PDF и любой финальный user-facing package запрещено публиковать, если не существует завершённого `allocation_ready` для того же `correlation_id`, окна и набора символов.

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

### 3. `analysis_ready`

**Meaning.** Аналитический слой для окна рассчитан и записан в curated tables / feature store. Это analysis-only результат, ещё не финальный user-facing report.

**Producer.** `analysis-engine`.

**Consumers.**

- `grid-engine` — основной потребитель;
- `analysis-preview-builder` — опциональный потребитель раннего preview;
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

### 4. `analysis_preview_ready`

**Meaning.** Опциональный ранний preview построен только на analysis-only результатах `Ben_Kim` и явно отделён от финального user-facing report.

**Producer.** `analysis-preview-builder` / `Jusetta-preview`.

**Consumers.**

- `Bobby Axe` — контроль маркировки preview;
- UI / API preview-channel;
- `audit-log`.

**Required payload.**

| Field | Description |
| --- | --- |
| `symbol` | Канонический инструмент или `portfolio` для пакетного preview. |
| `window_start_utc` | Начало окна анализа. |
| `window_end_utc` | Конец окна анализа. |
| `preview_id` | Стабильный идентификатор preview-артефакта. |
| `preview_version` | Версия шаблона/схемы preview. |
| `analysis_set_id` | Ссылка на upstream analysis-only result. |
| `artifact_uri` | URI preview-файла или объекта. |
| `generated_at_utc` | Время генерации. |
| `preview_label` | Обязательная метка `preview` / `draft`. |

**Idempotency key.**

`analysis_preview_ready:{symbol}:{window_start_utc}:{window_end_utc}:{preview_id}:{preview_version}`

**Gating rules.**

- это промежуточный артефакт;
- он может быть доставлен пользователю только через preview-channel и только с явной меткой draft/preview;
- событие не разблокирует `report_ready` и не заменяет `allocation_ready`.

### 5. `grid_ready`

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

### 6. `allocation_ready`

**Meaning.** Капитал распределён по готовому grid set и сохранён как детерминированный allocation result. Это обязательный upstream gate для финального `report_job`.

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

### 7. `report_ready`

**Meaning.** Финальный `report_job`, пользовательский PDF и metadata export для окна сформированы и доступны потребителям.

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
| `allocation_set_id` | Upstream allocation reference. Обязательное поле. |
| `artifact_uri` | URI файла, записи или export object. |
| `generated_at_utc` | Время генерации. |

**Idempotency key.**

`report_ready:{symbol}:{window_start_utc}:{window_end_utc}:{report_id}:{report_version}`

**Gating rules.**

- `report_ready` запрещено публиковать без валидного `allocation_set_id`;
- если для окна нет `allocation_ready`, событие должно быть отклонено как business violation, а не выпускаться как partial success;
- финальный user-facing PDF подпадает под те же ограничения, что и `report_ready`.

## Producer / consumer responsibility matrix

| Event | Producer | Primary consumer | Secondary consumers |
| --- | --- | --- | --- |
| `raw_data_ingested` | `raw-ingestion-service` | `second-bars-builder` | `pipeline-monitor`, `audit-log`, `backfill-coordinator` |
| `second_bars_ready` | `second-bars-builder` | `analysis-engine` | `quality-checker`, `pipeline-monitor` |
| `analysis_ready` | `analysis-engine` | `grid-engine` | `analysis-preview-builder`, `model-monitor`, `pipeline-monitor` |
| `analysis_preview_ready` | `analysis-preview-builder` | preview UI / API | `Bobby Axe`, `audit-log`, `pipeline-monitor` |
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
6. Для финального отчёта dedup должен дополнительно проверять, что `allocation_set_id` соответствует тому же `correlation_id` и окну.

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
- бизнес-версия результата неизвестна системе и не поддерживается;
- попытка выпустить `report_ready` без `allocation_ready` для того же окна.

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

### Safe ordering for historical ranges

Для диапазона `[from_utc, to_utc)` порядок должен быть таким:

1. raw ingestion / validation;
2. `raw_data_ingested`;
3. rebuild `second_bars` и публикация `second_bars_ready`;
4. recompute analysis и публикация `analysis_ready`;
5. опциональный `analysis_preview_ready`, если нужен ранний черновик;
6. recompute grid и публикация `grid_ready`;
7. recompute allocation и публикация `allocation_ready`;
8. recompute final reports и публикация `report_ready`.

Нельзя запускать downstream replay до подтверждения готовности upstream окна для того же `symbol` и времени.
Нельзя запускать `report_ready` без подтверждённого `allocation_ready`, даже если `analysis_preview_ready` уже существует.

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
6. Для `report_ready` consumer дополнительно валидирует наличие `allocation_ready` до смены статуса на `completed`.

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
6. Preview- и final-report артефакты должны храниться в разных префиксах, чтобы исключить смешение `analysis_preview` и `report_job`.
