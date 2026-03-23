# Price Levels + Fibo + Horizontal Volume | 5M

## Назначение
Субагент считает основной intraday structural context на `5m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Сначала получить aligned candles `5m` только через `TRADING_ALGOS/common/tick_to_features_engine.py` вместе с общими полями `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. После этого строить:
- swings
- support / resistance
- Fibonacci grid по рабочему swing range
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
Понять рабочий structural контекст intraday:
- цена у поддержки / сопротивления
- цена выше / ниже fib
- цена внутри / вне value area
- цена у POC или в отрыве от него

## Важные правила
- `5m` — основной рабочий structural слой
- уровень сам по себе не равен сигналу
- реакция цены важнее самого факта близости к уровню

## Формат ответа
Короткий JSON / API packet.
