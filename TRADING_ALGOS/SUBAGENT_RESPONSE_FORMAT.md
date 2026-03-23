# SUBAGENT RESPONSE FORMAT

Ниже единый response schema, который должен отдавать любой из 12 субагентов.

## JSON schema
См. `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`.

## Статусы
- `ready` — расчёт завершён, существенной деградации входа нет.
- `partial` — ответ можно использовать, но вход или расчёт деградировали; этот статус обязан согласовываться с `meta.is_partial = true`.
- `error` — полезный расчёт не собран; в `errors` должен быть минимум один объект ошибки.

## Поля верхнего уровня
- `request_id` — сквозной id request, который делает machine response самодостаточным storage object для downstream packaging.
- `agent_id` — id конкретного субагента.
- `strategy` — стратегия.
- `timeframe` — таймфрейм.
- `symbol` — инструмент.
- `source` — источник данных.
- `requested_at` — когда запросили.
- `generated_at` — канонический timestamp сборки machine response. Для Phase 3 packaging это timestamp самого storage object. Поле `as_of` больше не используется, чтобы не смешивать время сборки packet и рыночный срез.
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

## Phase 3 packaging boundary
- Выбран контракт `one machine response = one storage object`.
- Поэтому machine response сам обязан нести `request_id` и `generated_at`.
- Downstream packaging не должен реконструировать identity из внешней пары `request + response`; он может полагаться на сам machine response как на полный object для storage/transport.
- `requested_at` остаётся traceability-временем исходного orchestration request.
- `generated_at` — единственный канонический timestamp ответа. Если downstream нужен market snapshot time, он должен брать его из `input_window.to` или отдельного будущего поля, но не переиспользовать `generated_at`.

## Канонический `errors.scope` для всей Phase 2
Во всей runtime/schema/docs используется единый набор scope:
- `input` — ошибка в самом request-контракте или в обязательных входных полях до чтения данных.
- `read` — деградация или сбой при чтении/сборе окна данных: retention, pagination drift, empty window, input gaps.
- `normalization` — сбой нормализации raw ticks в общий runtime format.
- `features` — сбой или остановка на этапе candle/features/strategy computation, включая insufficient warmup; код `FEATURE_ENGINE_FAILED` покрывает как failure общего candle/feature engine, так и failure strategy-specific compute после успешной сборки свечей.
- `output` — ошибка валидации/сборки response packet.
- `transport` — ошибка доставки уже собранного ответа наружу.

Практическая граница такая:
- invalid request => `input`;
- проблема с доступностью или полнотой фактических market data => `read`;
- проблема с преобразованием данных => `normalization`;
- проблема с расчётом признаков/стратегии => `features`;
- проблема с самим ответом => `output`;
- проблема с отправкой ответа => `transport`.

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
- request schema не прошёл обязательную проверку (`scope = input`);
- окно данных не дочиталось, упёрлось в retention или оказалось пустым (`scope = read`);
- нормализатор не смог собрать валидный tick stream (`scope = normalization`);
- не удалось построить обязательные свечи или признаки (`scope = features`);
- сериализация / output validation упали (`scope = output`);
- transport / delivery сломались (`scope = transport`).

Практическое правило:
- если это деградация качества уже полученного результата, отражать в `meta`;
- если это отдельный сбой или нарушение pipeline, отражать в `errors`;
- если partial вызван read-stage деградацией, `meta.partial_reason` объясняет качество, а `errors[*].scope = read` объясняет pipeline-аномалию.

## Failure codes, которые должны быть реально достижимы runtime
- `NORMALIZATION_FAILED` — падение `normalize_ticks()`; ответ обязан вернуться как `status=error`, без проброса исключения наружу.
- `FEATURE_ENGINE_FAILED` — падение `build_tick_feature_candles()` или strategy-specific compute после сборки свечей.
- `OUTPUT_SCHEMA_FAILED` — итоговый packet не прошёл явную валидацию против `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`; runtime обязан вернуть fallback `status=error` packet с этой ошибкой.

## Минимальный пример partial-ответа
```json
{
  "agent_id": "rsi_macd_5m_01",
  "request_id": "req-2026-03-23T10:15:00Z-rsi5m-01",
  "strategy": "RSI_MACD",
  "timeframe": "5m",
  "symbol": "BTCUSDC",
  "source": "Data_collector",
  "requested_at": "2026-03-23T10:15:00Z",
  "generated_at": "2026-03-23T10:15:02Z",
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
    "partial_reason": "gap_heavy",
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
      "scope": "read",
      "retryable": true
    }
  ]
}
```
