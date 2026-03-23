# new_collector — API access guide

## Что это за проект

`new_collector` — это минимальный сервис сбора и выдачи тиковых данных.

Что он делает:
- забирает live tick/aggTrade поток из Binance Futures (USDC)
- пишет данные в Postgres (`collector_v2.tick_trade`)
- умеет делать backfill / continuity / retention
- отдаёт тики через простой HTTP API
- ограничивает доступ через `X-API-Key`
- пишет лог обращений к API в БД

Текущий API-эндпоинт:
- `GET /health`
- `GET /ticks`

---

## Что нужно для доступа

Нужны 3 вещи:
1. доступный инстанс API-сервера `new_collector`
2. активный `API key`
3. доступ к базе PostgreSQL для самого сервиса

Пользователь API **не обязан** иметь прямой доступ к Postgres.
Postgres нужен самому сервису, потому что он читает/пишет данные туда.

---

## Переменные окружения

Пример `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/data_collector_v2
BINANCE_REST_BASE_URL=https://fapi.binance.com
BINANCE_WS_BASE_URL=wss://fstream.binance.com/stream
SYMBOLS=BTCUSDC,ETHUSDC
RETENTION_DAYS=3
```

Главное:
- `DATABASE_URL` — строка подключения к Postgres
- `SYMBOLS` — список инструментов через запятую
- `RETENTION_DAYS` — окно хранения данных

---

## Подготовка базы

Нужно применить схему:

```bash
psql "$DATABASE_URL" -f new_collector/sql/001_init.sql
```

Это создаст:
- `collector_v2.tick_trade`
- `collector_v2.api_client`
- `collector_v2.api_access_log`
- `collector_v2.system_checkpoint`

---

## Установка зависимостей

```bash
pip install -r new_collector/requirements.txt
```

---

## Основные режимы запуска

### 1) Live collector

```bash
cd new_collector
python main.py live
```

### 2) Backfill

```bash
cd new_collector
python main.py backfill
```

### 3) Continuity check/fill

```bash
cd new_collector
python main.py continuity
```

### 4) Retention cleanup

```bash
cd new_collector
python main.py retention
```

### 5) HTTP API

```bash
cd new_collector
python api.py --host 127.0.0.1 --port 8791
```

Если нужен внешний доступ, меняют host/port и отдельно настраивают firewall / reverse proxy.

---

## Как выдать API key

Ключ выдаётся через registry CLI:

```bash
cd new_collector
python clients.py issue --client-id analyst_1 --nickname "Analyst 1" --note "read access"
```

На stdout вернётся **сырой API key**.
Сохранять его нужно сразу: в базе лежит только `sha256`-хеш ключа.

Отозвать ключ:

```bash
cd new_collector
python clients.py revoke --client-id analyst_1
```

---

## Как ходить в API

### Healthcheck

```bash
curl http://127.0.0.1:8791/health
```

### Получить тики

```bash
curl \
  -H "X-API-Key: YOUR_API_KEY" \
  "http://127.0.0.1:8791/ticks?symbol=BTCUSDC&limit=100"
```

### Получить тики за диапазон

```bash
curl \
  -H "X-API-Key: YOUR_API_KEY" \
  "http://127.0.0.1:8791/ticks?symbol=BTCUSDC&from=2026-03-23T00:00:00Z&to=2026-03-23T12:00:00Z&limit=500"
```

### Получить следующую страницу `/ticks`

```bash
curl \
  -H "X-API-Key: YOUR_API_KEY" \
  "http://127.0.0.1:8791/ticks?symbol=BTCUSDC&from=2026-03-23T00:00:00+00:00&to=2026-03-23T12:00:00+00:00&limit=500&cursor_event_time=2026-03-23T11:59:58Z&cursor_trade_id=987654321"
```

Поддерживаемые query-параметры:
- `symbol` — обязательно
- `from` — optional, ISO-8601 datetime with timezone offset; UTC only (`+00:00` or `Z`)
- `to` — optional, ISO-8601 datetime with timezone offset; UTC only (`+00:00` or `Z`)
- `limit` — optional, default `1000`, max `10000`
- `cursor_event_time` — optional, ISO-8601 datetime with timezone offset; UTC only (`+00:00` or `Z`); используется только вместе с `cursor_trade_id`
- `cursor_trade_id` — optional; используется только вместе с `cursor_event_time`

---

## Формальные правила чтения `/ticks`

### Источник данных

Сервер читает тики только из `collector_v2.tick_trade`.

### Границы окна

