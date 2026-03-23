# RSI + MACD | 60M

## Назначение
Субагент считает старший momentum/context по `60m` для BTC на основе только тиков.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream

## Базовая агрегация
Из `normalized ticks` общего слоя собрать свечи `60m`:
- `open`
- `high`
- `low`
- `close`
- `volume`
- `trade_count`

## Что считать
По свечам `60m` считать:
- `RSI(14)`
- `EMA(12)`
- `EMA(26)`
- `MACD line`
- `signal line`
- `histogram`

## Обязательные поля на выходе
- `timestamp`
- `timeframe = 60m`
- `rsi_value`
- `rsi_zone`
- `rsi_slope`
- `macd_line`
- `signal_line`
- `macd_hist`
- `macd_state`
- `hist_state`
- `momentum_state`
- `momentum_strength`

## Смысл для интерпретации
Этот packet должен давать старший momentum-контекст:
- конструктивный / слабый / смешанный
- усиливается ли старшая структура
- не ломается ли старший импульс

## Важные правила
- `60m` — старший контекст этой стратегии
- не делать резких выводов только по младшим ТФ против сильного `60m`
- старший MACD/RSI важнее минутного шума

## Формат ответа
Короткий JSON / API packet.
