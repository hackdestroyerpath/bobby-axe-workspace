# Contract: 1$_Dollar_Bill

## Назначение
Контракт описывает распределение капитала между тикерами на основании сеток `Maffi` и аналитики `Ben_Kim`.

## 1. Producer и consumer
- **Producers входа:** `Maffi`, `Ben_Kim`
- **Consumer входа / Producer выхода:** `1$_Dollar_Bill`
- **Consumers выхода:** `Jusetta`, процессы хранения `Jack`

## 2. Формат входа
Вход состоит из двух связанных наборов данных:
1. `grid_proposal` по каждому тикеру.
2. `analysis_result`, использованные как обоснование риска и приоритета.

**Схемы:**
- `contracts/schemas/grid_proposal.schema.json`
- `contracts/schemas/analysis_result.schema.json`

Требования к набору:
- по каждому `symbol` должен быть ровно один актуальный `grid_proposal` со статусом `ready`
- сумма итоговых аллокаций по всем тикерам должна равняться `100`

## 3. Формат выхода
Выходной объект называется `capital_allocation`.

**Схема:** `contracts/schemas/capital_allocation.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `capital_allocation`
- `allocation_id`
- `symbol`
- `proposal_id`
- `allocation_pct`
- `risk_bucket`: `low` | `medium` | `high`
- `rationale`
- `approved_at`
- `status`

## 4. Обязательные поля
- `event_type`
- `allocation_id`
- `symbol`
- `proposal_id`
- `allocation_pct`
- `risk_bucket`
- `rationale`
- `approved_at`
- `status`

## 5. Допустимые статусы ошибок
- `GRID_NOT_FOUND` — отсутствует сетка по тикеру
- `ANALYSIS_NOT_FOUND` — недоступны связанные аналитические выводы
- `ALLOCATION_SUM_MISMATCH` — сумма аллокаций не равна `100`
- `RISK_MODEL_FAILED` — ошибка модели риск-оценки
- `SCHEMA_VALIDATION_FAILED` — объект не прошёл валидацию
- `STORAGE_WRITE_FAILED` — не удалось сохранить результат
- `DUPLICATE_SYMBOL` — несколько аллокаций для одного тикера в одном батче

## 6. Таймфреймы
Входные данные могут ссылаться на аналитические таймфреймы:
- `1m`
- `5m`
- `60m`

Основанием для аллокации является `grid_proposal.frame = 5m`, но решение может учитывать сигналы из всех трёх таймфреймов.

## 7. Пример JSON-объекта
```json
{
  "event_type": "capital_allocation",
  "allocation_id": "alloc_BTCUSDC_20260321T121000Z",
  "symbol": "BTCUSDC",
  "proposal_id": "grid_BTCUSDC_20260321T120000Z",
  "allocation_pct": 27.5,
  "risk_bucket": "medium",
  "rationale": "Сетка подтверждена 5m и 60m сигналами, но волатильность остаётся повышенной.",
  "approved_at": "2026-03-21T12:10:00Z",
  "status": "ready",
  "supporting_analysis_ids": [
    "an_BTCUSDC_rsi_macd_20260321T120000Z_5m",
    "an_BTCUSDC_volume_profile_20260321T120000Z_60m"
  ]
}
```
