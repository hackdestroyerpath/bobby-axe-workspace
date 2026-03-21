# Contract: Jusetta

## Назначение
Контракт описывает два разных класса артефактов `Jusetta`:
1. **Опциональный промежуточный `analysis_preview`** — ранний черновик только на analysis-only данных `Ben_Kim`.
2. **Канонический финальный `report_job`** — полный report package: PDF-отчёт `Jusetta`, табличный экспорт, отдельный executive summary от `Bobby Axe` и manifest-файл, которые относятся к одному `correlation_id` и одному `report_period`.

Эти классы артефактов нельзя смешивать: `analysis_preview` не является `report_job`, а `report_job` не может быть выпущен до появления аллокаций от `1$_Dollar_Bill`.

## 1. Producer и consumer
- **Producers входа для `analysis_preview`:** `Jack / Data_collector`, `Ben_Kim`
- **Producers входа для `report_job`:** `Jack / Data_collector`, `Ben_Kim`, `Maffi`, `1$_Dollar_Bill`, `Bobby Axe`
- **Consumer входа / Producer выхода:** `Jusetta`
- **Consumers выхода:** `Bobby Axe`, пользователь, внешние каналы доставки отчётов, архив/аудит

## 2. Формат входа
### Для `analysis_preview`
`Jusetta` читает только:
- `analysis_result` от `Ben_Kim`;
- при необходимости `second_bar` для опорных рыночных метрик;
- параметры preview: период, список `symbols`, `correlation_id`, preview-channel.

### Для `report_job`
`Jusetta` читает уже сохранённые объекты:
- `second_bar` — для опорных рыночных метрик;
- `analysis_result`;
- `grid_proposal`;
- `capital_allocation`;
- executive summary от `Bobby Axe`, который остаётся отдельным артефактом и одновременно встраивается в PDF.

**Схемы:**
- `contracts/schemas/second_bar.schema.json`
- `contracts/schemas/analysis_result.schema.json`
- `contracts/schemas/grid_proposal.schema.json`
- `contracts/schemas/capital_allocation.schema.json`
- `contracts/schemas/report_job.schema.json`

## 3. Формат выхода
### 3.1. Промежуточный `analysis_preview`
`analysis_preview` описывает ранний черновик и не должен masquerade as финальный report package.

Обязательные свойства preview-артефакта:
- `event_type`: всегда `analysis_preview`;
- `preview_id`;
- `correlation_id`;
- `generated_at_utc`;
- `report_period`;
- `symbols`;
- `artifact_path`;
- `status`: `ready` | `rejected` | `error`;
- `label`: всегда `preview` или `draft`.

### 3.2. Финальный `report_job`
Выходной объект называется `report_job` и описывает полный package выпуска, а не только очередь на рендер.

