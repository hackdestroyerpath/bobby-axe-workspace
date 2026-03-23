# TODO

# PHASE 3 — INTEGRATION VALIDATION, BTC PACKAGING, STORAGE HANDOFF READINESS

## Goal
Подтвердить, что реализованный в `PHASE 2` contract-first runtime реально работает как единый operational contour для `Ben_Kim`:
- все 12 машин реально исполняемы;
- их outputs реально пригодны для orchestration;
- `Ben_Kim` реально умеет собирать по `symbol` 12 отдельных объектов;
- эти объекты реально можно передавать дальше в storage-ready форме;
- переход от machine response к symbol-scoped storage unit зафиксирован и проверяем.

## Context after Phase 2
`PHASE 2` уже дала готовую операционную базу:
- frozen registry в `machine_registry.py`;
- единый status model `ready / partial / error` в `runtime_contract.py`;
- 4 shared family-core слоя в `strategy_cores.py`;
- shared execution wrappers в `machines.py`;
- orchestration expectations в `BEN_KIM_ORCHESTRATION_CONTRACT.md`;
- тестовое покрытие runtime baseline в `tests/test_phase2_runtime.py` и `tests/test_strategy_cores.py`.

Значит `PHASE 3` должна быть не про изобретение новой архитектуры, а про:
1. integration validation;
2. packaging layer для `Ben_Kim`;
3. storage handoff readiness.

## Additional architectural assumptions for this Phase
Для текущего operational contour отдельно фиксируется следующее:
- сами вычисления и strategy-specific манипуляции выполняются на стороне 12 отдельных машин / алгоритмов;
- канонические входные тики хранятся централизованно в SQL storage под контуром `Jack`;
- доступ к входным тикам для runtime-машин должен идти через API contract, а не через произвольное прямое чтение SQL из strategy-layer;
- результаты машин после вызова собираются `Ben_Kim` в 12 отдельных symbol-scoped objects;
- эти objects должны сохраняться в отдельном SQL storage / отдельном storage domain для object layer;
- доступ к object storage также должен идти через API contract;
- tick storage и object storage считаются разными operational domains, даже если позднее окажутся физически размещены в одном инфраструктурном контуре;
- ни одна runtime-машина не считается владельцем данных; машины владеют compute-слоем, но не source-of-truth по входу или storage semantics.

## Additional API access and control assumption
Так как storage-контуры внешне доступны только через API, уже на `PHASE 3` нужно считать обязательным:
- доступ к tick storage только по `API key` / service identity;
- доступ к object storage только по `API key` / service identity;
- обязательную traceability каждого обращения через `request_id`, `api_key_id`, caller identity и timestamp;
- запрет на неаудируемые прямые обращения к storage в обход agreed API contract.

---

# PHASE 3A — RUNTIME INTEGRATION VALIDATION

## Goal of Phase 3A
Проверить, что контур, собранный в `PHASE 2`, реально исполняется как единая система без расхождений между контрактом, runtime-поведением и фактическими error/status semantics.

## Step 1. Freeze validation baseline for BTC
Нужно зафиксировать единый validation baseline для первой полноценной проверки.

### Что зафиксировать
- `symbol = BTCUSDC` как первый canonical validation symbol;
- один `response_contract_version`;
- один `source_contract_version`;
- один базовый test window для первого прогона;
- базовые runtime options:
  - `strict_mode = false`;
  - `include_incomplete_candle = false`;
- отдельный повторный прогон на том же окне для deterministic check.

### Комментарий
Phase 3 нельзя строить на случайных разных входах для разных машин. Нужен один понятный baseline, чтобы сравнение шло по общему контексту, а не по разным рыночным срезам.

### Result of the step
- один `PHASE_3_VALIDATION_BASELINE` для всех дальнейших проверок.

## Step 2. Run all 12 machines on one BTC baseline window
Нужно выполнить первый полный прогон всех 12 машин по одному и тому же BTC baseline window.

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

### Что проверить
- registry-addressing работает без ручных строковых догадок;
- request проходит `validate_request()`;
- shared normalization проходит;
- shared feature engine проходит;
- family-core compute проходит;
- response собирается по единому schema.

