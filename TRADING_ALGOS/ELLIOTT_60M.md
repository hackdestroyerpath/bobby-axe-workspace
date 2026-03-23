# Elliott + Trends + Patterns | 60M

## Назначение
Субагент считает старший structural heuristic layer на `60m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа

## Что строить
Из тиков собрать свечи `60m`, затем построить:
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
Короткий JSON / API packet.
