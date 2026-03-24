# MAFFI TODO

Статус: обновлено по фактическому состоянию репозитория и текущего кода.
Дата: 2026-03-24

---

# Что уже есть в коде и документах

По состоянию на сейчас уже существуют и лежат в репозитории:

## Уже собраны документы / контракты
- `Maffi/WISH_LIST_ALGO.md`
- `Maffi/LLM_TRIGGER_CONTRACT.md`
- `Maffi/LLM_PAYLOAD_BLOCKS.md`
- `Maffi/LLM_PAYLOAD_FIELD_MATRIX.md`
- `Maffi/LLM_PAYLOAD_MINIMIZATION_RULES.md`
- `Maffi/LLM_PAYLOAD_UNITS.md`
- `Maffi/LLM_OUTPUT_CONTRACT.md`
- `Maffi/llm_output_contract.json`
- `Maffi/PROMPT_TEMPLATE.md`
- `Maffi/PROMPT_CONTROL_POLICY.md`
- `Maffi/TICKER_LLM_ROUTING.md`
- `Maffi/LLM_OUTPUT_VALIDATOR.md`
- `Maffi/LLM_FALLBACK_POLICY.md`
- `Maffi/LLM_TRACEABILITY_SPEC.md`
- `Maffi/FINAL_RESPONSE_ENVELOPE.md`
- `Maffi/LIVE_TRIGGER_FLOW.md`
- `Maffi/RUNTIME_DELIVERY_CONTRACT.md`
- `Maffi/LLM_FLOW_ACCEPTANCE.md`
- `Maffi/PRODUCTION_RELEASE_CHECKLIST.md`

## Уже собраны примеры
- payload examples: healthy / weak / chaotic
- market snapshot / price structure / volatility / order flow / regime / support-resistance examples
- grid candidates examples
- prompt-ready examples
- final output example

## Уже есть runtime-код
- `Maffi/runtime/preprocessing.py`
- `Maffi/runtime/payload_builder.py`
- `Maffi/runtime/bridge.py`
- `Maffi/runtime/models.py`
- `Maffi/runtime/enums.py`
- `Maffi/runtime/acceptance_suite.py`
- `Maffi/runtime/__init__.py`

## Уже есть тесты
Прогнано успешно:
- `30 tests OK`
- acceptance smoke suite тоже проходит при запуске с `PYTHONPATH=.`

---

# Главный вывод

Большая часть **документной Phase 1–5** уже не “в планах”, а **уже формально собрана**.  
Теперь основной остаток — это не написать ещё один wishlist, а **дожать фактическую реализацию LLM-flow и связать её в живой runtime**.

То есть новый TODO должен быть не “что придумать”, а **что реально осталось реализовать поверх уже существующих контрактов и заготовок**.

---

# ОБНОВЛЁННЫЙ TODO

# PHASE 1 — Close gaps between docs and actual runtime

## 1. Свести runtime-код к новому LLM-flow

### Сейчас есть
- документы уже описывают новый LLM workflow;
- но runtime в `Maffi/runtime/__init__.py` всё ещё в основном работает как deterministic decision engine старого типа;
- он валидирует payload, ранжирует grid candidates и выдаёт решение сам, вместо полноценного `LLM call -> validate -> normalize` контура.

### Что осталось сделать
- перестроить runtime вокруг нового потока:
  - trigger input
  - algo payload intake
  - prompt building
  - ticker-specific LLM call
  - post-LLM validation
  - final normalized response

### Артефакт завершения
- `Maffi/runtime/llm_flow.py` или эквивалентный единый runtime entrypoint

---

## 2. Привязать payload builder к новому payload standard

### Сейчас есть
- `payload_builder.py` уже умеет собирать структурированный payload;
- но по содержанию он ещё ближе к старой score-based схеме (`long_score`, `short_score`, `reject_score`, `entry_candidates`, `support_level`, `resistance_level`).

### Что осталось сделать
- перестроить builder так, чтобы он собирал именно те блоки, которые зафиксированы в `WISH_LIST_ALGO`:
  - `request_context`
  - `market_snapshot`
  - `price_structure`
  - `volatility`
  - `order_flow`
  - `market_regime`
  - `support_resistance`
  - `grid_geometry_hints`
  - `grid_candidates`
  - `quality_trust`
  - `prompt_control`

### Артефакт завершения
- новый canonical `algo_payload` builder
- 1:1 соответствие `payload_builder.py` и `LLM_PAYLOAD_BLOCKS.md`

---

## 3. Дожать preprocessing до полного feature-pack

### Сейчас есть
- preprocessing собран базово;
- но часть блоков в документах есть только как spec/examples, а не как полноценный вычислительный слой.

### Что осталось сделать
- дожать фактический расчёт:
  - market snapshot fields
  - price structure fields
  - volatility block
  - order flow block
  - market regime block
  - support/resistance block
  - grid geometry hints block
  - quality/trust block

### Артефакт завершения
- feature extraction pipeline, который реально даёт весь compact algo_payload

---

# PHASE 2 — Build actual LLM invocation layer

## 4. Собрать prompt builder

### Что осталось сделать
- реализовать код, который из `algo_payload` строит prompt для LLM;
- встроить туда:
  - direction
  - ticker
  - timeframe
  - request timestamp
  - compact market context
  - must-return JSON contract