### Комментарий
Это первый реальный integration checkpoint. На этом шаге уже нельзя ссылаться только на дизайн-документы — нужно подтверждение реального прогона.

### Result of the step
- первый `BTC full 12-machine integration run`.

## Step 2A. Validate centralized tick access semantics through API-backed read layer
Нужно отдельно проверить, что переход к централизованному хранению тиков не ломает Phase 1/2 contracts и не размывает ownership границ между compute и storage.

### Что проверить
- ни одна из 12 машин не читает тики напрямую из произвольного SQL-path в обход agreed read layer;
- чтение идёт только через единый API-backed access contract поверх канонического tick storage;
- API-backed read layer не меняет semantics, уже зафиксированные в `TICK_SOURCE_CONTRACT.md` и `COMMON_TICK_READ_SPEC.md`;
- сохраняются inclusive boundaries окна, canonical ordering и pagination stability;
- `source`, `symbol`, window boundaries и traceability источника доходят до runtime без искажения;
- partial semantics не теряются на API-слое:
  - `retention_truncation`;
  - `pagination_truncation`;
  - `gap_heavy_window`;
  - `empty_window`.

### Blocker conditions
- хотя бы одна машина может operationally обходить agreed API-read contract;
- API read layer ломает deterministic ordering или window semantics;
- traceability входного чтения исчезает или становится неполной;
- degraded input на API/read boundary маскируется как нормальный complete read.

### Result of the step
- `tick API read validation report`.

## Step 3. Validate contract completeness against actual runtime
Нужно проверить, что runtime реально возвращает то, что обещает общий response contract.

### Проверять
- top-level response fields;
- `status`;
- `summary`;
- `meta`;
- `errors`;
- strategy-specific `features`;
- traceability fields:
  - `machine_id`;
  - `api_key_id`;
  - `build_version`;
  - `source_contract_version`;
  - `coverage_ratio`;
  - `is_partial`;
  - `partial_reason`.

### Blocker conditions
- critical top-level fields отсутствуют;
- response schema формально невалиден;
- traceability поля не совпадают с runtime expectations;
- machine output нельзя однозначно трактовать downstream.

### Result of the step
- `contract completeness matrix` по всем 12 машинам.

## Step 4. Validate status honesty
Это один из ключевых шагов всей фазы.

### Нужно доказать
- `ready` не рисуется при degraded input;
- `partial` не теряется между runtime и downstream interpretation;
- `error` не маскируется как usable packet.

### Отдельно проверить
- `retention_truncation`;
- `pagination_truncation`;
- `gap_heavy_window`;
- `empty_window`.

### Комментарий
Status model уже существует в `runtime_contract.py`. Теперь нужно проверить, что она operationally выдерживается и не ломается на реальном исполнении.

### Result of the step
- `status honesty report`.

## Step 5. Validate warmup behavior per machine family
Warmup policy уже зафиксирована в frozen registry. Теперь её нужно проверить на практике.

### Проверить
- `RSI_MACD` не даёт вид ready без достаточного числа candles;
- `LEVELS_FIBO_HV` не делает сильные structural claims без глубины окна;
- `VOLUME` не даёт сильный вывод без адекватного baseline;
- `ELLIOTT` не поднимает confidence на слабой структуре.

### Комментарий
Если warmup-политика существует только в коде, но не выдерживается в фактическом output, то Phase 2 формально есть, а operational discipline нет.

### Result of the step
- `warmup behavior validation` по всем 4 strategy families.

## Step 6. Validate failure catalog vs actual emitted errors
Это прямое следствие ограничений, зафиксированных в `PHASE_2_REPORT.md`.

### Нужно сделать
- собрать реально эмитируемые error codes из runtime;
- сравнить их с `FAILURE_MODE_MATRIX`;
- сравнить их с retry semantics из orchestration contract;
- выделить три класса:
  - полностью синхронизировано;
  - частично синхронизировано;
  - требует формализации.

