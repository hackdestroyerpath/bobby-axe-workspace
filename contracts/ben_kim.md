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
- `status`: бизнес-статус пригодности результата (`ready` | `partial` | `rejected`)
- `result_code`: технический/операционный итог выполнения (`ok` | `skipped` | `insufficient_data` | `error`)

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
- `result_code`

## 5. Каноническая модель статусов
`analysis_result` хранит два независимых, но согласованных слоя статуса:

### 5.1 `status` — бизнес-статус пригодности
- `ready` — результат можно использовать downstream как валидную аналитику.
- `partial` — результат можно хранить, логировать и показывать в отчётах, но нельзя напрямую использовать в торговом решении.
- `rejected` — результат отклонён из-за технической ошибки или невалидного выполнения и не может считаться входом для торговых решений.

### 5.2 `result_code` — технический итог выполнения
- `ok` — стратегия успешно отработала и вернула осмысленный результат.
- `skipped` — стратегия сознательно не запускалась или была пропущена по условиям применимости.
- `insufficient_data` — входных данных, истории или индикаторов недостаточно для вывода.
- `error` — выполнение завершилось технической ошибкой.

### 5.3 Обязательное соответствие полей
- `status=ready` допускается только вместе с `result_code=ok`.
- `status=partial` допускается только вместе с `result_code=skipped` или `result_code=insufficient_data`.
- `status=rejected` допускается только вместе с `result_code=error`.

## 6. Допустимые коды ошибок и причин
Эти значения используются в логах, `details`, алертах и операторской диагностике; они не заменяют `result_code`:
- `SYMBOL_NOT_FOUND` — тикер отсутствует в Data_collector
- `INSUFFICIENT_HISTORY` — недостаточно истории для стратегии
- `FRAME_NOT_SUPPORTED` — указан неподдерживаемый таймфрейм
- `STRATEGY_CONFIG_MISSING` — стратегия не настроена
- `SCHEMA_VALIDATION_FAILED` — выход не прошёл валидацию
- `ANALYSIS_TIMEOUT` — анализ не завершился в SLA
- `DEPENDENCY_UNAVAILABLE` — недоступны внешние зависимости, например новости
- `STORAGE_WRITE_FAILED` — не удалось сохранить результат

## 7. Таймфреймы
Поддерживаемые таймфреймы анализа:
- `1m`
- `5m`
- `60m`

Каждый `analysis_result` обязан содержать одно значение `frame` из списка выше.

## 8. Пример JSON-объекта
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
  "result_code": "ok",
  "details": {
    "rsi": 33.1,
    "macd_histogram": 12.4
  }
}
```
