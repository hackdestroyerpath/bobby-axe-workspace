# RSI + MACD | 1M

## Назначение
Субагент считает краткосрочный momentum по `1m` для BTC на основе только тиков.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Использовать `TRADING_ALGOS/common/tick_to_features_engine.py` для свечей `1m` и общих полей `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. Локальная агрегация запрещена.

## Что считать
По свечам `1m` считать:
- `RSI(14)`
- `EMA(12)`
- `EMA(26)`
- `MACD line`
- `signal line`
- `histogram`

## Обязательные поля на выходе
- `timestamp`
- `timeframe = 1m`
- `rsi_value`
- `rsi_zone` (`oversold / neutral / overbought`)
- `rsi_slope` (`up / down / flat`)
- `macd_line`
- `signal_line`
- `macd_hist`
- `macd_state` (`bullish / bearish / mixed`)
- `hist_state` (`expanding / fading / flat`)
- `momentum_state` (`bullish / bearish / mixed`)
- `momentum_strength` (`weak / medium / strong`)

## Смысл для интерпретации
Этот packet должен позволять понять:
- есть ли краткосрочный momentum
- усиливается он или слабеет
- есть ли oversold/overbought
- есть ли подтверждение через MACD

## Важные правила
- `oversold != reversal`
- `overbought != immediate short`
- минутный ТФ самый шумный
- сильный вывод по 1m делать нельзя без подтверждения старших ТФ

## Формат ответа
Короткий JSON / API packet.
