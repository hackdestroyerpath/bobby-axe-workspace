# PHASE 1 REPORT

## Что сделано
- Зафиксирован `Tick Source Contract`: единый source-of-truth для входных тиков всех 12 машин — таблица `collector_v2.tick_trade`, обязательные поля, UTC-правила и проверка фактической глубины истории через `MIN/MAX/COUNT`.
- Зафиксирован `Common Tick Read Spec`: единые входы tick-read (`symbol`, `timeframe_target`, `from`, `to`, `source`), inclusive window boundaries, canonical ordering, pagination rules и обязательная клиентская нормализация после чтения.
- Добавлен общий `tick_normalizer`: единый preprocessing-слой для приведения типов, dedup по `(source, symbol, trade_id)`, канонической сортировки, детекта empty window, gap detection, расчёта `coverage_ratio` и выставления partial quality flags.
- Добавлен общий `tick_to_features_engine`: единый feature layer для 1m / 5m / 60m с общими aligned candles, OHLCV, buy/sell volume, delta, imbalance, trade_speed, relative volume baseline и одинаковыми operational policies.
- Зафиксированы единые request/response schema и quality flags: один request contract для всех 12 машин, один response contract со статусами `ready/partial/error`, согласованностью `status` ↔ `meta.is_partial` и общими quality-полями `coverage_ratio`, `partial_reason`, `source_contract_version`, `build_version`, `machine_id`.

## Чем подтверждено
### Артефакты Phase 1
- Контракт источника тиков: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`.
- Единая спецификация чтения: `TRADING_ALGOS/COMMON_TICK_READ_SPEC.md`.
- Общий preprocessing: `TRADING_ALGOS/common/tick_normalizer.py`.
- Общий feature layer: `TRADING_ALGOS/common/tick_to_features_engine.py`.
- Единый request contract: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json`.
- Единый response contract: `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`.
- 12 machine templates, которые ссылаются на общий входной контракт, read spec, normalizer, feature engine и transport schemas:
  - `TRADING_ALGOS/RSI_MACD_1M.md`
  - `TRADING_ALGOS/RSI_MACD_5M.md`
  - `TRADING_ALGOS/RSI_MACD_60M.md`
  - `TRADING_ALGOS/LEVELS_FIBO_HV_1M.md`
  - `TRADING_ALGOS/LEVELS_FIBO_HV_5M.md`
  - `TRADING_ALGOS/LEVELS_FIBO_HV_60M.md`
  - `TRADING_ALGOS/VOLUME_1M.md`
  - `TRADING_ALGOS/VOLUME_5M.md`
  - `TRADING_ALGOS/VOLUME_60M.md`
  - `TRADING_ALGOS/ELLIOTT_1M.md`
  - `TRADING_ALGOS/ELLIOTT_5M.md`
  - `TRADING_ALGOS/ELLIOTT_60M.md`

### Проверки единой базы входных данных
- Подтверждено наличие ровно 12 machine templates в `TRADING_ALGOS`.
- Подтверждено, что все 12 machine templates ссылаются на один и тот же `TICK_SOURCE_CONTRACT`.
- Подтверждено, что все 12 machine templates ссылаются на один и тот же `COMMON_TICK_READ_SPEC`.
- Подтверждено, что все 12 machine templates используют один `tick_normalizer` и один `tick_to_features_engine` как обязательный shared layer.
- Подтверждено, что все 12 machine templates ссылаются на один request schema и один response schema.
- Подтверждено, что общий normalizer фиксирует единые partial reasons (`retention_truncation`, `pagination_truncation`, `empty_window`, `gap_heavy_window`) и считает `coverage_ratio` / `gap_count` на одном наборе правил.

## Что это означает для 12 машин
- Все 12 машин читают один и тот же входной источник: `collector_v2.tick_trade`.
- Все 12 машин используют один preprocessing pipeline: canonical filters/read rules -> `tick_normalizer` -> `normalized ticks`.
- Все 12 машин используют один feature layer: `tick_to_features_engine` даёт общий candle/microstructure base, поверх которого стратегии считают только strategy-specific indicators.
- Все 12 машин возвращают ответы в одном transport contract: единые request/response schema, единые статусы, единые quality flags и одинаковая логика partial/error интерпретации.

## Риски / следующий шаг
- Retention остаётся operational constraint: глубина истории зависит от `RETENTION_DAYS`, поэтому перед каждым расчётом окно всё ещё надо подтверждать фактическим `MIN/MAX/COUNT`.
- Pagination остаётся зоной контроля transport/runtime: spec зафиксирован, но в Phase 2 нужно довести его до реального API/оркестрационного исполнения без truncation drift.
- Coverage и gap quality flags уже стандартизированы, но их пороги и реакция стратегий на partial-окна ещё должны быть доведены на уровне реальных исполнителей.
- В Phase 2 переходит реализация самих машин поверх общей базы: подключение transport/runtime, фактическое чтение `/ticks`, расчёт strategy-specific features, output validation, orchestration и runtime-quality checks.
