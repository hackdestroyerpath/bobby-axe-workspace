# PHASE 1 Sign-off (Maffi runtime)

Дата фиксации: 2026-03-24

## 1) Финальная схема runtime-потока

Финальный execution path (runtime trigger):

1. `run_trigger` принимает `TriggerInput` и входной `algo_payload` (или собирает его через `payload_source`).
2. `prompt_builder` формирует `PromptBuildResult` (`system_prompt`, `user_prompt`, `combined_prompt`, `prompt_version`, `payload_for_prompt`).
3. `llm_router` выбирает `LLMRoute` (model/provider/temperature/route_name) по prompt metadata.
4. `llm_client` строит request и вызывает LLM, получая `LLMRawResponse`.
5. `output_validator` валидирует ответ относительно request expectations (`ticker/timeframe/direction`) и формирует `LLMValidationResult`.
6. При невалидном ответе `fallbacks` применяет policy (`retry` / `fallback` / `reject`) и возвращает `LLMFallbackResult`.
7. `finalize` собирает единый `FinalNormalizedResponse` для success/fallback/reject.
8. `run_trigger` завершает путь только через `FinalNormalizedResponse`.

## 2) Runtime-модули Phase 1

- `prompt_builder` — сборка prompt из `AlgoPayload`.
- `llm_router` — выбор runtime route/model.
- `llm_client` — вызов модели и парсинг raw JSON.
- `output_validator` — контрактная валидация output.
- `fallbacks` — policy-слой retry/fallback/reject.
- `finalize` — нормализация финального ответа.
- `run_trigger` — orchestration всего end-to-end потока.

## 3) Контракт `FinalNormalizedResponse`

Стабильный контракт final envelope:

- `ticker: str`
- `timeframe: str`
- `direction: str`
- `tp: float | None`
- `sl: float | None`
- `grids: int | None`
- `price_up: float | None`
- `price_down: float | None`
- `conclusion: str`
- `status: str` (`ok` / `fallback` / `reject`)
- `confidence: float | None`
- `model_id: str | None`
- `prompt_version: str | None`
- `validator_summary: dict[str, Any]`
- `trace: dict[str, Any]`

## 4) Done criteria (из TODO) — C / D / E / F

| Блок | Пункт | Статус | Краткая фиксация |
|---|---|---|---|
| C | C1 | ✅ | Validator fail-моды формализованы и используются в fallback policy. |
| C | C2 | ✅ | `Maffi/runtime/fallbacks.py` создан и включён в runtime-path. |
| C | C3 | ✅ | `LLMFallbackResult` введён как структурированный результат. |
| C | C4 | ✅ | `json_parse_failed` обрабатывается policy через retry ветку. |
| C | C5 | ✅ | `required_field_missing` обрабатывается policy как repairable/retryable при лимите retry. |
| C | C6 | ✅ | `invalid_range` / `invalid_grids` / `invalid_tp_sl` вынесены в fallback-ветку. |
| C | C7 | ✅ | `direction_mismatch` / `ticker_mismatch` / `timeframe_mismatch` обработаны централизованно. |
| C | C8 | ✅ | Retry policy централизован (`MAX_RETRY_COUNT`, `RETRYABLE_CODES`). |
| C | C9 | ✅ | Fallback envelope имеет стабильный shape (`fallback_payload`). |
| C | C10 | ✅ | Есть `tests/test_maffi_fallbacks.py`, тесты зелёные. |
| D | D1 | ✅ | Контракты finalizer input/output зафиксированы в сигнатуре `finalize_response`. |
| D | D2 | ✅ | `Maffi/runtime/finalize.py` создан и интегрирован. |
| D | D3 | ✅ | Normal flow нормализуется в `FinalNormalizedResponse` со стабильными типами. |
| D | D4 | ✅ | Fallback/reject path finalization поддерживается единым envelope. |
| D | D5 | ✅ | В финал прокидываются `status`, `model_id`, `prompt_version`, `validator_summary`, `trace`. |
| D | D6 | ✅ | Есть `tests/test_maffi_finalize.py`, тесты зелёные. |
| E | E1 | ✅ | Entry contract формализован (`TriggerInput` -> `FinalNormalizedResponse`). |
| E | E2 | ✅ | `Maffi/runtime/run_trigger.py` создан как orchestration entrypoint. |
| E | E3 | ✅ | Payload intake поддерживает `algo_payload` и `payload_source`. |
| E | E4 | ✅ | Интегрирован вызов `prompt_builder`. |
| E | E5 | ✅ | Интегрирован вызов `llm_router`. |
| E | E6 | ✅ | Интегрирован вызов `llm_client`. |
| E | E7 | ✅ | Интегрирован вызов `output_validator`. |
| E | E8 | ✅ | Интегрирован вызов `fallbacks` при validator-fail. |
| E | E9 | ✅ | Интегрирован вызов `finalize`, единый final envelope на выходе. |
| E | E10 | ✅ | Есть `tests/test_maffi_run_trigger.py`, trace propagation покрыт и зелёный. |
| F | F1 | ✅ | Acceptance suite проверяет новый LLM live chain end-to-end. |
| F | F2 | ✅ | Добавлены LLM-flow regression fixtures (`tests/fixtures/maffi_llm_flow/*`). |
| F | F3 | ✅ | Unit + acceptance набор прогнан и зелёный. |
| F | F4 | ✅ | Legacy boundary обозначен (см. раздел ниже). |
| F | F5 | ✅ | Формальный Phase 1 ready state зафиксирован этим sign-off документом. |

## 5) Legacy boundary

### Остаётся для compatibility

- Legacy deterministic runtime API и модели (транзитный слой в `models.py`) оставляются как compatibility path для текущих потребителей.
- Legacy acceptance path остаётся опциональным (`--with-legacy`) и не блокирует новый LLM release-pass по умолчанию.
- Runtime exports совместимости (например deterministic replay/legacy validators) сохраняются до отдельной deprecation-фазы.

### Считается deprecated

- Использование legacy deterministic path как primary execution route для новых trigger-вызовов.
- Расширение старого deterministic контракта вместо развития LLM runtime chain.
- Добавление новых feature-требований в legacy response-models без business-critical причины.

## 6) Минимальный acceptance-набор для release-pass

Минимум, который обязан быть зелёным:

1. `pytest -q tests/test_maffi_prompt_builder.py`
2. `pytest -q tests/test_maffi_llm_router.py`
3. `pytest -q tests/test_maffi_llm_client.py`
4. `pytest -q tests/test_maffi_output_validator.py`
5. `pytest -q tests/test_maffi_fallbacks.py`
6. `pytest -q tests/test_maffi_finalize.py`
7. `pytest -q tests/test_maffi_run_trigger.py`
8. `python -m Maffi.runtime.acceptance_suite`

Release decision rule:
- если любой пункт выше не зелёный — Phase 1 release-pass blocked;
- если все пункты зелёные — runtime считается готовым к релизному проходу в рамках Phase 1.
