# MAFFI TODO

Статус: обновлённый programming TODO по фактическому остатку работ.
Дата: 2026-03-24

---

# Короткий итог анализа текущего состояния

На текущий момент уже закрыты и реально работают в коде:

## Уже сделано
- runtime target зафиксирован под новый LLM-per-ticker flow
- `models.py` перестроен под новый flow с compatibility-слоем
- `payload_builder.py` собирает новый блочный `algo_payload`
- `preprocessing.py` даёт реальный compact feature-pack:
  - `market_snapshot`
  - `price_structure`
  - `volatility`
  - `order_flow`
  - `market_regime`
  - `support_resistance`
  - `quality_trust`
- `prompt_builder.py` уже собран и тестируется
- `llm_router.py` уже собран и тестируется
- `llm_client.py` уже собран и тестируется
- `output_validator.py` уже собран и тестируется
- runtime facade (`Maffi/runtime/__init__.py`) уже экспортирует:
  - `build_prompt`
  - `serialize_algo_payload_for_prompt`
  - `route_llm`
  - `build_llm_request`
  - `call_llm`
  - `validate_llm_output`

## Текущее подтверждение
Актуальный тестовый слой зелёный:
- **53 tests OK**

---

# Главный вывод

Фаза 1 больше не про контракты, prompt и routing — они уже собраны.  
Сейчас реальный остаток работ — это **замкнуть контур после validator и довести runtime до end-to-end execution path**.

То есть ядро текущего остатка:
1. `fallbacks.py`
2. `finalize.py`
3. `run_trigger.py`
4. обновление acceptance/e2e под новый flow
5. вычищение legacy-следов старого deterministic path настолько, насколько это безопасно в рамках Phase 1

---

# ОБНОВЛЁННЫЙ TODO

# PHASE 1 — Close the runnable LLM flow end-to-end

## Блок C — `fallbacks.py`

### C1. Зафиксировать контекст после validator
**Что сделать:**
- открыть `LLMValidationResult`
- открыть `LLMRawResponse`
- зафиксировать, какие validator fail-моды уже реально есть:
  - `json_parse_failed`
  - `required_field_missing`
  - `invalid_type`
  - `invalid_range`
  - `invalid_grids`
  - `invalid_tp_sl`
  - `direction_mismatch`
  - `ticker_mismatch`
  - `timeframe_mismatch`

**Результат:**
- ясная карта, какие ошибки fallback должен обрабатывать

---

### C2. Создать `fallbacks.py`
**Что сделать:**
- создать новый файл `Maffi/runtime/fallbacks.py`
- добавить imports
- создать scaffold функций

**Результат:**
- отдельный runtime-модуль fallback-слоя

---

### C3. Добавить fallback result object
**Что сделать:**
- создать структурированный fallback result либо в `models.py`, либо локально в `fallbacks.py`
- в result заложить:
  - `action`
  - `reason`
  - `retry_allowed`
  - `retry_recommended`
  - `fallback_payload`
  - `trace`

**Результат:**
- downstream не работает с размытыми `dict[Any]`

---

### C4. Реализовать broken JSON policy
**Что сделать:**
- если validator вернул `json_parse_failed`, определить policy:
  - retry once / reject
- оформить это в коде как отдельный сценарий

**Результат:**
- реакция на broken JSON формализована

---

### C5. Реализовать missing fields policy
**Что сделать:**
- если не хватает обязательных полей,
- определить, считается ли кейс repairable или hard reject

**Результат:**
- обязательные поля имеют формальную remediation policy

---

### C6. Реализовать invalid range / tp-sl / grids policy
**Что сделать:**
- для `invalid_range`
- для `invalid_grids`
- для `invalid_tp_sl`
сделать отдельные ветки policy

**Результат:**
- геометрически бессмысленный output не проходит дальше бесконтрольно

---

### C7. Реализовать mismatch policy
**Что сделать:**
- отдельно описать реакцию на:
  - `direction_mismatch`
  - `ticker_mismatch`
  - `timeframe_mismatch`

**Результат:**
- response/request consistency guarded centrally

---

### C8. Добавить retry policy
**Что сделать:**
- определить max retry count
- определить retryable codes
- вынести это в одно место, а не размазывать по коду

**Результат:**
- retry decision централизован и прозрачен

---

### C9. Добавить normalized fallback envelope
**Что сделать:**
- если нужен fallback output, он должен иметь стабильный shape
- без случайных ad-hoc dicts

**Результат:**
- downstream слои не ломаются на fallback path

---

### C10. Добавить fallback tests и прогнать suite
**Что сделать:**
- создать `tests/test_maffi_fallbacks.py`
- покрыть:
  - broken JSON
  - missing field
  - invalid range
  - wrong direction
  - hard reject
  - fallback envelope shape
- прогнать suite
- исправить интеграцию

**Результат:**
- fallback layer закрыт и зелёный

---

## Блок D — `finalize.py`

### D1. Зафиксировать finalizer input/output
**Что сделать:**
- определить вход finalizer’а:
  - validated output / fallback result / route meta / raw response meta
- определить выход:
  - `FinalNormalizedResponse`

**Результат:**
- finalizer получает чёткий контракт

---

### D2. Создать `finalize.py`
**Что сделать:**
- создать файл `Maffi/runtime/finalize.py`
- добавить scaffold

**Результат:**
- отдельный runtime-модуль finalization-слоя

---

