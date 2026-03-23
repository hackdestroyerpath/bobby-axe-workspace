# SUBAGENT RESPONSE FORMAT

Ниже единый response schema, который должен отдавать любой из 12 субагентов.

## JSON schema
См. `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`.

## Статусы
- `ready` — расчёт завершён, существенной деградации входа нет.
- `partial` — ответ можно использовать, но вход или расчёт деградировали; этот статус обязан согласовываться с `meta.is_partial = true`.
- `error` — полезный расчёт не собран; в `errors` должен быть минимум один объект ошибки.

## Поля верхнего уровня
- `agent_id` — id конкретного субагента.
- `strategy` — стратегия.
- `timeframe` — таймфрейм.
- `symbol` — инструмент.
- `source` — источник данных.
- `requested_at` — когда запросили.
- `as_of` — на какой момент рассчитан ответ.
- `response_contract_version` — версия общего response contract, по которому собран этот packet.
- `status` — итоговое состояние ответа: `ready`, `partial`, `error`.
- `input_window` — диапазон входных данных.
- `features` — рассчитанные признаки стратегии.
- `summary` — короткая сводка для оркестратора.
- `meta` — техническая метаинформация и quality flags.
- `errors` — список явных ошибок/аномалий.

## Поля `meta`
- `data_points` — сколько исходных datapoints реально попало в расчёт.
- `is_partial` — булев флаг деградированного, но всё ещё полезного ответа.
- `partial_reason` — короткая причина partial-режима. Обязательна, если `meta.is_partial = true` или `status = partial`.
- `coverage_ratio` — доля фактически покрытого входного окна в диапазоне `0..1`.
- `response_contract_version` живёт на верхнем уровне ответа и должен совпадать с ожидаемой версией из request.
- `source_contract_version` — версия входного source/tick contract, по которому реально работала машина.
- `build_version` — версия сборки / кода машины.
- `api_key_id` — технический id ключа/пула, если это нужно для трассировки доступа.
- `machine_id` — конкретная машина/инстанс.

## Согласованность `status` и `meta`
- `status = partial` => `meta.is_partial = true`.
- `meta.is_partial = true` => `status = partial`.
- Для partial-ответа `meta.partial_reason` обязателен и не должен быть пустым.
- `status = ready` => `meta.is_partial = false`, а `meta.partial_reason` должен быть `null` или отсутствовать по внутренней модели генерации.
- `status = error` => `errors` должен содержать хотя бы одну ошибку.

## Что хранить в `errors`, а что в `meta`
### В `meta`
Только состояние качества и контекста, которое помогает интерпретировать даже успешный или partial-ответ:
- неполное покрытие окна (`coverage_ratio < 1`);
- факт деградации (`is_partial`);
- краткая причина деградации (`partial_reason`);
- техническая трассировка версии контракта и сборки;
- количество реально использованных datapoints.

### В `errors`
Явные сбои, нарушения ожиданий и аномалии, которые нужно отдельно разбирать или ретраить:
- источник не ответил / ответил с ошибкой;
- не удалось построить обязательные свечи или признаки;
- обязательные поля ответа не собраны;
- сериализация / transport / output validation упали;
- любое событие, которому нужен `code`, `message`, `severity` и, при необходимости, `retryable`.

Практическое правило:
- если это деградация качества уже полученного результата, отражать в `meta`;
- если это отдельный сбой или нарушение pipeline, отражать в `errors`.

## Минимальный пример partial-ответа
```json
{
  "agent_id": "rsi_macd_5m_01",
  "strategy": "RSI_MACD",
  "timeframe": "5m",
  "symbol": "BTCUSDC",
  "source": "Data_collector",
  "requested_at": "2026-03-23T10:15:00Z",
  "as_of": "2026-03-23T10:15:02Z",
  "response_contract_version": "v1",
  "status": "partial",
  "input_window": {
    "from": "2026-03-23T06:00:00Z",
    "to": "2026-03-23T10:15:00Z"
  },
  "features": {},
  "summary": {
    "state": "mixed",
    "strength": "weak",
    "confidence": "low",
    "note": "Computed on incomplete input window"
  },
  "meta": {
    "data_points": 842,
    "is_partial": true,
    "partial_reason": "input_window_underfilled",
    "coverage_ratio": 0.71,
    "source_contract_version": "tick-source-v1",
    "build_version": "2026.03.23-1",
    "api_key_id": "collector-primary",
    "machine_id": "rsi_macd_5m_01"
  },
  "errors": [
    {
      "code": "INPUT_GAP_DETECTED",
      "message": "Gap detected inside requested input window",
      "severity": "warning",
      "scope": "input",
      "retryable": true
    }
  ]
}
```
