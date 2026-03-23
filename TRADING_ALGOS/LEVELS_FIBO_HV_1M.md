# Price Levels + Fibo + Horizontal Volume | 1M

## Назначение
Субагент считает краткосрочную structural position цены на `1m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream

## Что строить
Из `normalized ticks` общего слоя собрать свечи `1m`, затем построить:
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
Короткий JSON / API packet.
