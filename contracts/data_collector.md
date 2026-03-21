# Contract: Data Collector

## Назначение
Контракт описывает выходные данные `Jack/Data_collector`, которые публикуются в хранилище и используются следующими этапами пайплайна.

## 1. Producer и consumer
- **Producer:** `Jack / Data_collector`
- **Consumers:** `Ben_Kim`, `Jusetta`, служебные процессы валидации и хранения

## 2. Canonical vocabulary decision

Для `Data_collector` принимается тот же канонический словарь, что и для общей модели данных:

- использовать `event_time_utc`, а не `trade_ts`;
- использовать `quantity`, а не `qty`;
- использовать `ts_second_utc`, а не `second_ts`;
- использовать `base_volume`, `buy_volume`, `sell_volume`, а не `volume`, `bid_volume`, `ask_volume`.

Отдельно фиксируется, что `buy_volume` и `sell_volume` — это **агрессорные объёмы исполненных сделок**, и они **не эквивалентны** терминам `bid_volume` / `ask_volume`, которые в других системах могут обозначать объёмы пассивной ликвидности в стакане.

## 3. Формат входа
Источник входа — поток сделок Binance по USDC-futures. Нормализованный входной объект называется `trade_tick`.

**Схема:** `contracts/schemas/trade_tick.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `trade_tick`
- `source`: источник данных, например `binance_futures_usdc`
- `symbol`: тикер, например `BTCUSDC`
- `trade_id`: уникальный идентификатор сделки в источнике
- `price`: цена сделки
- `quantity`: объём сделки в базовом активе
- `side`: `buy` | `sell`
- `event_time_utc`: время сделки в UTC, RFC 3339
- `ingested_at_utc`: время приёма в Data_collector

## 4. Формат выхода
Основной выходной объект — `second_bar`, агрегированный на 1 секунду, со встроенными OHLC для таймфреймов `1m`, `5m`, `60m`.

**Схема:** `contracts/schemas/second_bar.schema.json`

Поля верхнего уровня:
- `event_type`: всегда `second_bar`
- `source`
- `symbol`
- `ts_second_utc`: начало секунды в UTC
- `open`, `high`, `low`, `close`
- `base_volume`
- `trade_count`
- `buy_volume`
- `sell_volume`
- `timeframes.1m`
- `timeframes.5m`
- `timeframes.60m`
- `status`: `ready` | `partial`

## 5. Storage fields vs transport fields

В текущем контракте transport fields и storage fields синхронизированы и используют **одни и те же канонические имена**. Это сделано специально, чтобы JSON-события, документация и таблицы не расходились по терминологии.

Legacy-имена допускаются только как временные входные алиасы во внутренних адаптерах совместимости и не должны использоваться в новых схемах, документации и конфигах.

| Семантика | Storage field | Transport field | Legacy alias | Notes |
| --- | --- | --- | --- | --- |
| Время сделки | `event_time_utc` | `event_time_utc` | `trade_ts` | UTC business timestamp |
| Количество сделки | `quantity` | `quantity` | `qty` | Base-asset size |
| Секундный бакет | `ts_second_utc` | `ts_second_utc` | `second_ts` | Start of second in UTC |
| Общий объём секунды | `base_volume` | `base_volume` | `volume` | Total traded base volume |
| Агрессорный объём покупок | `buy_volume` | `buy_volume` | `bid_volume` | Not order-book bid liquidity |
| Агрессорный объём продаж | `sell_volume` | `sell_volume` | `ask_volume` | Not order-book ask liquidity |

## 6. Обязательные поля
### Для входа `trade_tick`
- `event_type`
- `source`
- `symbol`
- `trade_id`
- `price`
- `quantity`
- `side`
- `event_time_utc`
- `ingested_at_utc`

### Для выхода `second_bar`
- `event_type`
- `source`
- `symbol`
- `ts_second_utc`
- `open`
- `high`
- `low`
- `close`
- `base_volume`
- `trade_count`
- `buy_volume`
- `sell_volume`
- `timeframes`
- `status`

## 7. Допустимые статусы ошибок
- `SOURCE_UNAVAILABLE` — источник данных временно недоступен
- `AUTH_FAILED` — ошибка авторизации в источнике
- `SCHEMA_VALIDATION_FAILED` — входной или выходной JSON не прошёл валидацию
- `OUT_OF_ORDER_EVENT` — сделка пришла с недопустимо старым timestamp
- `DUPLICATE_TRADE_ID` — повторный `trade_id`
- `SYMBOL_NOT_ALLOWED` — тикер не входит в universe USDC futures
- `AGGREGATION_GAP` — не удалось собрать корректную секундную агрегацию
- `STORAGE_WRITE_FAILED` — ошибка записи в SQL/объектное хранилище

## 8. Таймфреймы
Поддерживаемые таймфреймы:
- `1m`
- `5m`
- `60m`

Все три таймфрейма обязательны в объекте `second_bar.timeframes`.

## 9. Пример JSON-объекта
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
  "event_time_utc": "2026-03-21T12:00:00.182Z",
  "ingested_at_utc": "2026-03-21T12:00:00.310Z"
}
```

### Пример `second_bar`
```json
{
  "event_type": "second_bar",
  "source": "binance_futures_usdc",
  "symbol": "BTCUSDC",
  "ts_second_utc": "2026-03-21T12:00:00Z",
  "open": 64249.8,
  "high": 64251.0,
  "low": 64248.9,
  "close": 64250.5,
  "base_volume": 2.347,
  "trade_count": 41,
  "buy_volume": 1.245,
  "sell_volume": 1.102,
  "status": "ready",
  "timeframes": {
    "1m": {"open": 64210.0, "high": 64280.4, "low": 64198.3, "close": 64250.5},
    "5m": {"open": 64120.4, "high": 64310.0, "low": 64095.1, "close": 64250.5},
    "60m": {"open": 63680.0, "high": 64310.0, "low": 63520.5, "close": 64250.5}
  }
}
```
