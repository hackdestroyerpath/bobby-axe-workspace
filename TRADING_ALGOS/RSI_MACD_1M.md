# RSI + MACD | 1M

## Назначение
Субагент считает краткосрочный momentum по `1m` для BTC на основе только тиков.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- единая спецификация чтения тиков: `TRADING_ALGOS/COMMON_TICK_READ_SPEC.md`
- shared normalization module: `TRADING_ALGOS/common/tick_normalizer.py`
- shared feature engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- единый request schema: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md`
- `options.include_incomplete_candle=false` по умолчанию исключает последнюю незавершённую свечу; при `true` shared candle engine оставляет последний bucket и помечает его `is_incomplete=true`
- единый response schema: `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- машина получает `normalized ticks` из общего tick normalizer
- машина получает `candles` / `microstructure` из shared tick-to-features engine
- стратегия считает только свои `strategy-specific indicators` поверх общего feature layer

## Shared engine dependency
Использовать `TRADING_ALGOS/common/tick_to_features_engine.py` для свечей `1m` и общих полей `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. Локальная агрегация запрещена: свечи и общие microstructure-признаки приходят только из shared feature engine, а стратегия добавляет поверх них только свои strategy-specific indicators.

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
См. единый request schema `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и единый response schema `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`. Человекочитаемые пояснения: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`.
