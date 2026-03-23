# RSI + MACD | 1M

## Назначение
Субагент считает краткосрочный momentum по `1m` для BTC на основе только тиков.

## Вход
- тики BTC
- выбранный диапазон истории
- источник: `Data_collector`

## Базовая агрегация
Из тиков собрать свечи `1m`:
- `open`
- `high`
- `low`
- `close`
- `volume`
- `trade_count`

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
