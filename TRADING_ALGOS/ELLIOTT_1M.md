# Elliott + Trends + Patterns | 1M

## Назначение
Субагент считает самый быстрый structural heuristic layer на `1m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- общий preprocessing-слой: `TRADING_ALGOS/common/tick_normalizer.py`
- общий candle + microstructure engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа
- downstream-вход стратегии: только `normalized ticks`, а не raw tick stream
- стратегия обязана брать aligned candles только из shared engine и не описывать/не реализовывать собственную агрегацию

## Shared engine dependency
Сначала получить aligned candles `1m` только через `TRADING_ALGOS/common/tick_to_features_engine.py` вместе с общими полями `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. После этого строить:
- pivot highs / lows
- short swings
- local trend structure
- local pattern candidates
- Elliott candidates

## Что считать
- `trend_state` (`up / down / flat`)
- `structure_state` (`intact / weakening / broken`)
- `current_leg_direction`
- `current_leg_strength`
- `correction_depth_state`
- `pattern_candidate`
- `pattern_state`
- `elliott_candidate_family`
- `elliott_direction_candidate`
- `elliott_confidence_state` (`low / medium / high`, default low)

## Смысл для интерпретации
Понять краткосрочную structural картину:
- есть ли локальный тренд
- это impulse/correction candidate или нет
- есть ли pattern candidate
- есть ли elliott candidate

## Важные правила
- `candidate != confirmed`
- pattern recognition — heuristic
- Elliott по умолчанию low-confidence
- `1m` здесь максимально шумный слой

## Формат ответа
Короткий JSON / API packet.
