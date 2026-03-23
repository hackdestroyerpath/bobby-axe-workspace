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

Дальше каждый алгоритм сам:
- агрегирует тики в нужный ТФ
- считает свои признаки
- по запросу отдаёт свой strategy-specific packet

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
