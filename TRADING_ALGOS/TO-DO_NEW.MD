# TO-DO_NEW

# PHASE 3 — INTEGRATION VALIDATION, BTC PACKAGING, STORAGE HANDOFF READINESS

## Goal
Превратить уже собранный в `PHASE 2` contract-first runtime в проверяемый operational contour для `Ben_Kim`, не меняя архитектурную базу и не подменяя реальные проверки бумажным «вроде работает».

Эта фаза должна подтвердить сразу 3 вещи:
- все 12 машин реально вызываются и возвращают usable outputs по единому контракту;
- `Ben_Kim` умеет собирать по одному `symbol` ровно 12 отдельных symbol-scoped objects без потери identity, quality flags и traceability;
- эти objects уже готовы к downstream handoff в отдельный object-storage domain через API-контракт.

## Why this version replaces the old TO-DO_NEW
Старая версия `TO-DO_NEW` оставалась планом про `PHASE 2`, хотя проект уже перешёл к следующей стадии.

Новая версия оптимизирована под текущее состояние `TRADING_ALGOS`:
- опирается на уже существующие `machine_registry.py`, `runtime_contract.py`, `strategy_cores.py`, `machines.py`;
- не дублирует уже закрытую Phase 2;
- разделяет **что можно подготовить без API-ключа** и **что должен вручную валидировать владелец с API-доступом**;
- фиксирует путь `machine response -> Ben_Kim object -> storage-ready envelope` как основной operational deliverable.

## Context after completed Phase 2
К началу этой фазы уже считаем зафиксированным:
- frozen registry в `machine_registry.py`;
- единый status model `ready / partial / error` в `runtime_contract.py`;
- 4 shared family-core слоя в `strategy_cores.py`;
- shared execution wrappers в `machines.py`;
- orchestration expectations в `BEN_KIM_ORCHESTRATION_CONTRACT.md`;
- единые входные и выходные контракты (`TICK_SOURCE_CONTRACT.md`, `COMMON_TICK_READ_SPEC.md`, `SUBAGENT_*`).

Следствие: `PHASE 3` — это не новая архитектура и не ещё один redesign.
Это фаза верификации, упаковки и handoff readiness.

## Hard constraints for this phase
- compute живёт на стороне 12 машин;
- входные тики остаются в centralized tick storage;
- runtime-машины не владеют данными и не должны считать себя source-of-truth;
- доступ к tick storage идёт только через agreed API/read contract;
- `Ben_Kim` собирает machine outputs в 12 отдельных objects;
- objects должны быть готовы к записи в **отдельный** object-storage domain;
- tick storage и object storage — разные operational domains даже если инфраструктурно они позже окажутся рядом;
- traceability обязательна на всём пути: `request_id`, `api_key_id`, caller identity, timestamps, versions.

## Practical constraint for current executor
У текущего исполнителя нет API-ключа, поэтому фазу нужно вести в двух режимах:
1. **offline / contract-prep** — всё, что можно зафиксировать, проверить и подготовить без реального API-вызова;
2. **manual API validation** — всё, что должен прогнать владелец/оператор с доступом к реальному API.

Это не побочная оговорка, а часть operational discipline: не симулировать живую интеграцию там, где нет реального доступа.

---

# PHASE 3A — FREEZE VALIDATION BASELINE BEFORE ANY LIVE RUN

## Goal of Phase 3A
До любых прогонов зафиксировать один baseline, чтобы все проверки шли по одному и тому же контексту, а не по случайным окнам и разным версиям контракта.

## Step 1. Freeze the first canonical validation symbol
### Что зафиксировать
- `symbol = BTCUSDC` как первый canonical validation symbol;
- один canonical source;
- один owner-approved validation window;
- один expected `response_contract_version`;
- один expected `source_contract_version`.

### Дополнительно зафиксировать
- timezone = `UTC` на всём пути;
- window boundaries трактуются как inclusive;
- baseline должен быть одинаковым для всех 12 машин.

### Result of the step
- `PHASE_3_VALIDATION_BASELINE`.

