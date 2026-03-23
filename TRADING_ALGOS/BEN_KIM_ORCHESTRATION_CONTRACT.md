# BEN_KIM ORCHESTRATION CONTRACT

Этот документ фиксирует machine-to-orchestrator expectations для следующей фазы.

## 1. Addressing
- Адресовать машину только по `machine_id` / `agent_id` из frozen registry.
- Не собирать runtime-target по строковым эвристикам вне registry.
- Для агрегации стратегии сопоставлять только trio `1m`, `5m`, `60m` одной и той же family.

## 2. Reading status
- `ready` — можно агрегировать без degraded flag.
- `partial` — можно читать, но надо тащить `meta.partial_reason`, `coverage_ratio` и confidence cap дальше.
- `error` — не агрегировать в strategy vote; разбирать по `errors`.

## 3. Retry policy
Повторный вызов допустим только если у ошибки `retryable = true`.

Обычно retryable:
- `PAGINATION_DRIFT`
- `READ_TIMEOUT`
- `NORMALIZATION_FAILED`
- `FEATURE_ENGINE_FAILED`
- `TRANSPORT_FAILED`

Не retryable по умолчанию:
- `REQUEST_VALIDATION_FAILED`
- `RETENTION_WINDOW_TOO_SHALLOW`
- `INSUFFICIENT_WARMUP`
- `EMPTY_WINDOW`

## 4. Aggregation rules
- Агрегировать ответы только если совпадают `strategy`, `symbol`, верхнеуровневый `response_contract_version` и `meta.source_contract_version`.
- `partial` packet не превращать в `ready` после агрегации.
- Если хотя бы один timeframe в family имеет `partial` из-за retention/pagination/gaps, итог family надо маркировать как degraded.

## 5. Elliott handling
- Low-confidence Elliott не использовать как direct trigger.
- Elliott packet трактовать как candidate overlay поверх более детерминированных family outputs.
- Если `status=partial` или есть gaps, Elliott confidence не повышать даже при красивой структуре.

## 6. Multi-timeframe alignment
- `60m` — context anchor.
- `5m` — основное intraday confirmation.
- `1m` — tactical execution/timing layer.
- Конфликт `1m` против сильного `60m` не должен автоматически ломать старший bias.

## 7. Drop/degrade rules
Нужно отбрасывать или резко downweight:
- любой packet с `status=error`;
- любой packet с `partial_reason=empty_window`;
- Elliott packet с `elliott_confidence_state=low`, если нет подтверждения от других family;
- structural claims family `LEVELS_FIBO_HV`, если `level_context_strength=weak` и вход partial.
