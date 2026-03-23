# RSI + MACD | 60M

## Назначение
Субагент считает старший momentum/context по `60m` для BTC на основе только тиков.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- единая спецификация чтения тиков: `TRADING_ALGOS/COMMON_TICK_READ_SPEC.md`
- shared normalization module: `TRADING_ALGOS/common/tick_normalizer.py`
- shared feature engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- единый request schema: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md`
- единый response schema: `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- машина получает `normalized ticks` из общего tick normalizer
- машина получает `candles` / `microstructure` из shared tick-to-features engine
- стратегия считает только свои `strategy-specific indicators` поверх общего feature layer

## Shared engine dependency
Использовать `TRADING_ALGOS/common/tick_to_features_engine.py` для свечей `60m` и общих полей `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. Локальная агрегация запрещена: свечи и общие microstructure-признаки приходят только из shared feature engine, а стратегия добавляет поверх них только свои strategy-specific indicators.

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
