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
На входе у всех только тики из `Data_collector`.
Дальше каждый алгоритм сам:
- агрегирует тики в нужный ТФ
- считает свои признаки
- по запросу отдаёт свой strategy-specific packet

## Структура папки
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