## Step 2. Freeze runtime options for the baseline run
### Что зафиксировать
- `strict_mode = false` для первого общего прогона;
- `include_incomplete_candle = false` как baseline mode;
- отдельный повторный прогон на том же окне для deterministic check;
- отдельный optional прогон с `include_incomplete_candle = true` только как дополнительная проверка, не как основной baseline.

### Комментарий
Сначала нужен один стабильный и интерпретируемый baseline. Эксперименты с режимами — только после него.

### Result of the step
- `baseline runtime options`.

## Step 3. Freeze validation evidence format
### Нужно заранее определить
Для каждой live-проверки заранее собирать один и тот же evidence set:
- request payload;
- machine id;
- response payload;
- status;
- errors;
- `meta`;
- timestamps;
- request trace (`request_id`, `api_key_id`, caller identity если доступно);
- run label / batch label.

### Комментарий
Если evidence format не зафиксирован заранее, после первых API-прогонов начнётся хаос: часть фактов будет в логах, часть в памяти, часть потеряется.

### Result of the step
- `validation evidence checklist`.

---

# PHASE 3B — OFFLINE READINESS CHECKS (NO API KEY REQUIRED)

## Goal of Phase 3B
До живых API-тестов убедиться, что contracts, packaging rules и acceptance criteria уже определены и не потребуют пересборки после первого же реального запуска.

## Step 4. Freeze what exactly counts as a valid machine response
### Проверить и зафиксировать на уровне плана
- top-level response fields обязательны и одинаково трактуются для всех 12 машин;
- `status`, `summary`, `meta`, `errors`, `features` не должны теряться downstream;
- traceability поля обязательны:
  - `machine_id`;
  - `api_key_id`;
  - `build_version`;
  - `source_contract_version`;
  - `coverage_ratio`;
  - `is_partial`;
  - `partial_reason`.

### Что считается blocker уже на этом уровне
- downstream нельзя однозначно понять machine identity;
- нет ясной границы между `meta` и `errors`;
- `partial` semantics ещё можно «случайно потерять» при упаковке.

### Result of the step
- `machine response acceptance checklist`.

## Step 5. Freeze status honesty expectations before the first live run
### Нужно явно зафиксировать
- `ready` нельзя считать допустимым при degraded input;
- `partial` нельзя downcast-ить в нормальный usable packet без маркировки;
- `error` нельзя передавать дальше как будто это обычный answer;
- одинаково обрабатываются:
  - `retention_truncation`;
  - `pagination_truncation`;
  - `gap_heavy_window`;
  - `empty_window`.

### Комментарий
Это ключевой anti-self-deception пункт всей фазы.

### Result of the step
- `status honesty checklist`.

## Step 6. Freeze runtime readiness verdict model per machine
### Допустимые verdicts
- `ready`;
- `partial`;
- `blocked`.

### Логика verdict
#### ready
- schema complete;
- status semantics честные;
- warmup behavior корректен;
- payload usable downstream.

#### partial
- runtime работает;
- output usable только с explicit degraded-marking;
- ограничения прозрачны и traceable.

#### blocked
- broken schema;
- contract mismatch;
- status/error semantics нельзя надёжно трактовать;
- downstream не может использовать packet как unit.

### Result of the step
- `runtime readiness verdict model`.

## Step 7. Freeze Ben_Kim symbol-object contract before live packaging
### Один object =
`1 symbol + 1 strategy + 1 timeframe + 1 machine response`

### Минимально обязательные поля
- `object_id`;
- `batch_id`;
- `symbol`;
- `strategy`;
- `timeframe`;
- `machine_id`;
- `agent_id`;
- `request_id`;
- `generated_at`;
- `status`;
- `summary`;
- `meta`;
- `features`;
- `errors`.

### Обязательные quality / traceability fields
- `is_partial`;
- `partial_reason`;
- `coverage_ratio`;
- `data_points`;
- `build_version`;
- `source_contract_version`;
- `api_key_id`;
- `input_window_from`;
- `input_window_to`;
- `compute_origin` или иной эквивалентный execution origin, если доступен.

### Result of the step
- `Ben_Kim symbol object contract`.