### Особое внимание
- `READ_TIMEOUT` фигурирует в retry expectations, но не полностью синхронизирован как template failure code;
- runtime-generated коды вроде `INPUT_GAP_DETECTED` и `EMPTY_WINDOW` должны быть приведены к общей taxonomy или явно описаны как sanctioned exceptions.

### Result of the step
- `failure taxonomy reconciliation report`.

## Step 7. Mark per-machine runtime readiness
После валидации каждой машине нужно присвоить итоговый runtime readiness verdict.

### Допустимые статусы
- `ready`;
- `partial`;
- `blocked`.

### Правила
#### ready
- response schema complete;
- status semantics честные;
- warmup behavior корректен;
- payload usable downstream.

#### partial
- машина operationally работает;
- но есть контролируемые ограничения, которые нельзя скрывать.

#### blocked
- есть contract mismatch;
- broken schema;
- unstable runtime;
- некорректные status/error semantics;
- или response нельзя использовать как downstream unit.

### Result of the step
- `12-machine runtime readiness matrix`.

---

# PHASE 3B — BEN_KIM SYMBOL PACKAGING LAYER

## Goal of Phase 3B
Проверить, что `Ben_Kim` умеет работать не только как наблюдатель runtime, но и как packaging layer, который после пинга по symbol формирует 12 отдельных symbol-scoped objects.

## Step 8. Freeze symbol-object contract
Нужно зафиксировать, что считается одним итоговым объектом `Ben_Kim`.

### Один объект =
`1 symbol + 1 strategy + 1 timeframe + 1 machine response`

### Минимально обязательные поля объекта
- `symbol`;
- `strategy`;
- `timeframe`;
- `machine_id`;
- `agent_id`;
- `status`;
- `summary`;
- `meta`;
- `features`;
- `request_id`;
- `generated_at`.

### Обязательные quality / traceability fields
- `is_partial`;
- `partial_reason`;
- `coverage_ratio`;
- `data_points`;
- `build_version`;
- `source_contract_version`;
- `api_key_id`.

### Additional object identity and storage fields
Для distributed compute + centralized storage contour нужно дополнительно зафиксировать:
- `object_id` как уникальный identity ключ объекта;
- `batch_id` как identity одного `ping-run` / batch-сборки;
- `storage_written_at` как отдельное поле фактической записи в object storage;
- `input_window_from`;
- `input_window_to`;
- `executor_node` или иной `compute_origin`, если это поле доступно в runtime контуре.

### Additional idempotency rule
Нужно заранее определить stable idempotency basis для повторной записи объекта, чтобы retries не создавали неконтролируемые дубли.

Минимально acceptable basis:
- `symbol + strategy + timeframe + request_id`;
или
- `symbol + strategy + timeframe + batch_id`.

### Комментарий
Это уже не просто response sub-agent машины. Это единица хранения и оркестрации для следующего этапа.

### Result of the step
- `Ben_Kim symbol object contract`.

## Step 9. Build the first BTC package of 12 objects
После пинга на `BTCUSDC` `Ben_Kim` должен собрать ровно 12 отдельных объектов.

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
Это должны быть именно 12 отдельных objects, а не один merged blob или один свободный summary.

### Additional storage-facing expectation
Собранный пакет должен быть пригоден не только для чтения orchestration-слоем, но и для последующей idempotent записи в отдельный object storage domain через agreed API contract.

### Result of the step
- первый `BTC package` из 12 отдельных objects.

## Step 10. Validate packaging fidelity
Нужно проверить, что при упаковке machine response → symbol object ничего не искажается и не теряется.

### Проверять
- не теряется `machine_id`;
- не теряется `strategy` и `timeframe`;
- не теряется `status`;
- не теряется `partial_reason`;
- не теряется traceability;
- `summary` и `features` не искажаются;
- `error` packets не превращаются в usable objects без маркировки.

### Дополнительно проверить
- не теряются `object_id` и `batch_id`;
- не теряются `input_window_from` / `input_window_to`, если они объявлены частью symbol-object contract;
- не ломается idempotency basis при повторной упаковке того же run;
- object-level payload остаётся пригодным для downstream API-write без дополнительной ручной нормализации.

