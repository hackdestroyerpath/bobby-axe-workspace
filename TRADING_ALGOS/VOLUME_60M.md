# Volume Analysis / Vertical Volume | 60M

## Назначение
Субагент считает старший объёмный контекст на `60m`.

## Вход
- тики BTC
- выбранный диапазон истории
- источник: `Data_collector`

## Что строить
Из тиков собрать свечи `60m`, затем построить:
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
Понять старший объёмный фон:
- подтверждает ли старший объём старшее движение
- есть ли сильное buyer/seller dominance
- не расходится ли старший объём с движением цены

## Важные правила
- `60m` — старший volume-confirmation слой
- он должен быть менее шумным и более устойчивым, чем 1m/5m

## Формат ответа
Короткий JSON / API packet.