## Step 8. Freeze idempotency basis for object packaging and write
### Нужно определить заранее
Повторный запуск не должен плодить бесконтрольные дубли.

Минимально допустимая база идемпотентности:
- `symbol + strategy + timeframe + request_id`;
или
- `symbol + strategy + timeframe + batch_id`.

### Дополнительно определить
- overwrite vs append-only policy;
- duplicate handling rule;
- object versioning rule, если потребуется;
- как маркируется повторная запись того же logical object.

### Result of the step
- `idempotency and object identity policy`.

---

# PHASE 3C — MANUAL API VALIDATION OF THE 12-MACHINE RUNTIME

## Goal of Phase 3C
С реальным API-доступом доказать, что контур действительно исполняется, а не только красиво описан.

## Important ownership note
Эти шаги требуют реального API-ключа и должны быть прогнаны владельцем/оператором вручную.
Исполнитель без ключа не должен имитировать их завершение.

## Step 9. Run all 12 machines on the same BTC baseline window
### Обязательный набор машин
- `RSI_MACD_1M`
- `RSI_MACD_5M`
- `RSI_MACD_60M`
- `LEVELS_FIBO_HV_1M`
- `LEVELS_FIBO_HV_5M`
- `LEVELS_FIBO_HV_60M`
- `VOLUME_1M`
- `VOLUME_5M`
- `VOLUME_60M`
- `ELLIOTT_1M`
- `ELLIOTT_5M`
- `ELLIOTT_60M`

### Что подтвердить
- addressing идёт через frozen registry;
- request проходит единый validation path;
- shared normalization отрабатывает одинаково;
- shared feature engine не ломает pipeline;
- family-core compute отрабатывает в рамках общего response contract;
- outputs реально собираются по одному schema.

### Result of the step
- первый `BTC 12-machine integration run`.

## Step 10. Validate API-backed tick access semantics
### Нужно отдельно подтвердить
- ни одна машина не обходит agreed API-read layer;
- входные тики читаются только через канонический API contract;
- API-read semantics не ломают `TICK_SOURCE_CONTRACT.md` и `COMMON_TICK_READ_SPEC.md`;
- сохраняются inclusive boundaries, canonical ordering и pagination stability;
- traceability входного чтения не теряется;
- degraded input не маскируется как полноценный complete read.

### Отдельно проверить partial reasons
- `retention_truncation`;
- `pagination_truncation`;
- `gap_heavy_window`;
- `empty_window`.

### Result of the step
- `tick API read validation report`.

## Step 11. Validate contract completeness against actual runtime
### Проверять на живых ответах
- top-level response fields;
- `status`;
- `summary`;
- `meta`;
- `errors`;
- strategy-specific `features`;
- все обязательные traceability fields.

### Blocker conditions
- отсутствуют критичные поля;
- response schema формально или operationally broken;
- output нельзя однозначно трактовать downstream.

### Result of the step
- `contract completeness matrix` по всем 12 машинам.

## Step 12. Validate status honesty on real degraded cases
### Нужно доказать на фактических сценариях
- `ready` не рисуется при degraded input;
- `partial` доходит до downstream без потери;
- `error` не маскируется как usable packet.

### Проверяемые сценарии
- `retention_truncation`;
- `pagination_truncation`;
- `gap_heavy_window`;
- `empty_window`.

### Result of the step
- `status honesty report`.

## Step 13. Validate warmup behavior per strategy family
### Проверить
- `RSI_MACD` не выдаёт псевдо-ready без достаточного числа candles;
- `LEVELS_FIBO_HV` не делает сильные structural claims без нужной глубины окна;
- `VOLUME` не поднимает уверенность без корректного baseline;
- `ELLIOTT` остаётся candidate-heavy и conservative при слабой структуре.

### Result of the step
- `warmup behavior validation` по 4 strategy families.

## Step 14. Reconcile failure taxonomy with emitted runtime errors
### Нужно сделать
- собрать реально emitted error codes;
- сверить их с `FAILURE_MODE_MATRIX` / agreed taxonomy;
- сверить их с retry expectations для orchestration;
- разложить на 3 класса:
  - синхронизировано;
  - частично синхронизировано;
  - требует формализации.

