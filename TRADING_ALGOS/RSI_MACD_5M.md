# RSI + MACD | 5M

## Назначение
Субагент считает основной intraday momentum по `5m` для BTC на основе только тиков.

## Вход
- тики BTC
- выбранный диапазон истории
- источник: `Data_collector`

## Базовая агрегация
Из тиков собрать свечи `5m`:
- `open`
- `high`
- `low`
- `close`
- `volume`
- `trade_count`

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
