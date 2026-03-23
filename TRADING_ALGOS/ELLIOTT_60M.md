# Elliott + Trends + Patterns | 60M

## Назначение
Субагент считает старший structural heuristic layer на `60m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Сначала получить aligned candles `60m` только через `TRADING_ALGOS/common/tick_to_features_engine.py` вместе с общими полями `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. После этого строить:
- старшие swings
- старший trend structure
- pattern candidates
- Elliott candidates

## Что считать
- `trend_state`
- `structure_state`
- `current_leg_direction`
- `current_leg_strength`
- `correction_depth_state`
- `pattern_candidate`
- `pattern_state`
- `elliott_candidate_family`
- `elliott_direction_candidate`
- `elliott_confidence_state`

## Смысл для интерпретации
Понять старший structural heuristic контекст:
- сохраняется ли старший тренд
- correction / impulse candidate
- pattern candidate
- elliott candidate

## Важные правила
- `60m` важнее младших внутри этой стратегии
- всё равно оставаться cautious and candidate-based

## Формат ответа
См. единый request schema `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и единый response schema `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`. Человекочитаемые пояснения: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`.