### Комментарий
Если runtime правильный, но packaging деформирует объект, downstream storage и orchestration будут строиться на испорченном контуре.

### Result of the step
- `packaging fidelity report`.

## Step 11. Freeze object-level readiness rules
Нужно отдельно зафиксировать readiness не только для машины, но и для итогового symbol object.

### Допустимые object-level статусы
- `ready`;
- `partial`;
- `blocked`.

### Логика
Даже если машина отдала response, итоговый object всё ещё может быть:
- плохо упакован;
- лишён traceability;
- некорректно промаркирован;
- непригоден для storage handoff.

### Дополнительное правило для distributed storage contour
Object-level readiness должен учитывать не только корректность packaging, но и пригодность объекта для записи через agreed object-storage API contract без потери identity, статуса, quality flags и audit fields.

### Result of the step
- `12-object readiness matrix`.

## Step 12. Define Ben_Kim ping-run behavior
Нужно формально зафиксировать, как работает запуск после пользовательского пинга по symbol.

### После пинга `Ben_Kim` должен
1. определить целевой `symbol`;
2. адресовать нужные 12 машин через frozen registry;
3. получить 12 machine outputs;
4. привести их к symbol-object contract;
5. пометить object-level readiness;
6. подготовить batch к передаче в storage layer.

### Отдельно определить
- как выглядит один `ping-run`;
- когда допустим partial batch;
- когда run считается failed;
- как маркируется incomplete 12-object run;
- можно ли временно вернуть degraded batch без полной остановки контура.

### Дополнительно определить API-run semantics
- какие `API keys` / identities могут запускать `ping-run`;
- как логируется batch-level `request_id` / `batch_id`;
- как маркируется повторный запуск того же symbol-run;
- как batch готовится к идемпотентной записи в object storage.

### Result of the step
- `Ben_Kim ping-run contract`.

---

# PHASE 3C — STORAGE HANDOFF READINESS AND ACCEPTANCE

## Goal of Phase 3C
Довести `Ben_Kim` outputs до состояния, где они уже готовы передаваться дальше как storage-ready units, даже если финальная production-инструкция для `Jack` будет уточняться отдельно.

## Step 13. Freeze storage-ready envelope
Нужно зафиксировать форму одного storage-ready объекта.

### Обязательные поля envelope
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

### Комментарий
Это точка перехода от runtime semantics к storage discipline. Объект должен быть self-contained и downstream-readable.

### Result of the step
- `storage-ready envelope` для `Ben_Kim -> Jack`.

## Step 13A. Freeze object-storage write contract
Нужно отдельно зафиксировать не только shape объекта, но и сам write contract для отдельного object storage domain.

### Что зафиксировать
- допустимую форму single-object write;
- допустимую форму batch write на 12 objects;
- правила idempotency при retry;
- duplicate handling policy;
- overwrite vs append-only policy;
- object versioning policy, если она требуется;
- schema validation behavior при object write;
- audit fields, обязательные при каждой записи;
- допустимо ли хранить `partial` и `blocked` objects и как они маркируются в storage.

### Комментарий
Storage-ready object без explicit write semantics недостаточен. Для `PHASE 3` нужно заранее зафиксировать, как именно object layer принимает и хранит эти units.

### Result of the step
- `object storage write contract`.

## Step 14. Define batch acceptance rules for 12-object handoff
Нужно зафиксировать правила приёма полного пакета по symbol.

### Определить
- когда 12-object batch считается complete;
- можно ли передавать batch с `partial` objects;
- можно ли передавать batch с `blocked` objects;
- когда нужен fail-fast;
- как маркировать неполный batch;
- нужен ли общий `batch_status`.

### Комментарий
`Jack` не должен получить 9 объектов из 12 без явной маркировки, что пакет деградирован и почему именно.

### Result of the step
- `batch handoff acceptance rules`.

## Step 14A. Validate separation of tick storage and object storage domains
Нужно отдельно доказать, что в новом contour не смешиваются два storage domain: входной tick storage и downstream object storage.

