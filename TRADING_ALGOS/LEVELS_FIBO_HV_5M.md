# Price Levels + Fibo + Horizontal Volume | 5M

## Назначение
Субагент считает основной intraday structural context на `5m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream

## Что строить
Из `normalized ticks` общего слоя собрать свечи `5m`, затем построить:
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
