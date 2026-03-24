# COLLECTOR_ACCESS_INSTRUCTION

## Purpose
Единая инструкция подключения к `new_collector` для downstream-агентов, в первую очередь:
- `Ben_Kim`
- `Maffi`

Этот документ описывает только controlled-read доступ к collector data.

---

## 1. Canonical endpoint
Collector read contour:
- base URL: `http://127.0.0.1:8791`
- health: `GET /health`
- data read: `GET /ticks`

---

## 2. Auth model
Доступ к `/ticks` идёт только через header:
- `X-API-Key: <raw_machine_key>`

### Hard rule
- каждый machine branch использует свой machine-specific key
- raw key не печатать
- raw key не класть в response/logs/reports

---

## 3. Binding model
Используется canonical binding:
- `machine_id -> client_id -> api_key_id -> env_var`

Пример:
- `machine_id = rsi_macd_1m`
- `client_id = rsi_macd_1m__collector_reader`
- `api_key_id = collector-rsi_macd_1m`
- `env_var = COLLECTOR_KEY_RSI_MACD_1M`

Binding artifact:
- `TRADING_ALGOS/secrets/benkim_runtime_binding.tsv`

---

## 4. Runtime loading rule
Agent должен:
1. взять свой `machine_id`
2. найти binding row
3. получить `env_var`
4. прочитать raw key из runtime env
5. использовать key только в collector request

### Example runtime load
```bash
set -a
. /path/to/runtime_machine_env.env
set +a
```

---

## 5. Minimal request example
```bash
curl \
  -H "X-API-Key: ${COLLECTOR_KEY_RSI_MACD_1M}" \
  "http://127.0.0.1:8791/ticks?symbol=BTCUSDC&limit=5"
```

---

## 6. Expected response facts
Нормальный успешный ответ содержит:
- `client_id`
- `symbol`
- `count`
- `rows`
- `next_page`
- `server_order`
- `canonical_client_order`

---

## 7. Traceability rule
В downstream output/logics сохранять только:
- `machine_id`
- `client_id`
- `api_key_id`

Никогда не сохранять:
- raw key
- env dump
- полный secrets file

---

## 8. Query rules
Поддерживаемые query-параметры `/ticks`:
- `symbol` — required
- `from` — optional UTC datetime
- `to` — optional UTC datetime
- `limit` — optional
- `cursor_event_time` — optional
- `cursor_trade_id` — optional

### Important
- datetime только UTC
- pagination должна использовать server contract
- source-of-truth — `collector_v2.tick_trade`

---

## 9. Failure handling
### 401
- missing/invalid key

### 400
- invalid request params

### connect failure
- service layer not available on `127.0.0.1:8791`

### Hard rule
Если collector API недоступен, не подменять это выдуманным data success.

---

## 10. Operational summary
- collector access только по ключу
- machine-bound reads only
- raw secrets не светятся
- traceability обязательна
- Ben_Kim и Maffi используют одинаковый collector read contour