### Артефакт завершения
- `Maffi/runtime/prompt_builder.py`

---

## 5. Собрать ticker-specific LLM router

### Что осталось сделать
- реализовать реальный routing:
  - `ticker -> model/context`
- определить, как задаётся отдельная LLM под тикер;
- добавить конфиг и fallback routing.

### Артефакт завершения
- `Maffi/runtime/llm_router.py`
- config mapping для тикеров

---

## 6. Реализовать сам LLM call layer

### Что осталось сделать
- написать слой вызова модели;
- поддержать строгий JSON-only ответ;
- сохранить raw response и normalized response.

### Артефакт завершения
- `Maffi/runtime/llm_client.py`
- рабочий вызов OpenAI LLM для тикера

---

# PHASE 3 — Validate and normalize LLM output

## 7. Собрать post-LLM validator в коде

### Сейчас есть
- policy и контракт уже описаны документами;
- но нужен реальный кодовый валидатор под ответ модели.

### Что осталось сделать
Проверять:
- valid JSON
- все required fields
- `price_down < price_up`
- `grids > 0`
- корректность `tp/sl`
- non-empty conclusion
- соответствие direction входу

### Артефакт завершения
- `Maffi/runtime/output_validator.py`

---

## 8. Собрать fallback / reject executor

### Что осталось сделать
- реализовать, что делать при:
  - broken JSON
  - missing fields
  - nonsense TP/SL
  - inverted range
  - invalid grids
- определить retry policy и reject mode.

### Артефакт завершения
- `Maffi/runtime/fallbacks.py`

---

## 9. Собрать final response normalizer

### Что осталось сделать
- привести ответ модели к стабильному финальному envelope;
- нормализовать ключи, типы и поле `conclusion`.

### Артефакт завершения
- `Maffi/runtime/finalize.py`

---

# PHASE 4 — Integrate live flow

## 10. Собрать единый runtime entrypoint под trigger

### Что осталось сделать
Собрать end-to-end path:
- trigger parse
- payload build / fetch
- prompt build
- LLM call
- output validate
- fallback/reject
- final response

### Артефакт завершения
- `Maffi/runtime/run_trigger.py`

---

## 11. Связать orchestration delivery

### Что осталось сделать
- определить, как algo_payload реально попадает в Maffi;
- увязать bridge/runtime delivery с live trigger flow.

### Артефакт завершения
- обновлённый `bridge.py` под новый LLM-flow

---

## 12. Добавить traceability по каждому вызову

### Что осталось сделать
Логировать:
- trigger input
- payload version
- prompt version
- ticker route
- raw LLM response
- normalized response
- validator result
- final status

### Артефакт завершения
- runtime trace log / structured event object

---

# PHASE 5 — Hardening and release

## 13. Расширить acceptance suite до нового LLM-flow

### Сейчас есть
- acceptance smoke suite есть, но он ещё проверяет скорее deterministic local decision path.

### Что осталось сделать
Добавить сценарии именно под новый контур:
- healthy long LLM response
- healthy short LLM response
- weak confidence payload
- chaotic payload
- invalid model JSON
- missing field output
- fallback path
- full trigger flow

### Артефакт завершения
- обновлённый `Maffi/runtime/acceptance_suite.py`

---

## 14. Добавить regression fixtures для LLM-flow

### Что осталось сделать
Собрать fixtures:
- prompt fixtures
- raw response fixtures
- normalized output fixtures
- reject/fallback fixtures

### Артефакт завершения
- regression pack under `Maffi/examples/` or `tests/fixtures/`

---

## 15. Закрыть production release checklist фактом, а не только документом

### Что осталось сделать
Подтвердить вживую:
- contracts match runtime
- payload builder match docs
- prompt builder ready
- ticker router ready
- llm client ready
- output validator ready
- fallback ready
- live trigger flow ready
- acceptance green

### Артефакт завершения
- production-ready signoff

---

# Что можно считать уже закрытым

## Закрыто или почти закрыто
- документный контур нового LLM-flow;
- examples layer;
- базовый preprocessing scaffold;
- базовый payload builder scaffold;
- базовый bridge scaffold;
- базовый acceptance scaffold.

## Не закрыто
- реальный LLM invocation layer;
- prompt builder;
- ticker-specific routing в коде;
- post-LLM validator в коде;
- fallback executor;
- final live trigger entrypoint;
- full acceptance именно под новый LLM-flow.

---

# Приоритет следующего хода

Если идти правильно, следующий рабочий порядок такой:

1. **Перестроить `payload_builder.py` под новый `algo_payload` standard**
2. **Собрать `prompt_builder.py`**
3. **Собрать `llm_router.py` и `llm_client.py`**
4. **Собрать `output_validator.py` и `fallbacks.py`**
5. **Собрать единый `run_trigger.py`**
6. **Обновить acceptance suite под новый flow**

---

# Definition of Done

Этот TODO считается закрытым, когда Maffi по trigger-вызову:
- принимает `ticker + timeframe + ts + direction + algo_payload`,
- вызывает правильную тикерную LLM,
- получает валидный ответ,
- нормализует его,
- умеет корректно reject/fallback,
- и стабильно возвращает:
  - `TP`
  - `SL`
  - `Grids`
  - `Price_up`
  - `Price_down`
  - `Короткое заключение`
