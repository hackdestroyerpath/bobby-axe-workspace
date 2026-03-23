# TODO

## Current status
- `PHASE 1` закрыта и подтверждена в `TRADING_ALGOS/PHASE_1_REPORT.md`.
- Канонические артефакты общей базы уже существуют:
  - `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
  - `TRADING_ALGOS/COMMON_TICK_READ_SPEC.md`
  - `TRADING_ALGOS/common/tick_normalizer.py`
  - `TRADING_ALGOS/common/tick_to_features_engine.py`
  - `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.*`
  - `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.*`
- В `TODO.md` больше не держим план по уже выполненной `PHASE 1`, чтобы не смешивать закрытый фундамент и актуальные следующие шаги.

---

# PHASE 2 — PREPARE AND BUILD 12 STRATEGY MACHINES ON TOP OF PHASE 1

## Goal
Перевести `PHASE 1` из уровня «контракты и общая база готовы» в уровень «12 машин можно поднимать без расхождения по runtime, входу, качеству и интерпретации».

`PHASE 2` теперь не про придумать стратегии заново, а про аккуратное доведение до рабочего контура уже зафиксированной архитектуры:
- `TICK_SOURCE_CONTRACT.md` остаётся единственным source-of-truth по входу;
- `COMMON_TICK_READ_SPEC.md` остаётся единственным read-contract;
- `common/tick_normalizer.py` обязателен для всех машин;
- `common/tick_to_features_engine.py` обязателен для всех машин;
- `SUBAGENT_REQUEST_FORMAT.*` и `SUBAGENT_RESPONSE_FORMAT.*` остаются общим transport contract.

## Что изменилось после сильной Phase 1
`PHASE 1` закрыта и удалена из operational backlog.
Теперь главная задача — не пересобирать базу, а не испортить её при реализации машин.

### Главный принцип Phase 2
Каждая машина должна добавлять только `strategy-specific compute layer`.
Она не должна:
- придумывать свой способ читать тики;
- локально переагрегировать вход в обход shared engine;
- по-своему трактовать `partial/gaps/pagination`;
- возвращать свой transport format;
- скрывать ограничения данных или симулировать уверенность там, где её нет.

### Ключевые риски, которые надо закрыть в этой фазе
На основе `PHASE_1_REPORT.md` в реализацию `PHASE 2` обязательно заложить:
- контроль retention как operational constraint, а не как предположение;
- контроль pagination/runtime drift при чтении `/ticks`;
- одинаковую реакцию всех стратегий на `partial` окна;
- явное разделение между shared features и strategy-specific features;
- machine-level runtime discipline: одна машина = один `machine_id` = один runtime contract = один набор failure modes.

---

# PHASE 2A — CROSS-CUTTING PREPARATION BEFORE CODING 12 MACHINES

## Step 1. Freeze machine registry for all 12 executors
До реализации логики создать жёсткий реестр всех 12 машин.

### Что зафиксировать
Для каждой машины отдельно зафиксировать:
- `machine_id`
- `agent_id`
- `strategy`
- `timeframe`
- `human_name`
- `input_timeframe_target`
- `primary_output_packet`
- `runtime_entrypoint`
- `api_key_id`
- `build_version_policy`
- `owner`

### Полный список машин
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

### Комментарий
Это нужно сделать до кода, чтобы потом не появилось 12 почти одинаковых, но operationally разных исполнителей.

### Результат шага
- один `machine registry` на все 12 машин;
- у каждой машины есть жёсткая identity и runtime-привязка.

## Step 2. Freeze common runtime pipeline for every machine
Нужно заранее зафиксировать один и тот же lifecycle вызова для всех машин.

### Канонический pipeline
1. принять request по общему schema;
2. проверить обязательные поля запроса;
3. проверить доступную глубину окна относительно retention;
4. прочитать тики через общий read contract;
5. прогнать данные через `tick_normalizer`;
6. прогнать `normalized ticks` через `tick_to_features_engine`;
7. посчитать только strategy-specific indicators;
8. собрать `summary`;
9. выставить `status` и `meta`;
10. вернуть response по общему schema.

### Что запретить явно
- strategy code не должен ходить в таблицу напрямую в обход общего read layer;
- strategy code не должен сам считать quality flags, если они уже есть из shared pipeline;
- strategy code не должен переписывать `status` без связи с `meta.is_partial` и `errors`.

### Комментарий
Если это не зафиксировать до реализации, `PHASE 1` формально останется, но фактически каждая машина снова станет отдельным мини-проектом.

### Результат шага
- один runtime execution contract для всех 12 машин.

## Step 3. Freeze partial-data policy before strategy logic
До реализации индикаторов нужно утвердить реакцию на неидеальные входные окна.

### Что определить
Для всех 12 машин одинаково определить:
- когда окно считается `ready`;
- когда окно считается `partial`;
- когда ответ должен быть `error`;
- какие `partial_reason` передаются дальше без переименования;
- можно ли считать strategy-specific indicators на partial окне;
- какие поля обязаны оставаться заполненными даже при `partial`;
- когда `summary.confidence` понижается автоматически из-за качества входа.

### Минимальная operational логика
- `retention_truncation` не маскировать как нормальное окно;
- `pagination_truncation` не маскировать как complete read;
- `empty_window` не превращать в нейтральный market opinion;
- `gap_heavy_window` должен снижать confidence и явно отражаться в `errors/meta`.

### Комментарий
Это критично, потому что проблема в runtime обычно не в самой формуле RSI или Fibonacci, а в том, что стратегия делает вид, будто вход полон и чист.

### Результат шага
- единая policy обработки `ready / partial / error` для всех 12 машин.

## Step 4. Freeze warmup policy per timeframe and per strategy family
Shared engine уже даёт базовые candles/features, но стратегии не смогут считаться без минимального окна истории.

### Что определить
Для каждой strategy-family и каждого timeframe зафиксировать:
- минимальный warmup window;
- рекомендуемый рабочий window;
- минимальное число свечей для valid output;
- поведение при недостаточном warmup;
- является ли выход `partial` или `error`, если warmup не добран.

### Обязательные комментарии по стратегиям
- `RSI_MACD`: warmup нужен не только для `RSI(14)`, но и для устойчивого `MACD/EMA`-состояния;
- `LEVELS_FIBO_HV`: нужен диапазон, достаточный для swing detection и volume profile, иначе уровни будут случайными;
- `VOLUME`: relative volume без baseline-window бессмысленен;
- `ELLIOTT`: самый требовательный к структуре и самый опасный с точки зрения ложной уверенности.

### Результат шага
- одна таблица warmup-требований на 12 машин.

## Step 5. Freeze summary generation rules
Поскольку у всех машин общий response schema, надо заранее описать, как строится `summary`.

### Что определить
Для каждой strategy-family нужно зафиксировать:
- как вычисляется `summary.state`;
- как выставляется `summary.strength`;
- как ограничивается `summary.confidence`;
- какие strategy-specific conditions обязательно попадают в `summary.note`;
- как quality flags влияют на итоговый summary.

### Комментарий
Без этого 12 машин формально будут возвращать одинаковый schema, но фактически будут разговаривать на 12 разных языках.

### Результат шага
- единая policy построения `summary` поверх strategy-specific output.

---

# PHASE 2B — IMPLEMENT STRATEGY FAMILY: RSI_MACD

## Step 6. Build shared RSI_MACD compute module
Сначала не делать 3 независимые реализации, а один общий strategy-core для семейства `RSI_MACD`.

### Что должно быть внутри
- вход: candles и общие microstructure fields из shared engine;
- расчёт `RSI(14)`;
- расчёт `EMA(12)`;
- расчёт `EMA(26)`;
- расчёт `MACD line`;
- расчёт `signal line`;
- расчёт `histogram`;
- derivation для `rsi_zone`;
- derivation для `rsi_slope`;
- derivation для `macd_state`;
- derivation для `hist_state`;
- derivation для `momentum_state`;
- derivation для `momentum_strength`.

### Что проверить концептуально
- формулы должны работать одинаково на `1m`, `5m`, `60m`;
- различаться должен timeframe input, а не business logic;
- incomplete last candle не должен бездумно искажать momentum-вывод.

### Комментарий
Сначала один reusable family-core, потом уже 3 runtime-машины.

### Результат шага
- один reusable `RSI_MACD` strategy-core.

## Step 7. Wrap RSI_MACD into 3 machine executors
После family-core поднять:
- `RSI_MACD_1M`
- `RSI_MACD_5M`
- `RSI_MACD_60M`

### Для каждой машины отдельно зафиксировать
- какой timeframe она запрашивает у shared engine;
- какой warmup обязателен;
- какие output fields обязательны;
- какие downgrade rules по confidence применяются;
- какие failure modes считаются retryable.

### Обязательные поля семейства
- `timestamp`
- `timeframe`
- `rsi_value`
- `rsi_zone`
- `rsi_slope`
- `macd_line`
- `signal_line`
- `macd_hist`
- `macd_state`
- `hist_state`
- `momentum_state`
- `momentum_strength`

### Результат шага
- 3 отдельные runtime-машины семейства `RSI_MACD`.

---

# PHASE 2C — IMPLEMENT STRATEGY FAMILY: LEVELS_FIBO_HV

## Step 8. Build shared LEVELS_FIBO_HV compute module
Собрать один strategy-core для семейства `LEVELS_FIBO_HV`.

### Что должно быть внутри
- swing detection на shared candles;
- выделение локальных support / resistance;
- выбор последнего рабочего swing range;
- расчёт Fibonacci levels по этому range;
- horizontal volume profile;
- `POC`;
- `value_area_high`;
- `value_area_low`;
- derivation контекстных полей по отношению цены к уровням.

### Обязательные design-решения
Надо заранее зафиксировать:
- как считается swing high / swing low;
- что считать «рабочим» swing range;
- как выбирать levels при конфликте нескольких swing-структур;
- как строить volume profile по окну;
- как определять `near` для `fib/POC/levels`;
- что делать, если структуры недостаточно.

### Результат шага
- один reusable `LEVELS_FIBO_HV` strategy-core.

## Step 9. Wrap LEVELS_FIBO_HV into 3 machine executors
Поднять:
- `LEVELS_FIBO_HV_1M`
- `LEVELS_FIBO_HV_5M`
- `LEVELS_FIBO_HV_60M`

### Обязательные поля семейства
- `nearest_support`
- `nearest_resistance`
- `distance_to_support`
- `distance_to_resistance`
- `nearest_fib_ratio`
- `nearest_fib_level`
- `price_vs_fib`
- `hv_poc`
- `value_area_high`
- `value_area_low`
- `inside_value_area`
- `price_vs_poc`
- `structure_state`
- `level_context_strength`

### Специальные комментарии
- `1m` должен быть наиболее консервативным по structural claims;
- `60m` требует самого аккуратного контроля retention depth;
- если swing structure неубедительна, машина должна честно снижать confidence, а не дорисовывать уровни.

### Результат шага
- 3 отдельные runtime-машины семейства `LEVELS_FIBO_HV`.

---

# PHASE 2D — IMPLEMENT STRATEGY FAMILY: VOLUME

## Step 10. Build shared VOLUME compute module
Сначала собрать общий strategy-core для семейства `VOLUME`.

### Что должно быть внутри
- `current_volume`;
- `avg_volume`;
- `relative_volume`;
- `volume_spike_flag`;
- `buy_volume` и `sell_volume` как strategy payload поверх shared base;
- `volume_delta`;
- `imbalance_ratio`;
- derivation `pressure_side`;
- derivation `volume_confirmation_state`;
- derivation `flow_strength`.

### Что нужно уточнить заранее
- какое окно брать для `avg_volume`;
- что считать baseline для `relative_volume`;
- как отличать spike от обычного ускорения;
- как интерпретировать высокий объём против движения цены;
- как incomplete last candle влияет на текущий volume reading.

### Результат шага
- один reusable `VOLUME` strategy-core.

## Step 11. Wrap VOLUME into 3 machine executors
Поднять:
- `VOLUME_1M`
- `VOLUME_5M`
- `VOLUME_60M`

### Обязательные поля семейства
- `current_volume`
- `avg_volume`
- `relative_volume`
- `volume_spike_flag`
- `buy_volume`
- `sell_volume`
- `volume_delta`
- `imbalance_ratio`
- `pressure_side`
- `volume_confirmation_state`
- `flow_strength`

### Специальные комментарии
- нельзя путать volume pressure с directional signal;
- volume spike должен оставаться контекстом, а не магическим trigger;
- если volume baseline невалиден, итог обязан понижаться минимум до `partial` или low-confidence.

### Результат шага
- 3 отдельные runtime-машины семейства `VOLUME`.

---

# PHASE 2E — IMPLEMENT STRATEGY FAMILY: ELLIOTT

## Step 12. Build shared ELLIOTT compute module
Это семейство нужно строить самым последним, после всех более детерминированных слоёв.

### Что должно быть внутри
- pivot highs / lows;
- short and medium swings;
- local trend structure;
- candidate patterns;
- Elliott candidate families;
- derivation для `trend_state`;
- derivation для `structure_state`;
- derivation для `current_leg_direction`;
- derivation для `current_leg_strength`;
- derivation для `correction_depth_state`;
- derivation для `pattern_candidate`;
- derivation для `pattern_state`;
- derivation для `elliott_candidate_family`;
- derivation для `elliott_direction_candidate`;
- derivation для `elliott_confidence_state`.

### Жёсткие ограничения
- `candidate != confirmed` должно быть зашито в runtime и wording;
- default confidence — low, пока нет сильного подтверждения;
- при data gaps или partial input confidence нельзя повышать;
- нельзя возвращать псевдо-точные Elliott labels при слабой структуре.

### Результат шага
- один reusable `ELLIOTT` strategy-core.

## Step 13. Wrap ELLIOTT into 3 machine executors
Поднять:
- `ELLIOTT_1M`
- `ELLIOTT_5M`
- `ELLIOTT_60M`

### Обязательные поля семейства
- `trend_state`
- `structure_state`
- `current_leg_direction`
- `current_leg_strength`
- `correction_depth_state`
- `pattern_candidate`
- `pattern_state`
- `elliott_candidate_family`
- `elliott_direction_candidate`
- `elliott_confidence_state`

### Специальные комментарии
- `1m` почти всегда должен оставаться максимально осторожным;
- `60m` полезнее структурно, но сильнее зависит от глубины истории;
- при недостатке структуры машина должна честно говорить `unclear`, а не сочинять wave narrative.

### Результат шага
- 3 отдельные runtime-машины семейства `ELLIOTT`.

---

# PHASE 2F — OPERATIONAL HARDENING OF ALL 12 MACHINES

## Step 14. Standardize machine-specific failure modes
После реализации strategy families отдельно описать failure mode matrix для всех 12 машин.

### Для каждой машины определить
- input validation failures;
- retention failures;
- pagination/read failures;
- normalization failures;
- insufficient warmup failures;
- feature computation failures;
- output schema failures;
- transport failures.

### Что важно
У каждого failure mode должно быть:
- machine-readable `code`;
- `severity`;
- `scope`;
- `retryable` флаг;
- понятное сообщение для orchestration layer.

### Результат шага
- одна failure-mode matrix по всем 12 машинам.

## Step 15. Standardize build/version metadata
До передачи в orchestration слой нужно обеспечить traceability.

### Что обязать для всех машин
Каждый response обязан стабильно нести:
- `machine_id`
- `api_key_id`
- `build_version`
- `source_contract_version`
- `data_points`
- `coverage_ratio`
- `is_partial`
- `partial_reason`

### Результат шага
- traceable meta contract для всех 12 машин.

## Step 16. Freeze orchestration expectations for Ben_Kim
Подготовка к следующей фазе должна начаться уже здесь.

### Что нужно определить заранее
Для `Ben_Kim` на уровне контракта описать:
- как он адресует конкретную машину;
- как он различает `ready / partial / error`;
- какие ошибки он может ретраить;
- какие ответы можно агрегировать;
- какие ответы надо отбрасывать или помечать как degraded;
- как он должен относиться к low-confidence Elliott output;
- как он должен сопоставлять `1m / 5m / 60m` по одной стратегии.

### Результат шага
- machine-to-orchestrator readiness contract.

---

# DEFINITION OF DONE FOR PHASE 2

`PHASE 2` считается подготовленной и завершённой только если одновременно выполнено всё ниже:
- `PHASE 1` не переписан и не обойдён, а реально использован как обязательная база;
- существует единый machine registry на все 12 машин;
- существует один runtime pipeline, обязательный для всех машин;
- существуют family-core реализации для `RSI_MACD`, `LEVELS_FIBO_HV`, `VOLUME`, `ELLIOTT`;
- поверх них подняты 12 отдельных runtime-машин;
- у каждой машины зафиксированы warmup rules, partial rules и failure modes;
- все машины возвращают output в одном response contract;
- ни одна машина не скрывает retention/pagination/gap проблемы под видом normal output;
- summary generation согласована с quality flags;
- подготовлен machine-to-orchestrator contract для следующей фазы.

---

# PHASE 3 — VALIDATION OF EACH MACHINE

## Goal
Проверить, что каждая из 12 машин реально считает то, что должна.

## Step 1. Test each machine on BTC sample windows
Для каждой машины отдельно прогнать тесты на BTC за выбранные окна.

Нужно проверить:
- что машина стартует;
- что читает тики;
- что строит свой ТФ;
- что отдаёт ответ без падения.

## Step 2. Validate output fields
Убедиться, что каждая машина реально возвращает все обязательные поля из своего ТЗ.

Нельзя допускать частичную реализацию без явной маркировки.

## Step 3. Validate semantic correctness
Проверить не только наличие полей, но и смысл:
- RSI должен быть осмысленным;
- MACD не должен быть пустым;
- levels должны строиться из реальных swings;
- volume fields должны соответствовать тиковой реальности;
- Elliott не должен выдавать fake certainty.

## Step 4. Validate consistency across repeated calls
Прогнать повторные запросы по одному и тому же окну.

Проверить:
- детерминированность;
- повторяемость;
- отсутствие хаотического дрейфа.

## Step 5. Mark machine states
Для каждой машины после проверки выставить статус:
- `ready`
- `partial`
- `blocked`

И отдельно фиксировать причину, если машина ещё не `ready`.

---

# PHASE 4 — ORCHESTRATION LAYER FOR BEN_KIM

## Goal
Сделать так, чтобы `Ben_Kim` больше не считал ничего сам, а только оркестрировал 12 машин и собирал ответ.

## Step 1. Define orchestration request plan
Для каждого `symbol` `Ben_Kim` должен уметь запускать 12 запросов:
- 4 стратегии × 3 ТФ

Нужно определить:
- порядок вызова;
- `parallel/serial` режим;
- `timeout policy`;
- `retry policy`.

## Step 2. Define collection layer
`Ben_Kim` должен уметь собирать 12 ответов в один внутренний пакет.

Нужно определить:
- как считать missing response;
- как считать partial response;
- как считать failed response.

## Step 3. Define summarization rules
`Ben_Kim` должен суммаризировать:
- не сырые тики,
- а ответы 12 машин.

Нужно жёстко зафиксировать, что итоговый текст строится на основании:
- strategy outputs
- timeframe outputs
- confidence/strength/status из subagent responses

## Step 4. Define fallback rules
Если часть машин не ответила:
- что считается partial analysis;
- когда можно писать summary;
- когда нельзя делать сильный вывод.

## Step 5. Define operator visibility
Нужно сделать операторский обзор:
- какие из 12 машин ответили;
- какие partial;
- какие failed;
- какой итоговый статус по symbol.

---

# PHASE 5 — DEPLOYMENT AND OPERATION

## Goal
Довести систему до рабочего режима, в котором все 12 машин можно реально поднимать и использовать.

## Step 1. Deploy machines
Поднять все 12 машин по отдельности:
- с их ключами;
- с их runtime;
- с их конфигами.

## Step 2. Register API access
Для каждой машины зафиксировать:
- endpoint;
- api key;
- auth rule;
- allowable request params.

## Step 3. Run first full 12-request cycle
На одном символе выполнить полный цикл:
- 12 запросов
- 12 ответов
- 1 финальный summary от `Ben_Kim`

## Step 4. Observe failure modes
Сразу после первого цикла зафиксировать:
- что падает;
- что медленно;
- что partial;
- где inconsistent output.

## Step 5. Stabilize operational runbook
После первых живых прогонов собрать рабочий runbook:
- как запускать;
- как проверять;
- как чинить;
- как понимать, что всё healthy.

---

# FINAL RESULT

После прохождения всех фаз должно быть:
- 12 отдельных машин;
- единый вход по тикам;
- единый формат ответа;
- `Ben_Kim` как оркестратор, а не счётная машина;
- один сводный текстовый вывод из 12 `strategy/timeframe`-ответов.
