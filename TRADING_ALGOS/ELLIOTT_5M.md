# Elliott + Trends + Patterns | 5M

## Назначение
Субагент считает основной intraday structural heuristic layer на `5m`.

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
Сначала получить aligned candles `5m` только через `TRADING_ALGOS/common/tick_to_features_engine.py` вместе с общими полями `open`, `high`, `low`, `close`, `volume`, `trade_count`, `buy_volume`, `sell_volume`, `delta`, `imbalance`, `trade_speed`, `relative_volume_baseline`. После этого стратегия считает только свои strategy-specific indicators поверх общего feature layer и строит:
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
См. единый request schema `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и единый response schema `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json`. Человекочитаемые пояснения: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`.
