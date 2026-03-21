# Contract: Ben_Kim

## Назначение
Контракт описывает обмен данными между `Data_collector` и аналитическим агентом `Ben_Kim`.

## 1. Producer и consumer
- **Producer входа:** `Jack / Data_collector`
- **Consumer входа / Producer выхода:** `Ben_Kim`
- **Consumers выхода:** `Maffi`, `Jusetta`, процессы хранения `Jack`

## 2. Формат входа
`Ben_Kim` читает исторические и актуальные `second_bar` записи по тикеру.

**Схема:** `contracts/schemas/second_bar.schema.json`

Дополнительные требования к батчу:
- все записи в батче относятся к одному `symbol`
- данные содержат `timeframes.1m`, `timeframes.5m`, `timeframes.60m`
- записи отсортированы по `second_ts` по возрастанию

## 3. Формат выхода
Выходной объект называется `analysis_result`.

**Схема:** `contracts/schemas/analysis_result.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `analysis_result`
- `analysis_id`
- `symbol`
- `strategy`
- `frame`
- `signal`: `bullish` | `bearish` | `neutral` | `ignore`
- `conclusion`
- `confidence`
- `observed_at`
- `source_window`
- `status`

## 4. Обязательные поля
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

## 5. Допустимые статусы ошибок
- `SYMBOL_NOT_FOUND` — тикер отсутствует в Data_collector
- `INSUFFICIENT_HISTORY` — недостаточно истории для стратегии
- `FRAME_NOT_SUPPORTED` — указан неподдерживаемый таймфрейм
- `STRATEGY_CONFIG_MISSING` — стратегия не настроена
- `SCHEMA_VALIDATION_FAILED` — выход не прошёл валидацию
- `ANALYSIS_TIMEOUT` — анализ не завершился в SLA
- `DEPENDENCY_UNAVAILABLE` — недоступны внешние зависимости, например новости
- `STORAGE_WRITE_FAILED` — не удалось сохранить результат

## 6. Таймфреймы
Поддерживаемые таймфреймы анализа:
- `1m`
- `5m`
- `60m`

Каждый `analysis_result` обязан содержать одно значение `frame` из списка выше.

## 7. Пример JSON-объекта
```json
{
  "event_type": "analysis_result",
  "analysis_id": "an_BTCUSDC_rsi_macd_20260321T120000Z_5m",
  "symbol": "BTCUSDC",
  "strategy": "rsi_macd",
  "frame": "5m",
  "signal": "bullish",
  "conclusion": "RSI вышел из зоны перепроданности, MACD подтверждает разворот вверх.",
  "confidence": 0.74,
  "observed_at": "2026-03-21T12:00:00Z",
  "source_window": {
    "from": "2026-03-21T11:00:00Z",
    "to": "2026-03-21T12:00:00Z"
  },
  "status": "ready",
  "details": {
    "rsi": 33.1,
    "macd_histogram": 12.4
  }
}
```
