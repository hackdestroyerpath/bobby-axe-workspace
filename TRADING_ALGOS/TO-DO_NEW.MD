ONLY PHASE 1 OPTIMIZATION

# TO-DO_NEW

# PHASE 1 — OPTIMIZED CORE DATA FOUNDATION

## Goal
Зафиксировать один реальный контракт чтения и один общий preprocessing-слой, чтобы все 12 машин считали разные стратегии, но на одной и той же базе тиков без расхождения по входу.

## Step 1. Freeze source-of-truth contract
Жёстко зафиксировать, что все субагенты берут тики из центральной БД `new_collector`, таблица:

- `collector_v2.tick_trade`

Обязательные поля, которые уже гарантированы схемой:
- `source`
- `symbol`
- `trade_id`
- `event_time_utc`
- `price`
- `quantity`
- `side`
- `ingested_at_utc`

Что нужно зафиксировать сразу:
- `side` доступен напрямую, proxy-логика не нужна;
- все timestamps трактуются только в UTC;
- BTC depth нельзя предполагать — её надо проверять отдельно через `MIN(event_time_utc)`, `MAX(event_time_utc)`, `COUNT(*)`;
- retention зависит от настройки `RETENTION_DAYS`, значит допустимая глубина окна должна считаться как operational constraint, а не как допущение.

Артефакт шага:
- один документ `Tick Source Contract`, на который будут ссылаться все 12 машин.

## Step 2. Define one canonical read spec for all subagents
Сделать один общий контракт чтения тиков для всех будущих машин.

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
- один зафиксированный источник тиков;
- один общий SQL/read contract;
- один normalization layer;
- один shared candle+microstructure engine;
- один response contract;
- ноль расхождений между машинами на уровне входных данных.
