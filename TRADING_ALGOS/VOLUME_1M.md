# Volume Analysis / Vertical Volume | 1M

## Назначение
Субагент считает краткосрочное объёмное давление на `1m`.

## Вход
- входной тик-контракт: `TRADING_ALGOS/TICK_SOURCE_CONTRACT.md`
- выбранный диапазон истории
- источник: см. единый контракт, без локального пересказа

## Что строить
Из тиков собрать свечи `1m`, затем построить:
- vertical volume per candle
- buy volume / sell volume
- delta
- imbalance
- relative volume
- volume spikes

## Что считать
- `current_volume`
- `avg_volume`
- `relative_volume`
- `volume_spike_flag`
- `buy_volume`
- `sell_volume`
- `volume_delta`
- `imbalance_ratio`
- `pressure_side` (`buyers / sellers / mixed`)
- `volume_confirmation_state` (`confirms / weak / mixed`)
- `flow_strength` (`weak / medium / strong`)

## Смысл для интерпретации
Понять:
- кто давит объёмно сейчас
- подтверждает ли объём движение
- есть ли spike / climax / weak participation

## Важные правила
- большой объём не значит автоматически bullish
- delta сам по себе не полный сигнал
- spike может быть и exhaustion, и continuation
- `1m` самый шумный volume-flow слой

## Формат ответа
Короткий JSON / API packet.