Параметры `from`, `to` и `cursor_event_time` принимаются только в ISO-8601 с timezone offset.
Разрешён только UTC: используйте суффикс `Z` или offset `+00:00`.
Naive datetime без offset сервер отклоняет с `400` и ошибкой `datetime must include UTC offset`.

Если переданы `from` и/или `to`, сервер сначала нормализует их к UTC и затем использует **inclusive**-границы:
- `event_time_utc >= from`
- `event_time_utc <= to`

Это поведение не меняется между первой и последующими страницами.
Cursor добавляет только отсечение уже прочитанной части окна.

### Server-side sort order

Страница `/ticks` формируется в строгом порядке:

```sql
ORDER BY event_time_utc DESC, trade_id DESC
```

То есть сервер отдаёт записи от более новых к более старым.

### Stable tie-break

Если несколько сделок имеют одинаковый `event_time_utc`, сервер обязан разруливать порядок по `trade_id`.
Это делает выдачу детерминированной и защищает pagination от дублей/пропусков на одинаковых timestamp.

### Pagination model

Когда окно содержит больше строк, чем `limit`, клиент должен читать страницы последовательно.

Правило перехода на следующую страницу такое:
- взять последнюю запись текущей страницы;
- использовать её `event_time_utc` как `cursor_event_time`;
- использовать её `trade_id` как `cursor_trade_id`;
- повторить тот же запрос с теми же `symbol`, `from`, `to`, `limit` и добавить cursor-пару.

Серверная логика следующей страницы эквивалентна условию:

```sql
AND (event_time_utc, trade_id) < (:cursor_event_time, :cursor_trade_id)
```

Именно strict `<` гарантирует, что последняя запись предыдущей страницы не повторится на следующей.

### Клиентская нормализация порядка

`/ticks` оптимизирован под стабильную pagination и поэтому отдаёт страницы в descending order.

После загрузки всех нужных страниц клиент **обязан** нормализовать итоговую последовательность в ascending order:

```sql
ORDER BY event_time_utc ASC, trade_id ASC
```

Именно ascending sequence считается каноническим порядком для расчётов, ресемплинга, candle build и любых downstream-алгоритмов.

---

## Формат ответа `/ticks`

Примерно такой:

```json
{
  "client_id": "analyst_1",
  "nickname": "Analyst 1",
  "symbol": "BTCUSDC",
  "count": 2,
  "server_order": ["event_time_utc DESC", "trade_id DESC"],
  "canonical_client_order": ["event_time_utc ASC", "trade_id ASC"],
  "next_page": {
    "cursor_event_time": "2026-03-23 12:00:01+00:00",
    "cursor_trade_id": "123"
  },
  "rows": [
    {
      "source": "binance_futures_usdc",
      "symbol": "BTCUSDC",
      "trade_id": "123",
      "event_time_utc": "2026-03-23T12:00:01+00:00",
      "price": "84500.1",
      "quantity": "0.010",
      "side": "buy",
      "ingested_at_utc": "2026-03-23T12:00:02+00:00"
    }
  ]
}
```

Пояснения:
- `count` — количество строк в текущей странице
- `server_order` — фактический серверный порядок выдачи страницы
- `canonical_client_order` — порядок, в который клиент должен привести объединённый набор после pagination
- `next_page` — cursor для следующего запроса; если `null`, сервер не смог подтвердить наличие следующей страницы в рамках текущего окна
- `rows` — сами тики в серверном descending order

Практическое правило клиента:
1. читать страницы в порядке, который отдаёт сервер;
2. накапливать все `rows`;
3. после завершения pagination пересортировать массив в `event_time_utc ASC, trade_id ASC`.

---

## Ошибки API

Типовые ответы:
- `401 missing_api_key`
- `401 invalid_or_revoked_api_key`
- `400 symbol is required`
- `400 invalid limit`
- `400 invalid datetime format; use ISO-8601`
- `400 datetime must include UTC offset`
- `400 cursor_event_time and cursor_trade_id must be provided together`
- `404 not_found`

---

## Безопасность

Минимальные правила:
- не коммитить реальные ключи в git
- не передавать `DATABASE_URL` и API keys в публичные чаты
- по возможности держать API за reverse proxy / VPN / firewall
- если ключ утёк — сразу `revoke` и выдать новый
- если API открыт наружу, лучше добавить rate limiting на уровне прокси

---

## Кратко по архитектуре

Поток такой:
1. `live.py` слушает Binance WebSocket
2. `db.py` пишет тики в Postgres
3. `api.py` читает тики из Postgres
4. `clients.py` управляет API-ключами
5. `api_access_log` хранит журнал обращений

То есть `new_collector` — это не аналитика и не стратегия, а базовый слой сбора и controlled-read доступа к тиковым данным.