### Result of the step
- `failure taxonomy reconciliation report`.

## Step 15. Mark per-machine runtime readiness
### Для каждой машины вынести итоговый verdict
- `ready`;
- `partial`;
- `blocked`.

### Result of the step
- `12-machine runtime readiness matrix`.

---

# PHASE 3D — BEN_KIM PACKAGING LAYER VALIDATION

## Goal of Phase 3D
Подтвердить, что `Ben_Kim` — это не просто наблюдатель над runtime, а корректный packaging layer между 12 machine responses и downstream object storage.

## Step 16. Build the first BTC package of 12 separate objects
### Обязательный состав пакета
1. `BTCUSDC + RSI_MACD + 1m`
2. `BTCUSDC + RSI_MACD + 5m`
3. `BTCUSDC + RSI_MACD + 60m`
4. `BTCUSDC + LEVELS_FIBO_HV + 1m`
5. `BTCUSDC + LEVELS_FIBO_HV + 5m`
6. `BTCUSDC + LEVELS_FIBO_HV + 60m`
7. `BTCUSDC + VOLUME + 1m`
8. `BTCUSDC + VOLUME + 5m`
9. `BTCUSDC + VOLUME + 60m`
10. `BTCUSDC + ELLIOTT + 1m`
11. `BTCUSDC + ELLIOTT + 5m`
12. `BTCUSDC + ELLIOTT + 60m`

### Критичное правило
Это должны быть **именно 12 отдельных objects**, а не merged blob и не один свободный summary.

### Result of the step
- первый `BTC package` из 12 objects.

## Step 17. Validate packaging fidelity
### Нужно проверить
- не теряется `machine_id`;
- не теряются `strategy` и `timeframe`;
- не теряется `status`;
- не теряется `partial_reason`;
- не ломается traceability;
- `summary`, `features`, `errors`, `meta` не искажаются;
- `error` packets не превращаются в usable objects без маркировки;
- `object_id` и `batch_id` сохраняют identity discipline.

### Result of the step
- `packaging fidelity report`.

## Step 18. Freeze and validate object-level readiness rules
### Допустимые object-level verdicts
- `ready`;
- `partial`;
- `blocked`.

### Логика
Даже при корректном machine response итоговый object может быть непригоден, если:
- потеряна identity-связка;
- утеряны quality flags;
- сломан storage-facing envelope;
- объект нельзя безопасно записать downstream.

### Result of the step
- `12-object readiness matrix`.

## Step 19. Freeze Ben_Kim ping-run contract
### После одного пользовательского пинга `Ben_Kim` должен
1. определить целевой `symbol`;
2. адресовать нужные 12 машин через registry;
3. получить 12 machine outputs;
4. преобразовать их в symbol objects;
5. проставить object-level readiness;
6. подготовить batch к handoff в object storage.

### Отдельно определить
- как выглядит один `ping-run`;
- когда допустим partial batch;
- когда run считается failed;
- как маркируется incomplete run;
- как логируются `request_id` и `batch_id`;
- как обрабатывается retry того же symbol-run.

### Result of the step
- `Ben_Kim ping-run contract`.

---

# PHASE 3E — STORAGE HANDOFF READINESS

## Goal of Phase 3E
Довести outputs до состояния, в котором они уже готовы к отдельному object-storage domain без смешения с tick storage semantics.

## Step 20. Freeze storage-ready envelope
### Обязательные поля
- `symbol`;
- `strategy`;
- `timeframe`;
- `machine_id`;
- `agent_id`;
- `request_id`;
- `generated_at`;
- `status`;
- `summary`;
- `meta`;
- `features`;
- `errors`;
- `response_contract_version`.

### Ключевое правило
`one machine response = one storage object`.

### Result of the step
- `storage-ready envelope`.

## Step 21. Freeze object-storage write contract
### Нужно зафиксировать
- single-object write shape;
- batch write shape на 12 objects;
- idempotency rule;
- duplicate handling policy;
- overwrite vs append-only policy;
- schema validation behavior;
- обязательные audit fields;
- допустимо ли хранить `partial` и `blocked` objects и как они маркируются.

