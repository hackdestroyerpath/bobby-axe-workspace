# TRADING_ALGOS

Развернутые ТЗ для 12 субагентов `Ben_Kim`.

## Архитектура
- 4 стратегии
- 3 таймфрейма на каждую
- итого 12 отдельных алгоритмов / машин / субагентов

## Стратегии
1. `RSI + MACD`
2. `Price Levels + Fibo + Horizontal Volume`
3. `Volume Analysis / Vertical Volume`
4. `Elliott + Trends + Patterns`

## Таймфреймы
- `1m`
- `5m`
- `60m`

## Общее правило
Единый source-of-truth для входных тиков зафиксирован в `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`. Все 12 машин должны ссылаться на этот контракт и использовать его без локального пересказа.

Дальше каждая машина работает по единому pipeline:
- машина получает `normalized ticks` из общего tick normalizer `TRADING_ALGOS/common/tick_normalizer.py`
- машина получает `candles` и `microstructure` из shared tick-to-features engine `TRADING_ALGOS/common/tick_to_features_engine.py`
- стратегия считает только свои `strategy-specific indicators` поверх общего feature layer
- по запросу машина отдаёт свой strategy-specific packet в едином request/response contract

## Общие ссылки
- тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- единая спецификация чтения тиков: `TRADING_ALGOS/COMMON_TICK_READ_SPEC.md`
- shared normalization module: `TRADING_ALGOS/common/tick_normalizer.py`
- shared feature engine: `TRADING_ALGOS/common/tick_to_features_engine.py`
- единый request schema: `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.json` и `TRADING_ALGOS/SUBAGENT_REQUEST_FORMAT.md`
- единый response schema: `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.json` и `TRADING_ALGOS/SUBAGENT_RESPONSE_FORMAT.md`

## Структура папки
- `TICK_SOURCE_CONTRACT.md`
- `RSI_MACD_1M.md`
- `RSI_MACD_5M.md`
- `RSI_MACD_60M.md`
- `LEVELS_FIBO_HV_1M.md`
- `LEVELS_FIBO_HV_5M.md`
- `LEVELS_FIBO_HV_60M.md`
- `VOLUME_1M.md`
- `VOLUME_5M.md`
- `VOLUME_60M.md`
- `ELLIOTT_1M.md`
- `ELLIOTT_5M.md`
- `ELLIOTT_60M.md`

## Phase 2 артефакты
- `machine_registry.py` — frozen registry и warmup-политики для всех 12 машин
- `runtime_contract.py` — единый runtime pipeline, partial-policy, failure-mode matrix, summary policy
- `strategy_cores.py` — shared family-core реализации для `RSI_MACD`, `LEVELS_FIBO_HV`, `VOLUME`, `ELLIOTT`
- `machines.py` — 12 runtime wrappers поверх общего контракта и family-core
- `PHASE_2_BLUEPRINT.md` — cross-cutting operational decisions для всей фазы
- `PHASE_2_REPORT.md` — closing-report по всей Phase 2 и сверка с Definition of Done
- `BEN_KIM_ORCHESTRATION_CONTRACT.md` — machine-to-orchestrator readiness contract для следующей фазы
