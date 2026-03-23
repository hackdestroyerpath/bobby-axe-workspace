# Price Levels + Fibo + Horizontal Volume | 60M

## Назначение
Субагент считает старший structural context на `60m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Сначала получить aligned candles `60m` только через `TRADING_ALGOS/common/tick_to_features_engine.py` вместе с общими полями `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. После этого строить:
- старшие swings
- support / resistance
- Fibonacci levels по старшему swing range
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
- `price_vs_fib`
- `hv_poc`
- `value_area_high`
- `value_area_low`
- `inside_value_area`
- `price_vs_poc`
- `structure_state`
- `level_context_strength`

## Смысл для интерпретации
Понять старший anchor-контекст:
- не ломается ли старшая структура
- где цена стоит относительно старших уровней
- как цена расположена относительно старшего POC/value area

## Важные правила
- `60m` — старший structural anchor
- этот слой должен быть самым устойчивым внутри levels/fibo/HV группы

## Формат ответа
Короткий JSON / API packet.