### Result of the step
- `object storage write contract`.

## Step 22. Freeze batch acceptance rules for 12-object handoff
### Определить
- когда batch считается complete;
- можно ли передавать batch с `partial` objects;
- можно ли передавать batch с `blocked` objects;
- когда нужен fail-fast;
- как маркируется неполный batch;
- нужен ли общий `batch_status`.

### Result of the step
- `batch handoff acceptance rules`.

## Step 23. Validate separation of tick storage and object storage domains
### Нужно подтвердить
- object storage не становится source-of-truth для входных тиков;
- tick storage не используется как storage для machine outputs;
- деградация tick storage отражается в runtime/status/errors, а не маскируется packaging-слоем;
- деградация object storage не меняет semantics input-read contract;
- ownership boundaries между compute, tick storage и object storage остаются явными.

### Result of the step
- `dual-storage separation validation report`.

---

# PHASE 3F — FINAL ACCEPTANCE AND REPORTING

## Step 24. Produce PHASE 3 report
### В финальном отчёте должно быть
- результаты `12-machine integration validation`;
- contract completeness matrix;
- status honesty report;
- warmup behavior validation;
- failure taxonomy reconciliation;
- runtime readiness matrix;
- первый `BTC package` из 12 objects;
- packaging fidelity report;
- object readiness matrix;
- storage-ready envelope confirmation;
- batch acceptance rules;
- dual-storage separation confirmation;
- список blockers;
- список known limitations;
- итоговый verdict:
  - `PHASE 3 accepted`;
  - или `PHASE 3 partial`;
  - или `PHASE 3 blocked`.

### Result of the step
- `PHASE_3_REPORT.md`.

---

# DEFINITION OF DONE FOR PHASE 3

`PHASE 3` считается завершённой только если одновременно выполнено всё ниже:
- на одном и том же `BTCUSDC` baseline прогнаны все 12 машин;
- по каждой машине есть runtime readiness verdict;
- подтверждена честность `ready / partial / error`;
- подтверждено соблюдение warmup policy;
- сверены фактические emitted errors и agreed failure taxonomy;
- `Ben_Kim` умеет собрать ровно 12 symbol-scoped objects по одному symbol;
- сформирован первый `BTCUSDC` batch из 12 отдельных objects;
- по каждому object есть object-level readiness verdict;
- зафиксирован storage-ready envelope;
- зафиксирован object-storage write contract;
- зафиксированы batch acceptance rules;
- подтверждена separation between tick storage and object storage;
- подтверждена end-to-end traceability на всём пути от API access до storage handoff;
- выпущен `PHASE_3_REPORT.md`.

---

# BLOCKERS FOR PHASE 3

Следующее считается blocker:
- хотя бы одна машина не может быть стабильно вызвана через frozen registry;
- response schema ломается или не трактуется downstream;
- traceability fields отсутствуют или несогласованы;
- status semantics не совпадают с фактическим качеством входа;
- failure taxonomy настолько расходится с runtime, что orchestration не понимает retryability;
- `Ben_Kim` не может собрать ровно 12 отдельных objects по `BTCUSDC`;
- packaging теряет identity, status или quality flags;
- object envelope не позволяет безопасный downstream write;
- runtime-машины обходят agreed API-read contour;
- object write semantics не обеспечивают идемпотентность, auditability или separation от tick storage domain.

---

# FINAL COMMENT ON PHASE 3

Оптимальная последовательность теперь такая:
- сначала заморозить baseline и критерии приёмки;
- затем подготовить всё, что можно без API-ключа;
- затем вручную прогнать live validation на одном canonical symbol;
- затем проверить упаковку `Ben_Kim` в 12 отдельных objects;
- затем довести objects до storage-ready handoff.

Это лучше старой версии плана по двум причинам:
- не путает уже завершённую `PHASE 2` с текущей фазой;
- честно разделяет offline-prep и manual API-validation, что особенно важно при отсутствии ключа у исполнителя.
