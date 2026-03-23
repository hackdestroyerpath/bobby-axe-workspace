# RSI + MACD | 60M

## Назначение
Субагент считает старший momentum/context по `60m` для BTC на основе только тиков.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Использовать `TRADING_ALGOS/common/tick_to_features_engine.py` для свечей `60m` и общих полей `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. Локальная агрегация запрещена.

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
См. единый request schema `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и единый response schema `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`. Человекочитаемые пояснения: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`.
