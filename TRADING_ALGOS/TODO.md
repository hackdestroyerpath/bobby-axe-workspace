# TODO

# PHASE 1 — OPTIMIZED CORE DATA FOUNDATION

## Goal
Зафиксировать один реальный контракт чтения и один общий preprocessing-слой, чтобы все 12 машин считали разные стратегии, но на одной и той же базе тиков без расхождения по входу.

## Step 1. Freeze source-of-truth contract
Source-of-truth для входных тиков зафиксировать отдельным документом `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`. Именно этот документ должен быть единственной точкой правды для всех 12 машин и связанных документов.

Что обязан фиксировать контракт:
- таблицу `collector_v2.tick_trade`;
- обязательные поля `source`, `symbol`, `trade_id`, `event_time_utc`, `price`, `quantity`, `side`, `ingested_at_utc`;
- правило, что `side` берётся напрямую, без proxy-логики;
- правило, что все timestamps трактуются только как UTC;
- operational constraint по retention через `RETENTION_DAYS`;
- отдельную процедуру проверки доступной глубины через `MIN(event_time_utc)`, `MAX(event_time_utc)`, `COUNT(*)`.

Артефакт шага:
- один документ `Tick Source Contract`, на который будут ссылаться все 12 машин.

## Step 2. Define one canonical read spec for all subagents
Сделать один общий контракт чтения тиков для всех будущих машин. Этот read spec должен ссылаться на `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md` как на базовый входной контракт и не дублировать его своими словами.

Общий input contract:
- `symbol`
- `timeframe_target`
- `from`
- `to`
- `source = Data_collector`

Общие правила чтения:
- читать только из `collector_v2.tick_trade`;
- фильтрация по `symbol`, `event_time_utc >= from`, `event_time_utc <= to`;
- внутренний канонический порядок данных для расчётов — ascending по `event_time_utc`, затем `trade_id`;
- если чтение идёт через API `/ticks`, учитывать limit/pagination и после получения нормализовать порядок, потому что API/DB сейчас отдают `ORDER BY event_time_utc DESC`;
- границы окна должны быть одинаковыми для всех машин: inclusive-from / inclusive-to, если не будет отдельно утверждено иное.

Нужно исключить ситуацию, где каждая машина:
- сама выбирает sort order;
- сама решает, как пагинировать;
- сама трактует границы окна.

Артефакт шага:
- один `Common Tick Read Spec`
- один canonical SQL template для чтения тиков

## Step 3. Build common tick normalization layer
До любой стратегии сделать единый preprocessing-слой.

Он должен:
- приводить типы (`price`, `quantity`) к единому числовому формату;
- удалять/игнорировать дубли по ключу (`source`, `symbol`, `trade_id`);
- нормализовать порядок тиков в ascending sequence;
- проверять пустые окна;
- фиксировать gaps по времени;
- считать coverage по окну;
- маркировать `partial`, если окно неполное или данные обрезаны retention/pagination.

Минимальные поля результата normalization:
- `tick_count`
- `window_from`
- `window_to`
- `is_partial`
- `partial_reason`
- `gap_count`
- `first_tick_ts`
- `last_tick_ts`

Артефакт шага:
- один reusable `tick_normalizer`, обязательный для всех 12 машин.

## Step 4. Build one shared candle + microstructure engine
Не разделять candle engine и derived fields на два независимых этапа.
Оптимизировать их в один общий переиспользуемый слой, который на входе получает normalized ticks.

Слой должен уметь строить:
- candles: `1m`, `5m`, `60m`
- базовые candle fields:
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
  - `trade_count`
- общие microstructure fields:
  - `buy_volume`
  - `sell_volume`
  - `delta`
  - `imbalance`
  - `trade_speed`
  - `relative_volume_baseline`

Дополнительно надо сразу зафиксировать:
- правила bucket alignment для 1m / 5m / 60m;
- минимальный warmup window для расчётов;
- что делать с пустыми bucket'ами;
- как маркировать incomplete last candle.

Артефакт шага:
- один shared `tick_to_features_engine`, который используют все стратегии.

