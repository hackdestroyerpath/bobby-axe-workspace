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
  "http://127.0.0.1:8791/ticks?symbol=BTCUSDC&from=2026-03-23T00:00:00+00:00&to=2026-03-23T12:00:00+00:00&limit=500"
```

Поддерживаемые query-параметры:
- `symbol` — обязательно
- `from` — optional, ISO-8601
- `to` — optional, ISO-8601
- `limit` — optional, default `1000`, max `10000`

---

## Формат ответа `/ticks`

Примерно такой:

```json
{
  "client_id": "analyst_1",
  "nickname": "Analyst 1",
  "symbol": "BTCUSDC",
  "count": 2,
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

---

## Ошибки API

Типовые ответы:
- `401 missing_api_key`
- `401 invalid_or_revoked_api_key`
- `400 symbol is required`
- `400 invalid limit`
- `400 invalid datetime format; use ISO-8601`
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
