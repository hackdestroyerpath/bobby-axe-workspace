# MAFFI TODO

Статус: кодовый TODO-лист после анализа текущего `Maffi/`.
Дата: 2026-03-24

---

# Короткий итог анализа

В `Maffi/` уже собраны:
- почти весь документный каркас нового LLM-flow;
- examples для payload/output;
- базовый runtime scaffold;
- preprocessing / payload_builder / bridge / acceptance_suite;
- decision engine старого deterministic типа, который уже частично усилен.

Значит, следующая задача — не писать ещё одну схему, а **довести код до рабочего LLM-per-ticker runtime**.

Главный разрыв сейчас такой:
- **документы описывают новый LLM-flow**,
- **часть кода всё ещё живёт в старой score-based decision логике**.

Поэтому основной план должен закрыть именно этот разрыв.

---

# План моих действий

План разбит на **3 фазы**.

---

# PHASE 1 — Rebuild core runtime around the new LLM flow

## Цель фазы
Собрать рабочее ядро нового runtime-контура:

`trigger -> algo_payload -> prompt -> ticker-LLM -> output validation -> normalized final response`

Это главная фаза. Ниже мои действия — детально и по мелким шагам.

---

## 1. Зафиксировать фактический runtime target

### Действия
1. Сверить между собой:
   - `WISH_LIST_ALGO.md`
   - `LLM_TRIGGER_CONTRACT.md`
   - `LLM_OUTPUT_CONTRACT.md`
   - `FINAL_RESPONSE_ENVELOPE.md`
   - текущие `runtime/models.py`
2. Выписать, какие runtime-модели уже подходят новому flow, а какие нет.
3. Отдельно отметить legacy-поля старого decision path:
   - `long_score`
   - `short_score`
   - `reject_score`
   - `entry_candidates`
   - старый `Decision`-центричный output
4. Зафиксировать канонический runtime path для кода, а не только для docs.

### Результат
- один короткий execution target для runtime;
- ясный список, что в коде остаётся, что меняется, что выпиливается постепенно.

---

## 2. Перестроить runtime models под LLM-flow

### Действия
1. Разделить модели на 4 уровня:
   - `TriggerInput`
   - `AlgoPayload`
   - `LLMRawResponse`
   - `FinalNormalizedResponse`
2. Вынести в модели новые блоки payload:
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
3. Отделить transport-модели от final response-моделей.
4. Сохранить совместимость там, где это полезно для bridge/tests.

### Результат
- `models.py` соответствует новому flow;
- старые поля больше не являются центром архитектуры.

---

## 3. Перестроить payload_builder под реальный algo_payload

### Действия
1. Взять текущий `payload_builder.py` и разложить его на новые блоки.
2. Привязать builder к данным из preprocessing.
3. Добавить формирование:
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
4. Проверить, что итоговый builder даёт compact payload, а не legacy score-pack.
5. Оставить, если нужно, временный adapter из legacy-полей в новый формат.

### Результат
- builder реально собирает payload для LLM;
- payload shape соответствует документам и examples.

---

## 4. Дожать preprocessing до полного feature-pack

### Действия
1. Проверить, какие блоки уже реально считаются в `preprocessing.py`.
2. Закрыть пробелы по:
   - market snapshot fields
   - short-term structure fields
   - volatility fields
   - order flow fields
   - support/resistance zones
   - quality/degradation fields
3. Убедиться, что preprocessing не передаёт в LLM сырые тики и длинные массивы.
4. Нормализовать quality/degradation trace.
5. Сверить получаемые поля с `LLM_PAYLOAD_FIELD_MATRIX.md`.

### Результат
- preprocessing становится настоящим feature source для LLM-flow;
- payload_builder больше не догадывается, а получает нормальные агрегаты.

---

## 5. Собрать prompt builder

### Действия
1. Создать `prompt_builder.py`.
2. На основе `PROMPT_TEMPLATE.md` собрать deterministic prompt assembly.
3. В prompt жёстко вставлять:
   - ticker
   - timeframe
   - request_ts
   - direction
   - compact algo_payload
   - required JSON-only output contract
4. Ограничить длину prompt за счёт minimization rules.
5. Добавить prompt versioning.

### Результат
- есть реальный код, который готовит prompt для тикерной LLM;
- prompt стабилен и воспроизводим.

---

## 6. Собрать ticker-specific LLM router

### Действия
1. Создать `llm_router.py`.
2. Зафиксировать кодовый mapping:
   - `ticker -> model/config/context`
3. Поддержать default route и ticker overrides.
4. Добавить risk mode / style mode hooks.
5. Сделать router чистым и тестируемым, без скрытой магии.

### Результат
- Maffi умеет выбирать правильный LLM context под тикер.

---

## 7. Реализовать LLM client layer