**Схема:** `contracts/schemas/report_job.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `report_job`;
- `job_id`;
- `correlation_id` — общий идентификатор для PDF, таблицы, summary и manifest;
- `report_type` — `live_snapshot` | `periodic_report` | `exception_report` | `portfolio_allocation_report`;
- `requested_at`;
- `generated_at_utc` — время сборки package в UTC;
- `report_period`;
- `symbols`;
- `artifacts`;
- `delivery`;
- `status`;
- опционально `pipeline_status` и `decision`.

## 4. Обязательные поля
### 4.1. Для `analysis_preview`
- `event_type`
- `preview_id`
- `correlation_id`
- `generated_at_utc`
- `report_period.from`
- `report_period.to`
- `symbols`
- `artifact_path`
- `status`
- `label`

### 4.2. Для `report_job`
- `event_type`
- `job_id`
- `correlation_id`
- `report_type`
- `requested_at`
- `generated_at_utc`
- `report_period.from`
- `report_period.to`
- `symbols`
- `delivery.channel`
- `status`

### Артефакты package
- `artifacts.pdf_path`
- `artifacts.table_path`
- `artifacts.summary_path`
- `artifacts.manifest_path`

`summary_path` обязателен, потому что executive summary `Bobby Axe` остаётся самостоятельным артефактом пакета, даже если тот же текст встроен в PDF. `manifest_path` обязателен, потому что manifest является канонической точкой трассировки состава выпуска.

## 5. Канонические статусы `Jusetta`
### Для `analysis_preview`
Единый enum `analysis_preview.status`:
- `ready` — preview сформирован и записан;
- `rejected` — preview остановлен по бизнес-причине;
- `error` — preview остановлен по технической причине.

**Previewability:** `analysis_preview` остаётся промежуточным артефактом. Его можно отправлять пользователю только как явно маркированный preview/черновик.

### Для `report_job`
Единый enum для `report_job.status`:
- `queued` — package зарегистрирован, но сборка ещё не началась;
- `running` — `Jusetta` собирает артефакты или записывает их в storage;
- `ready` — все обязательные артефакты package сформированы и записаны по путям из `artifacts.*`;
- `rejected` — выпуск остановлен по бизнес-причине: неполный upstream, несогласованное окно, невозможность безопасной публикации;
- `error` — выпуск остановлен по технической причине: рендер, storage, шаблон, delivery и т.п.

**Publishable-статус:** только `status = ready` считается publishable для финального пользовательского package. Если дополнительно задан `decision`, то:
- `decision = publish` — полноценный publishable release;
- `decision = informational_only` — package можно доставлять пользователю, но нельзя трактовать как торгово-исполняемый выпуск;
- `decision = revision_required` или `escalate` — пакет не должен считаться publishable, даже если артефакты частично успели сохраниться.

## 6. Gating rules и аллокации
- `analysis_preview` является **промежуточным** артефактом.
- `report_job` и пользовательский PDF являются **финальными** артефактами.
- `analysis_preview` может быть отправлен пользователю только как preview/draft.
- `report_job` и пользовательский PDF могут быть отправлены пользователю только после завершения `Maffi` и `1$_Dollar_Bill`.
- При отсутствии `capital_allocation` для того же `correlation_id`, окна и символов должны быть заблокированы:
  - `report_job`;
  - `artifacts.pdf_path`;
  - любой финальный канал доставки пользователю.

Нормативное правило: отсутствие аллокаций — это business block (`rejected`), а не допустимый partial success для финального report package.

## 7. Опциональные управленческие поля
- `pipeline_status` — агрегированная готовность upstream-цепочки: `ready` | `partial` | `blocked`.
- `decision` — управленческий итог от `Bobby Axe`: `publish` | `informational_only` | `revision_required` | `escalate`.

Если эти поля присутствуют, они должны быть согласованы с содержимым executive summary и manifest.

## 8. Обязательное содержимое manifest
Manifest, на который ссылается `artifacts.manifest_path`, обязан перечислять как минимум:
- `report_type`;
- `job_id`;
- `correlation_id`;
- `generated_at_utc`;
- `report_period.from` и `report_period.to`;
- `symbols`;
- `status`;
- `allocation_set_id` или эквивалентную ссылку на подтверждённые аллокации;
- опционально `pipeline_status` и `decision`;
- список артефактов с типом, путём, producer и checksum.

Минимальный список `artifact.kind` внутри manifest:
- `pdf` — основной PDF от `Jusetta`;
- `table` — табличный экспорт;
- `summary` — отдельный executive summary от `Bobby Axe`;
- `manifest` — сам manifest.

Если выпускается `analysis_preview`, он должен жить отдельно и не подменять manifest финального package.

## 9. Допустимые статусы ошибок
- `UPSTREAM_DATA_MISSING` — отсутствуют данные одного из этапов;
- `PDF_RENDER_FAILED` — не удалось собрать PDF;
- `TABLE_EXPORT_FAILED` — не удалось сформировать табличный артефакт;
- `SUMMARY_ARTIFACT_MISSING` — не получен обязательный executive summary от `Bobby Axe`;
- `MANIFEST_WRITE_FAILED` — не удалось записать manifest;
- `TEMPLATE_NOT_FOUND` — отсутствует шаблон отчёта;
- `DELIVERY_FAILED` — не удалось доставить отчёт пользователю;
- `SCHEMA_VALIDATION_FAILED` — объект задания не прошёл валидацию;
- `STORAGE_WRITE_FAILED` — не удалось сохранить артефакты отчёта;
- `ALLOCATIONS_MISSING` — отсутствуют обязательные аллокации для финального `report_job`.

## 10. Таймфреймы
Отчёт обязан поддерживать агрегацию результатов, построенных на таймфреймах:
- `1m`
- `5m`
- `60m`

Для итоговой таблицы допускается сводка по тикеру, но в источниках и manifest должны сохраняться ссылки на исходные таймфреймы и upstream-артефакты.

## 11. Пример JSON-объекта финального `report_job`
```json
{
  "event_type": "report_job",
  "job_id": "report_20260321T121500Z",
  "correlation_id": "corr-8f3a",
  "report_type": "periodic_report",
  "requested_at": "2026-03-21T12:15:00Z",
  "generated_at_utc": "2026-03-21T12:16:02Z",
  "report_period": {
    "from": "2026-03-21T11:00:00Z",
    "to": "2026-03-21T12:15:00Z"
  },
  "symbols": ["BTCUSDC", "ETHUSDC"],
  "artifacts": {
    "pdf_path": "reports/periodic_report/2026/03/21/corr-8f3a/pdf__periodic_report__20260321T110000Z__20260321T121500Z__universe-2__corr-8f3a__v1.pdf",
    "table_path": "reports/periodic_report/2026/03/21/corr-8f3a/table__periodic_report__20260321T110000Z__20260321T121500Z__universe-2__corr-8f3a__v1.csv",
    "summary_path": "reports/periodic_report/2026/03/21/corr-8f3a/summary__periodic_report__20260321T110000Z__20260321T121500Z__universe-2__corr-8f3a__v1.md",
    "manifest_path": "reports/periodic_report/2026/03/21/corr-8f3a/manifest__periodic_report__20260321T110000Z__20260321T121500Z__universe-2__corr-8f3a__v1.json"
  },
  "delivery": {
    "channel": "user_download",
    "recipient": "primary_user"
  },
  "status": "ready",
  "pipeline_status": "ready",
  "decision": "publish"
}
```
