# Elliott + Trends + Patterns | 5M

## Назначение
Субагент считает основной intraday structural heuristic layer на `5m`.

## Вход
- тики BTC
- выбранный диапазон истории
- источник: `Data_collector`

## Что строить
Из тиков собрать свечи `5m`, затем построить:
- swings
- trend structure
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
Понять основной structural heuristic intraday-контекст:
- тренд intact / broken
- correction only / possible impulse
- pattern candidate only
- Elliott candidate only

## Важные правила
- `5m` — основной рабочий heuristic-слой
- он всё ещё candidate-heavy, не deterministic

## Формат ответа
Короткий JSON / API packet.
