# Contract: Jusetta

## Назначение
Контракт описывает сбор финального отчёта из аналитики, сеток и аллокаций.

## 1. Producer и consumer
- **Producers входа:** `Jack / Data_collector`, `Ben_Kim`, `Maffi`, `1$_Dollar_Bill`
- **Consumer входа / Producer выхода:** `Jusetta`
- **Consumers выхода:** пользователь, внешние каналы доставки отчётов

## 2. Формат входа
`Jusetta` читает уже сохранённые объекты:
- `second_bar` — для опорных рыночных метрик
- `analysis_result`
- `grid_proposal`
- `capital_allocation`

**Схемы:**
- `contracts/schemas/second_bar.schema.json`
- `contracts/schemas/analysis_result.schema.json`
- `contracts/schemas/grid_proposal.schema.json`
- `contracts/schemas/capital_allocation.schema.json`

## 3. Формат выхода
Выходной объект называется `report_job` и описывает задание на сборку отчёта.

**Схема:** `contracts/schemas/report_job.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `report_job`
- `job_id`
- `requested_at`
- `report_period`
- `symbols`
- `artifacts`
- `delivery`
- `status`

## 4. Обязательные поля
- `event_type`
- `job_id`
- `requested_at`
- `report_period.from`
- `report_period.to`
- `symbols`
- `artifacts.pdf_path`
- `delivery.channel`
- `status`

## 5. Допустимые статусы ошибок
- `UPSTREAM_DATA_MISSING` — отсутствуют данные одного из этапов
- `PDF_RENDER_FAILED` — не удалось собрать PDF
- `TEMPLATE_NOT_FOUND` — отсутствует шаблон отчёта
- `DELIVERY_FAILED` — не удалось доставить отчёт пользователю
- `SCHEMA_VALIDATION_FAILED` — объект задания не прошёл валидацию
- `STORAGE_WRITE_FAILED` — не удалось сохранить артефакты отчёта

## 6. Таймфреймы
Отчёт обязан поддерживать агрегацию результатов, построенных на таймфреймах:
- `1m`
- `5m`
- `60m`

Для итоговой таблицы допускается сводка по тикеру, но в источниках должны сохраняться ссылки на исходные таймфреймы.

## 7. Пример JSON-объекта
```json
{
  "event_type": "report_job",
  "job_id": "report_20260321T121500Z",
  "requested_at": "2026-03-21T12:15:00Z",
  "report_period": {
    "from": "2026-03-21T11:00:00Z",
    "to": "2026-03-21T12:15:00Z"
  },
  "symbols": ["BTCUSDC", "ETHUSDC"],
  "artifacts": {
    "pdf_path": "reports/report_20260321T121500Z.pdf",
    "table_path": "reports/report_20260321T121500Z.csv"
  },
  "delivery": {
    "channel": "user_download",
    "recipient": "primary_user"
  },
  "status": "queued"
}
```
