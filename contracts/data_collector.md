# Contract: Data Collector

## Назначение
Контракт описывает выходные данные `Jack/Data_collector`, которые публикуются в хранилище и используются следующими этапами пайплайна.

## 1. Producer и consumer
- **Producer:** `Jack / Data_collector`
- **Consumers:** `Ben_Kim`, `Jusetta`, служебные процессы валидации и хранения

## 2. Формат входа
Источник входа — поток сделок Binance по USDC-futures. Нормализованный входной объект называется `trade_tick`.

**Схема:** `contracts/schemas/trade_tick.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `trade_tick`
- `source`: источник данных, например `binance_futures_usdc`
- `symbol`: тикер, например `BTCUSDC`
- `trade_id`: уникальный идентификатор сделки в источнике
- `price`: цена сделки
- `quantity`: объём сделки
- `side`: `buy` | `sell`
- `trade_ts`: время сделки в UTC, RFC 3339
- `ingested_at`: время приёма в Data_collector

## 3. Формат выхода
Основной выходной объект — `second_bar`, агрегированный на 1 секунду, со встроенными OHLC для таймфреймов `1m`, `5m`, `60m`.

**Схема:** `contracts/schemas/second_bar.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `second_bar`
- `source`
- `symbol`
- `second_ts`: начало секунды в UTC
- `open`, `high`, `low`, `close`
- `volume`
- `trade_count`
- `bid_volume`
- `ask_volume`
- `timeframes.1m`
- `timeframes.5m`
- `timeframes.60m`
- `status`: `ready` | `partial`

## 4. Обязательные поля
### Для входа `trade_tick`
- `event_type`
- `source`
- `symbol`
- `trade_id`
- `price`
- `quantity`
- `side`
- `trade_ts`
- `ingested_at`

### Для выхода `second_bar`
- `event_type`
- `source`
- `symbol`
- `second_ts`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `trade_count`
- `timeframes`
- `status`

## 5. Допустимые статусы ошибок
- `SOURCE_UNAVAILABLE` — источник данных временно недоступен
- `AUTH_FAILED` — ошибка авторизации в источнике
- `SCHEMA_VALIDATION_FAILED` — входной или выходной JSON не прошёл валидацию
- `OUT_OF_ORDER_EVENT` — сделка пришла с недопустимо старым timestamp
- `DUPLICATE_TRADE_ID` — повторный `trade_id`
- `SYMBOL_NOT_ALLOWED` — тикер не входит в universe USDC futures
- `AGGREGATION_GAP` — не удалось собрать корректную секундную агрегацию
- `STORAGE_WRITE_FAILED` — ошибка записи в SQL/объектное хранилище

## 6. Таймфреймы
Поддерживаемые таймфреймы:
- `1m`
- `5m`
- `60m`

Все три таймфрейма обязательны в объекте `second_bar.timeframes`.

## 7. Пример JSON-объекта
### Пример `trade_tick`
```json
{
  "event_type": "trade_tick",
  "source": "binance_futures_usdc",
  "symbol": "BTCUSDC",
  "trade_id": "1844674407370",
  "price": 64250.5,
  "quantity": 0.018,
  "side": "buy",
  "trade_ts": "2026-03-21T12:00:00.182Z",
  "ingested_at": "2026-03-21T12:00:00.310Z"
}
```

### Пример `second_bar`
```json
{
  "event_type": "second_bar",
  "source": "binance_futures_usdc",
  "symbol": "BTCUSDC",
  "second_ts": "2026-03-21T12:00:00Z",
  "open": 64249.8,
  "high": 64251.0,
  "low": 64248.9,
  "close": 64250.5,
  "volume": 2.347,
  "trade_count": 41,
  "bid_volume": 1.102,
  "ask_volume": 1.245,
  "status": "ready",
  "timeframes": {
    "1m": {"open": 64210.0, "high": 64280.4, "low": 64198.3, "close": 64250.5},
    "5m": {"open": 64120.4, "high": 64310.0, "low": 64095.1, "close": 64250.5},
    "60m": {"open": 63680.0, "high": 64310.0, "low": 63520.5, "close": 64250.5}
  }
}
```
