# RSI + MACD | 5M

## Назначение
Субагент считает основной intraday momentum по `5m` для BTC на основе только тиков.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Использовать `TRADING_ALGOS/common/tick_to_features_engine.py` для свечей `5m` и общих полей `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. Локальная агрегация запрещена.

## Что считать
По свечам `5m` считать:
- `RSI(14)`
- `EMA(12)`
- `EMA(26)`
- `MACD line`
- `signal line`
- `histogram`

## Обязательные поля на выходе
- `timestamp`
- `timeframe = 5m`
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
Этот packet должен позволять понять:
- основной intraday momentum
- идёт ли усиление/затухание импульса
- есть ли рабочая bullish/bearish структура импульса

## Важные правила
- `5m` важнее `1m`, но слабее `60m`
- oversold и overbought не считать сами по себе входом
- MACD positive/negative не интерпретировать без контекста RSI и slope

## Формат ответа
Короткий JSON / API packet.