### Что проверить
- object storage не используется как source-of-truth для входных тиков;
- tick storage не используется как место хранения machine outputs / symbol objects;
- деградация object storage не подменяет semantics tick read contract;
- деградация tick storage корректно отражается в runtime/status/errors, а не маскируется через object layer;
- ownership границы между compute, tick storage и object storage остаются явными и проверяемыми.

### Result of the step
- `dual-storage separation validation report`.

## Step 15. Produce PHASE 3 report
По завершении фазы должен быть подготовлен формальный отчёт.

### В отчёте должно быть
- результаты 12-machine integration validation;
- reconciliation по failure taxonomy;
- готовность packaging layer;
- готовность первого `BTC package` из 12 объектов;
- storage handoff readiness;
- список blockers;
- список known limitations;
- итоговое решение:
  - `PHASE 3 accepted`;
  - или `PHASE 3 partial`;
  - или `PHASE 3 blocked`.

### Дополнительно в отчёте должно быть
- подтверждение API-backed tick access semantics;
- подтверждение готовности object-storage write contract;
- подтверждение separation между tick storage и object storage;
- подтверждение end-to-end traceability пути `API key -> machine call -> packaged object -> object storage write`.

### Result of the step
- `PHASE_3_REPORT.md`.

---

# DEFINITION OF DONE FOR PHASE 3

`PHASE 3` считается завершённой только если одновременно выполнено всё ниже:
- на `BTCUSDC` прогнаны все 12 машин;
- по каждой машине есть runtime readiness verdict;
- сверены фактические emitted errors и failure taxonomy;
- подтверждена честность `ready / partial / error`;
- подтверждено соблюдение warmup policy;
- `Ben_Kim` умеет собирать 12 symbol-scoped objects по одному symbol;
- сформирован первый `BTCUSDC` batch из 12 объектов;
- по каждому объекту есть object-level readiness verdict;
- зафиксирован storage-ready envelope;
- зафиксированы batch acceptance rules;
- выпущен `PHASE_3_REPORT.md`;
- подтверждено, что все 12 машин читают входные тики только через agreed API-backed central tick storage contract;
- подтверждено, что `Ben_Kim` сохраняет 12 symbol objects через отдельный object-storage API contract;
- подтверждена idempotent write semantics для object layer;
- подтверждена end-to-end traceability на всём пути от API access до storage write.

---

# BLOCKERS FOR PHASE 3

Следующее считается blocker:
- хотя бы одна машина не может быть стабильно вызвана через frozen registry;
- response schema ломается на runtime;
- traceability fields отсутствуют или несогласованы;
- status semantics не совпадают с фактическим качеством входа;
- failure taxonomy расходится с реальным runtime так, что orchestration не может надёжно трактовать retryability;
- `Ben_Kim` не может собрать ровно 12 отдельных objects по `BTCUSDC`;
- object-level packaging теряет identity, status или quality flags;
- storage-ready envelope не позволяет downstream хранить объект как отдельную единицу;
- runtime-машины обходят agreed API-read contour и читают входные данные вне зафиксированного доступа;
- object write semantics не позволяют обеспечить идемпотентность, auditability или separation от tick storage domain.

---

# FINAL COMMENT ON PHASE 3

После фактически реализованной `PHASE 2` следующая фаза должна быть не про новую архитектуру, а про проверку её работоспособности в бою на одном символе и подготовку `Ben_Kim` к роли operational layer между machine runtime и storage.

Правильная последовательность теперь такая:
- сначала проверить, что 12-machine runtime реально работает как единый контур;
- потом научить `Ben_Kim` упаковывать outputs в 12 symbol-scoped objects;
- потом довести эти объекты до storage-ready handoff.

Именно так `PHASE 3` превращает уже собранную contract-first систему в operationally usable pipeline.

## Additional final clarification for current architecture
С учётом нового решения по размещению данных `PHASE 3` теперь должна также подтвердить ещё одну вещь:
- compute живёт на стороне 12 машин;
- входные тики живут в centralized tick SQL storage под API-контролем;
- outputs машин живут в separate object SQL storage под API-контролем;
- orchestration обязан сохранять separation между compute, tick storage и object storage, а не смешивать их в один неформальный runtime blob.