### D3. Реализовать normal flow normalization
**Что сделать:**
- нормализовать:
  - `ticker`
  - `timeframe`
  - `direction`
  - `tp`
  - `sl`
  - `grids`
  - `price_up`
  - `price_down`
  - `conclusion`
- привести к стабильным типам

**Результат:**
- success-path final response стабилен

---

### D4. Реализовать fallback/reject finalization
**Что сделать:**
- если upstream дал fallback/reject,
- собирать совместимый final response envelope
- не ломать общий output contract

**Результат:**
- finalizer умеет не только happy path

---

### D5. Добавить status/meta/trace injection
**Что сделать:**
- прокинуть в final object:
  - `status`
  - `model_id`
  - `prompt_version`
  - `validator_summary`
  - `trace`

**Результат:**
- final response пригоден для downstream и audit

---

### D6. Добавить finalize tests и прогнать suite
**Что сделать:**
- создать `tests/test_maffi_finalize.py`
- покрыть:
  - valid normalize
  - nullable fields
  - fallback status
  - prompt_version/model_id pass-through
  - trace pass-through
- прогнать suite
- исправить интеграцию

**Результат:**
- finalizer закрыт и зелёный

---

## Блок E — `run_trigger.py`

### E1. Зафиксировать entrypoint contract
**Что сделать:**
- определить минимальный input:
  - `ticker`
  - `timeframe`
  - `request_ts_utc`
  - `direction`
  - payload source / payload object
- определить output:
  - `FinalNormalizedResponse`

**Результат:**
- entrypoint имеет чёткий контракт

---

### E2. Создать `run_trigger.py`
**Что сделать:**
- создать файл `Maffi/runtime/run_trigger.py`
- добавить scaffold orchestration-функции

**Результат:**
- отдельный entrypoint-модуль создан

---

### E3. Подключить payload intake
**Что сделать:**
- принять готовый payload или собрать его из builder-пайплайна
- выровнять вход runtime

**Результат:**
- единая точка входа в flow

---

### E4. Подключить `prompt_builder`
**Что сделать:**
- вызвать `build_prompt(payload)`
- получить `PromptBuildResult`

**Результат:**
- prompt входит в единый runtime-path

---

### E5. Подключить `llm_router`
**Что сделать:**
- вызвать `route_llm(prompt_result)`
- получить `LLMRoute`

**Результат:**
- route становится частью entrypoint

---

### E6. Подключить `llm_client`
**Что сделать:**
- вызвать `call_llm(prompt_result, route)`
- получить `LLMRawResponse`

**Результат:**
- entrypoint уже реально зовёт модель

---

### E7. Подключить `output_validator`
**Что сделать:**
- вызвать `validate_llm_output(...)`
- получить `LLMValidationResult`

**Результат:**
- в flow появляется контрактная валидация

---

### E8. Подключить `fallbacks`
**Что сделать:**
- если validator fail,
- применить fallback policy

**Результат:**
- flow не ломается на невалидном ответе модели

---

### E9. Подключить `finalize`
**Что сделать:**
- перевести success/fallback path в `FinalNormalizedResponse`

**Результат:**
- flow заканчивается единым final envelope

---

### E10. Добавить trace propagation, tests и прогнать suite
**Что сделать:**
- прокинуть trace/meta через весь контур
- создать `tests/test_maffi_run_trigger.py`
- покрыть:
  - happy path
  - invalid output path
  - fallback path
  - reject path
  - trace propagation
- прогнать suite
- исправить интеграцию

**Результат:**
- runtime entrypoint закрыт и зелёный

---

## Блок F — Final Phase 1 closure

### F1. Обновить acceptance suite под новый LLM-flow
**Что сделать:**
- переписать/расширить acceptance suite так, чтобы он проверял новый live chain:
  - prompt -> route -> llm -> validator -> fallback/finalize -> final response

**Результат:**
- acceptance соответствует новому runtime

---

### F2. Добавить LLM-flow regression fixtures
**Что сделать:**
- fixtures для:
  - prompt build
  - llm raw response
  - validator result
  - fallback result
  - final response

**Результат:**
- regression покрывает end-to-end path

---

### F3. Прогнать полный suite
**Что сделать:**
- unit suite
- acceptance suite
- при необходимости smoke e2e

**Результат:**
- зелёный тестовый контур всего Phase 1

---

### F4. Проверить legacy cleanup boundary
**Что сделать:**
- отметить, что из legacy deterministic path можно оставить как compatibility
- что уже можно не использовать в новом path

**Результат:**
- чистые границы нового и старого контура

---

### F5. Зафиксировать Phase 1 ready state
**Что сделать:**
- короткий signoff по факту:
  - runtime flow собран
  - validator/fallback/finalize/entrypoint закрыты
  - tests зелёные

**Результат:**
- формальное закрытие Phase 1

---

# Приоритет ближайшего хода

Если идти правильно, ближайший порядок теперь такой:

1. **Закрыть `fallbacks.py`**
2. **Закрыть `finalize.py`**
3. **Закрыть `run_trigger.py`**
4. **Обновить acceptance suite**
5. **Сделать final Phase 1 closure**

---

# Definition of Done

Этот TODO считается закрытым, когда новый Maffi runtime по trigger-вызову:
- принимает входной context,
- получает/строит `algo_payload`,
- собирает prompt,
- выбирает route,
- вызывает LLM,
- валидирует output,
- применяет fallback при необходимости,
- собирает final normalized response,
- и проходит unit + acceptance suite без поломок.