### Действия
1. Создать `llm_client.py`.
2. Реализовать реальный вызов модели.
3. Поддержать:
   - system + user prompt
   - JSON-only mode
   - timeout
   - raw response capture
   - normalized parsed response
4. Добавить защиту от пустого/битого ответа.
5. Подготовить interface так, чтобы потом можно было мокать в тестах.

### Результат
- runtime может реально сходить в LLM и получить сырой ответ.

---

## 8. Собрать post-LLM output validator

### Действия
1. Создать `output_validator.py`.
2. Проверять:
   - валидность JSON
   - наличие всех required fields
   - `price_down < price_up`
   - `grids > 0`
   - корректность `tp/sl`
   - непустой `conclusion`
   - согласованность с input direction
3. Вернуть machine-readable validator result.
4. Добавить severity / reason codes.

### Результат
- ответ модели проходит жёсткий машинный контроль до отдачи наружу.

---

## 9. Собрать fallback executor

### Действия
1. Создать `fallbacks.py`.
2. Описать поведение при:
   - broken JSON
   - missing required fields
   - nonsensical ranges
   - nonsensical TP/SL
   - contradictory output
3. Поддержать:
   - retry once / retry policy
   - hard reject
   - normalized fallback envelope
4. Логировать, почему сработал fallback.

### Результат
- Maffi не ломается на плохом ответе модели.

---

## 10. Собрать final response normalizer

### Действия
1. Создать `finalize.py` или аналогичный слой.
2. Привести итог к одному stable response shape.
3. Нормализовать типы, ключи, nullable-поля и текст заключения.
4. Убедиться, что наружу всегда уходит один и тот же envelope.

### Результат
- внешний мир получает стабильный ответ независимо от внутренней вариативности LLM.

---

## 11. Собрать единый runtime entrypoint

### Действия
1. Создать `run_trigger.py` или `llm_flow.py`.
2. Соединить весь контур:
   - parse trigger
   - build payload
   - build prompt
   - route ticker model
   - call LLM
   - validate response
   - apply fallback/reject
   - normalize final answer
3. Сделать entrypoint простым и пригодным для orchestration.

### Результат
- появляется единая точка запуска Maffi под новый trigger.

---

## 12. Обновить acceptance suite под новый core flow

### Действия
1. Переписать `acceptance_suite.py` так, чтобы он проверял уже новый LLM-runtime.
2. Добавить хотя бы smoke-сценарии:
   - healthy long
   - healthy short
   - weak confidence
   - chaotic
   - invalid llm json
   - fallback path
3. Сделать моки LLM client.

### Результат
- Phase 1 проверяется автоматически именно как новый LLM-flow.

---

## Definition of Done Phase 1
Фаза 1 считается завершённой, если:
- runtime models соответствуют новому LLM flow;
- payload_builder реально собирает новый compact algo_payload;
- preprocessing даёт полный feature-pack;
- есть prompt builder;
- есть ticker-specific router;
- есть реальный llm client layer;
- есть post-LLM validator;
- есть fallback executor;
- есть final response normalizer;
- есть единый runtime entrypoint;
- acceptance smoke suite проверяет новый flow.

---

# PHASE 2 — Integrate with orchestration and harden runtime

## Цель фазы
Подключить новый LLM-runtime к реальному delivery/orchestration слою и сделать его устойчивым в бою.

## Мои задачи
1. Обновить `bridge.py` под новый trigger/payload flow.
2. Связать runtime delivery с live trigger contract.
3. Добавить structured traceability на каждый run:
   - trigger input
   - payload version
   - prompt version
   - routed ticker/model
   - raw llm response
   - validator result
   - fallback result
   - final response
4. Добавить deterministic fixtures для prompt / llm raw output / normalized output.
5. Подготовить e2e тесты на orchestration handoff.
6. Проверить go/no-go path на реальных сценариях запуска.

## Definition of Done Phase 2
- orchestration умеет передать payload в новый runtime;
- runtime умеет пройти весь trigger flow end-to-end;
- есть трассировка и audit trail;
- e2e сценарии зелёные.

---

# PHASE 3 — Production hardening and release closure

## Цель фазы
Закрыть production-ready требования не документом, а фактом работы системы.

## Мои задачи
1. Расширить acceptance suite до production-уровня.
2. Собрать regression pack по:
   - prompt fixtures
   - llm responses
   - fallback cases
   - trigger cases
3. Проверить соответствие runtime всем документам в `Maffi/`.
4. Закрыть release checklist по фактическим артефактам.
5. Провести финальную ревизию:
   - что legacy можно удалить,
   - что оставить как compatibility layer,
   - где ещё остаются узкие места.

## Definition of Done Phase 3
- acceptance/regression зелёные;
- runtime соответствует docs;
- trigger flow production-ready;
- release checklist реально закрыт;
- Maffi готов к живому LLM-per-ticker режиму.
