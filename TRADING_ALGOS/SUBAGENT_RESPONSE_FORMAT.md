# SUBAGENT RESPONSE FORMAT

Ниже единый формат ответа, который должен отдавать любой из 12 субагентов.

```json
{
  "agent_id": "string",
  "strategy": "RSI_MACD | LEVELS_FIBO_HV | VOLUME | ELLIOTT",
  "timeframe": "1m | 5m | 60m",
  "symbol": "BTCUSDC",
  "source": "Data_collector",
  "requested_at": "ISO-8601",
  "as_of": "ISO-8601",
  "status": "ready | partial | error",
  "input_window": {
    "from": "ISO-8601",
    "to": "ISO-8601"
  },
  "features": {},
  "summary": {
    "state": "bullish | bearish | neutral | mixed | unclear",
    "strength": "weak | medium | strong",
    "confidence": "low | medium | high",
    "note": "short human-readable line"
  },
  "meta": {
    "data_points": 0,
    "build_version": "string",
    "api_key_id": "string",
    "machine_id": "string"
  },
  "errors": []
}
```

## Смысл полей
- `agent_id` — id конкретного субагента
- `strategy` — стратегия
- `timeframe` — таймфрейм
- `symbol` — инструмент
- `source` — источник данных
- `requested_at` — когда запросили
- `as_of` — на какой момент рассчитан ответ
- `status` — готовность ответа
- `input_window` — диапазон входных данных
- `features` — сами рассчитанные признаки стратегии
- `summary` — короткая сводка для оркестратора
- `meta` — техническая метаинформация
- `errors` — список ошибок, если есть
