# TODO

# PHASE 1 — CORE DATA FOUNDATION

## Goal
Поднять общую основу, от которой потом будут работать все 12 машин.

## Step 1. Verify raw source contract
Проверить и зафиксировать:
- откуда именно читаются тики;
- какой формат у тиков;
- какие поля гарантированы;
- какая глубина хранения доступна по BTC;
- как будет задаваться период выборки.

Нужно явно проверить наличие минимум таких полей:
- trade timestamp
- price
- quantity / size
- trade id
- side или proxy, если side нет напрямую

## Step 2. Define common ingestion interface
Сделать единый контракт чтения тиков для всех будущих машин.

То есть все 12 машин должны читать данные одинаково:
- symbol
- timeframe target
- from
- to
- source = Data_collector

Нужно исключить ситуацию, где каждая машина сама по-своему читает тики.

## Step 3. Build common tick-to-candle engine
Написать общую базовую машину, которая из тиков строит свечи:
- 1m
- 5m
- 60m

Для каждой свечи должны получаться минимум:
- open
- high
- low
- close
- volume
- trade_count

Это должен быть единый переиспользуемый слой для всех 12 машин.

## Step 4. Build common derived microstructure fields
Поверх тиков и свечей собрать общий слой полей, который потом смогут использовать разные стратегии.

Например:
- buy_volume
- sell_volume
- delta
- imbalance
- trade_speed
- relative volume baseline

Если какое-то поле нельзя достать точно, надо сразу зафиксировать proxy-логику.

## Step 5. Define common request/response transport
Привести все будущие машины к одному формату запроса и одному формату ответа.

Использовать `SUBAGENT_RESPONSE_FORMAT.json` как базу.

Каждая машина должна отвечать одинаково по структуре, чтобы оркестратор не писал 12 разных парсеров.

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