## Step 5. Freeze common request/response and quality gates
После того как вход и preprocessing стабилизированы, зафиксировать единый request/response transport.

Использовать `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json` как базу.

Дополнительно обязать все машины возвращать в `meta`/`errors` признаки качества входных данных:
- `data_points`
- `is_partial`
- `partial_reason`
- `coverage_ratio`
- `source_contract_version`
- `build_version`

Нужно добиться, чтобы оркестратор понимал не только стратегический вывод, но и качество входного окна.

Артефакт шага:
- единый request schema
- единый response schema
- единые quality flags для всех 12 машин

---

# RESULT OF OPTIMIZED PHASE 1

После завершения этой фазы должно быть:
- один зафиксированный источник тиков через `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`;
- один общий SQL/read contract;
- один normalization layer;
- один shared candle+microstructure engine;
- один response contract;
- ноль расхождений между машинами на уровне входных данных.

---

# PHASE 2 — BUILD 12 STRATEGY MACHINES

## Goal
Поднять все 12 отдельных машин: 4 стратегии × 3 таймфрейма.

## Step 1. Build RSI+MACD machines
Поднять по отдельности:
- RSI_MACD_1M
- RSI_MACD_5M
- RSI_MACD_60M

Каждая машина должна:
- ссылаться на `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md` как на source-of-truth входа;
- читать тики через общий слой;
- строить свой ТФ;
- считать RSI(14), MACD(12,26,9);
- отдавать packet в общем формате.

## Step 2. Build Levels/Fibo/HV machines
Поднять по отдельности:
- LEVELS_FIBO_HV_1M
- LEVELS_FIBO_HV_5M
- LEVELS_FIBO_HV_60M

Каждая машина должна:
- ссылаться на `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md` как на source-of-truth входа;
- строить swings;
- строить support/resistance;
- считать Fibonacci;
- строить horizontal volume / POC / value area;
- отдавать packet в общем формате.

## Step 3. Build Volume machines
Поднять по отдельности:
- VOLUME_1M
- VOLUME_5M
- VOLUME_60M

Каждая машина должна:
- ссылаться на `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md` как на source-of-truth входа;
- считать vertical volume;
- buy/sell split;
- delta;
- imbalance;
- relative volume;
- volume spike logic.

## Step 4. Build Elliott machines
Поднять по отдельности:
- ELLIOTT_1M
- ELLIOTT_5M
- ELLIOTT_60M

Каждая машина должна:
- ссылаться на `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md` как на source-of-truth входа;
- строить swings;
- trend structure;
- pattern candidates;
- Elliott candidates;
- оставаться candidate-based и low-confidence by default.

## Step 5. Isolate each machine operationally
Для каждой из 12 машин отдельно зафиксировать:
- machine id;
- api key;
- runtime command;
- request format;
- response format;
- failure mode.

Нельзя держать это «в голове».

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
- ready
- partial
- blocked

И отдельно фиксировать причину, если машина ещё не ready.

---

# PHASE 4 — ORCHESTRATION LAYER FOR BEN_KIM

## Goal
Сделать так, чтобы Ben_Kim больше не считал ничего сам, а только оркестрировал 12 машин и собирал ответ.

## Step 1. Define orchestration request plan
Для каждого symbol Ben_Kim должен уметь запускать 12 запросов:
- 4 стратегии × 3 ТФ

Нужно определить:
- порядок вызова;
- parallel/serial режим;
- timeout policy;
- retry policy.

## Step 2. Define collection layer
Ben_Kim должен уметь собирать 12 ответов в один внутренний пакет.

Нужно определить:
- как считать missing response;
- как считать partial response;
- как считать failed response.

## Step 3. Define summarization rules
Ben_Kim должен суммаризировать:
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
- 1 финальный summary от Ben_Kim

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

После прохождения всех 5 фаз должно быть:
- 12 отдельных машин
- единый вход по тикам
- единый формат ответа
- Ben_Kim как оркестратор, а не счётная машина
- один сводный текстовый вывод из 12 strategy/timeframe ответов
