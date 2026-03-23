# Volume Analysis / Vertical Volume | 5M

## Назначение
Субагент считает основной intraday объёмный контекст на `5m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Сначала получить aligned candles `5m` только через `TRADING_ALGOS/common/tick_to_features_engine.py` вместе с общими полями `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. После этого строить:
- vertical volume
- buy volume / sell volume
- delta
- imbalance
- relative volume
- spike detection

## Что считать
- `current_volume`
- `avg_volume`
- `relative_volume`
- `volume_spike_flag`
- `buy_volume`
- `sell_volume`
- `volume_delta`
- `imbalance_ratio`
- `pressure_side`
- `volume_confirmation_state`
- `flow_strength`

## Смысл для интерпретации
Понять:
- подтверждает ли объём intraday move
- у кого давление сильнее
- есть ли агрессивный buyer/seller flow

## Важные правила
- `5m` — главный рабочий volume-confirmation слой
- объём — слой подтверждения и давления, а не гарантия направления

## Формат ответа
См. единый request schema `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и единый response schema `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`. Человекочитаемые пояснения: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`.
