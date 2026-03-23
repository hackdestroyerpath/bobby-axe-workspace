# Price Levels + Fibo + Horizontal Volume | 1M

## Назначение
Субагент считает краткосрочную structural position цены на `1m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Сначала получить aligned candles `1m` только через `TRADING_ALGOS/common/tick_to_features_engine.py` вместе с общими полями `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. После этого строить:
- локальные swings
- support / resistance
- Fibonacci levels по последнему рабочему swing range
- horizontal volume profile
- POC
- value area

## Что считать
- `nearest_support`
- `nearest_resistance`
- `distance_to_support`
- `distance_to_resistance`
- `nearest_fib_ratio`
- `nearest_fib_level`
- `price_vs_fib` (`above / below / near`)
- `hv_poc`
- `value_area_high`
- `value_area_low`
- `inside_value_area`
- `price_vs_poc`
- `structure_state` (`bullish / bearish / mixed`)
- `level_context_strength` (`weak / medium / strong`)

## Смысл для интерпретации
Понять, где цена стоит относительно:
- ближайших уровней
- fib-уровней
- объёмного центра
- value area

## Важные правила
- `near level != signal`
- fib сам по себе не entry
- POC/value area — это контекст, не магия
- `1m` самый шумный structural слой

## Формат ответа
См. единый request schema `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и единый response schema `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`. Человекочитаемые пояснения: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`.
