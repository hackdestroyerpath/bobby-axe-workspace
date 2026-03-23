# Runbook: запуск `Jack / Data_collector`

## Цель
Этот runbook описывает, как `Jack` поднимает `Data_collector`, подключает новый источник данных, ограничивает ingestion разрешённым universe и подтверждает, что live-поток сделок здоров до передачи данных downstream-этапам.

## Область ответственности
- Поднять intake для live trades.
- Записать raw trades в raw layer.
- Построить детерминированные `second_bar` и OHLC `1m/5m/60m`.
- Опубликовать технический статус для `Bobby Axe`.

## Канонический источник и universe
### Источник по умолчанию
- Канонический live-источник: `binance_futures_usdc`.
- Разрешён только поток сделок по USDC futures.
- Все timestamps хранятся в UTC.

### Текущий operational universe
На старте системы `Jack` поддерживает следующий allowlist символов:

- `BTCUSDC`
- `ETHUSDC`
- `SOLUSDC`
- `XRPUSDC`
- `ADAUSDC`

Любой другой тикер из Binance USDC futures считается **неразрешённым**, пока не пройдет процедуру онбординга и не будет явно добавлен в allowlist.

## Как подключается новый источник данных
Под «новым источником» понимается либо новый provider, либо новый способ доставки данных от текущего provider (например, отдельный live stream или backfill API).

### Preconditions
Перед подключением нового источника `Jack` обязан проверить:
1. Источник публикует сделки, а не только свечи.
2. У события есть стабильный `trade_id` либо возможен fallback-ключ `source + symbol + trade_ts + price + quantity + side`.
3. Символы источника можно привести к каноническому формату вида `BTCUSDC`.
4. Источник отдаёт время сделки, которое можно хранить как `trade_ts` в UTC.
5. Источник покрывает только разрешённый universe или поддерживает фильтрацию на intake.
6. Есть отдельные технические секреты/авторизация, которые можно ротировать без изменения downstream-контрактов.

### Процедура онбординга
1. Зарегистрировать `source_name` и указать transport: `websocket`, `REST batch`, `replay` или `file ingest`.
2. Описать mapping полей источника в контракт `trade_tick`:
   - `source`
   - `symbol`
   - `trade_id`
   - `price`
   - `quantity`
   - `side`
   - `trade_ts`
   - `ingested_at`
3. Включить нормализацию символов в канонический USDC futures format.
4. Включить pre-filter по allowlist universe до записи в raw layer.
5. Включить idempotent upsert в raw layer по ключу `source + symbol + trade_id`.
6. Настроить routing в curated rebuild для событий `raw_data_ingested`.
7. Выполнить smoke test на одном символе из allowlist.
8. Выполнить dry-run backfill на коротком окне и убедиться, что `second_bar` собираются детерминированно.
9. Передать `Bobby Axe` артефакты проверки:
   - sample normalized `trade_tick`
   - результат schema validation
   - lag/trades/sec по тестовому окну
   - duplicate rate
   - итоговый статус `ready` или `revision_required`

### Definition of done для нового источника
Источник считается подключённым только если:
- schema validation проходит стабильно;
- неразрешённые символы отклоняются до записи;
- raw ingest идемпотентен;
- `second_bar` пересобираются без расхождений на повторном окне;
- `Bobby Axe` получил подтверждение о готовности.

## Как запускать `Data_collector`
### Порядок старта
1. Подтвердить, что secrets и сетевой доступ к источнику валидны.
2. Загрузить allowlist universe.
3. Открыть live stream сделок.
4. Запустить writer в raw layer.
5. Включить consumer, который публикует `raw_data_ingested`.
6. Запустить rebuild `second_bar` и старших таймфреймов `1m/5m/60m`.
7. Включить мониторинг и алерты.
8. Сообщить `Bobby Axe`, что stage `Jack` находится в статусе `running`, а затем `ready` после прохождения health checks.

### Startup checklist
- Источник доступен и авторизация проходит.
- Загружен правильный `source` и `mode` (`realtime`, `backfill`, `replay`).
- Allowlist совпадает с актуальным operational universe.
- Raw layer принимает запись без ошибок.
- Curated layer доступен для upsert/rebuild.
- Метрики и алерты доступны до начала live traffic.

## Как понять, что поток live trades здоров
Live-поток считается здоровым только при одновременном выполнении всех условий ниже.

### 1. Lag в норме
- `event_lag = now_utc - max(trade_ts)` по каждому символу.
- Целевой режим для live ingestion: `P95 lag <= 3s`, аварийный порог: `> 10s` более 60 секунд подряд.

### 2. Trades/sec не деградирует
- Для каждого символа сравнивать текущий `trades/sec` с 15-минутным baseline.
- Считать поток подозрительным, если `trades/sec` падает более чем на 80% при том, что соединение формально не разорвано.

### 3. Symbols online соответствуют allowlist
- `symbols_online` должен быть равен числу символов из operational universe, по которым за последние 30 секунд были получены события или heartbeat.
- Если любой символ из allowlist выпал из online-состояния, поток считается degraded.

### 4. Duplicate rate под контролем
- `duplicate_rate = duplicates / total_received` за окно 5 минут.
- Целевой уровень: `< 0.5%`.
- При `>= 2%` требуется расследование, потому что возможны replay-loop, повторная доставка или проблемы у upstream source.

### 5. Failed writes отсутствуют
- Любой ненулевой sustained `failed_writes` в raw или curated layer считается признаком нездорового потока.
- Если ошибка записи длится более 30 секунд, ingestion должен перейти в `degraded` или `error`.

### 6. Агрегация не имеет дыр
- Для активного символа `second_bar` должны материализоваться без пропуска ожидаемых секунд окна.
- Допустим только краткий `partial` во время текущей незакрытой секунды; историческое окно не должно оставаться `partial`.

## Метрики, которые нужно мониторить
### Обязательные метрики
1. `lag`
   - по `source`
   - по `symbol`
   - P50/P95/P99
2. `trades_per_sec`
   - по `symbol`
   - aggregate по всему ingestion
3. `symbols_online`
   - текущее число online-символов
   - список offline-символов
4. `duplicate_rate`
   - по окну 1 минута и 5 минут
   - отдельно для raw intake и для post-dedup stage
5. `failed_writes`
   - raw layer
   - curated layer
   - dead-letter / retry queue при наличии

### Рекомендуемые дополнительные метрики
- `raw_data_ingested publish delay`
- `second_bars_ready latency`
- `schema_validation_failures`
- `out_of_order_event rate`
- `source reconnect count`

## Коммуникация с `Bobby Axe`
После запуска `Jack` должен отправить краткий статус:

```text
[Jack Result]
Mode: realtime
Window: <window_start_utc> -> <window_end_utc>
Symbol: <symbol or batch>
Status: ready
Artifacts:
- raw_storage_ref: <table/partition>
- curated_storage_ref: <table/partition>
- timeframes: <1m,5m,60m>
Checks:
- schema_validation: pass
- deduplication: pass
- aggregation: pass
Issue:
- none
```

Если хотя бы один из health checks не пройден, вместо `ready` должен использоваться `partial` или `error` с явным описанием причины.
