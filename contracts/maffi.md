# Contract: Maffi

## Назначение
Контракт описывает генерацию параметров торговой сетки на основе результатов `Ben_Kim`.

## 1. Producer и consumer
- **Producer входа:** `Ben_Kim`
- **Consumer входа / Producer выхода:** `Maffi`
- **Consumers выхода:** `1$_Dollar_Bill`, `Jusetta`, процессы хранения `Jack`

## 2. Формат входа
Вход — массив объектов `analysis_result` по одному `symbol`.

**Схема:** `contracts/schemas/analysis_result.schema.json`

Требования к батчу:
- минимум один `analysis_result` для `1m`, `5m`, `60m`
- все записи имеют одинаковый `symbol`
- usable-входами считаются только записи с `status=ready` и `result_code=ok`
- записи со `status=partial` или `status=rejected` могут храниться в батче, но не могут использоваться для построения сетки

## 3. Формат выхода
Выходной объект называется `grid_proposal`.

**Схема:** `contracts/schemas/grid_proposal.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `grid_proposal`
- `proposal_id`
- `symbol`
- `frame`: всегда `5m`
- `direction`: `long` | `short`
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `sl`
- `tp`
- `rationale`
- `based_on`
- `status`

## 4. Обязательные поля
- `event_type`
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
- `based_on.analysis_ids`
- `status`

## 5. Допустимые статусы ошибок
- `ANALYSIS_NOT_FOUND` — нет usable-аналитики по обязательному таймфрейму
- `INCONSISTENT_SIGNALS` — usable-сигналы конфликтуют и не дают построить сетку
- `FRAME_NOT_SUPPORTED` — запрос сделан не для `5m`
- `RISK_LIMIT_EXCEEDED` — параметры сетки выходят за допустимые риски
- `SCHEMA_VALIDATION_FAILED` — выход не прошёл валидацию
- `CALCULATION_FAILED` — расчёт диапазона сетки завершился ошибкой
- `STORAGE_WRITE_FAILED` — ошибка сохранения

## 6. Таймфреймы
Поддерживаемые таймфреймы во входной аналитике:
- `1m`
- `5m`
- `60m`

Таймфрейм выходной сетки:
- `5m` — обязателен и единственный допустимый

## 7. Пример JSON-объекта
```json
{
  "event_type": "grid_proposal",
  "proposal_id": "grid_BTCUSDC_20260321T120000Z",
  "symbol": "BTCUSDC",
  "frame": "5m",
  "direction": "long",
  "grid_upper_price": 64520.0,
  "grid_lower_price": 64080.0,
  "grid_count": 8,
  "sl": 63940.0,
  "tp": 64780.0,
  "rationale": "Преобладают usable bullish-сигналы на 5m и 60m, ожидается восстановление от зоны спроса.",
  "based_on": {
    "analysis_ids": [
      "an_BTCUSDC_rsi_macd_20260321T120000Z_5m",
      "an_BTCUSDC_volume_profile_20260321T120000Z_60m"
    ],
    "signal_summary": {
      "bullish": 5,
      "bearish": 1,
      "neutral": 2,
      "ignore": 1
    }
  },
  "status": "ready"
}
```
