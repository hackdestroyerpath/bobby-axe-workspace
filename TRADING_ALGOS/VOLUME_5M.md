# Volume Analysis / Vertical Volume | 5M

## Назначение
Субагент считает основной intraday объёмный контекст на `5m`.

## Вход
- тики BTC
- выбранный диапазон истории
- источник: `Data_collector`

## Что строить
Из тиков собрать свечи `5m`, затем построить:
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
Короткий JSON / API packet.
