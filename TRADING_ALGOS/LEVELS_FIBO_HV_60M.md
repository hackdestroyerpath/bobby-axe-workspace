# Price Levels + Fibo + Horizontal Volume | 60M

## Назначение
Субагент считает старший structural context на `60m`.

## Вход
- тики BTC
- выбранный диапазон истории
- источник: `Data_collector`

## Что строить
Из тиков собрать свечи `60m`, затем построить:
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
