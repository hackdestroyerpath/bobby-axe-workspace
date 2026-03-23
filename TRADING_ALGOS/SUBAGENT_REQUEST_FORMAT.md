# SUBAGENT REQUEST FORMAT

Ниже единый request schema для всех 12 субагентов: 4 стратегии × 3 таймфрейма.

## JSON schema
См. `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json`.

## Обязательные поля
- `request_id` — сквозной id запроса от оркестратора.
- `agent_id` — целевой id машины, которая должна обработать запрос.
- `strategy` — одна из стратегий: `RSI_MACD`, `LEVELS_FIBO_HV`, `VOLUME`, `ELLIOTT`.
- `timeframe` — один из таймфреймов: `1m`, `5m`, `60m`.
- `symbol` — инструмент, например `BTCUSDC`.
- `source` — upstream-источник данных / collector.
- `requested_at` — время постановки запроса в ISO-8601.
- `input_window.from` / `input_window.to` — рабочее окно данных, которое машина должна обработать.
- `response_contract_version` — какая версия общего response contract ожидается в ответе.
- `source_contract_version` — какая версия общего тик-контракта использовалась оркестратором.

## Опциональные поля
- `options.include_incomplete_candle` — можно ли включать незавершённую последнюю свечу.
- `options.strict_mode` — если `true`, машина должна предпочесть `status=error`, а не деградированный partial-ответ, когда критичный вход отсутствует.

## Минимальный пример
```json
{
  "request_id": "req-2026-03-23T10:15:00Z-rsi5m-01",
  "agent_id": "rsi_macd_5m_01",
  "strategy": "RSI_MACD",
  "timeframe": "5m",
  "symbol": "BTCUSDC",
  "source": "Data_collector",
  "requested_at": "2026-03-23T10:15:00Z",
  "input_window": {
    "from": "2026-03-23T06:00:00Z",
    "to": "2026-03-23T10:15:00Z"
  },
  "response_contract_version": "v1",
  "source_contract_version": "tick-source-v1",
  "options": {
    "include_incomplete_candle": false,
    "strict_mode": false
  }
}
```
