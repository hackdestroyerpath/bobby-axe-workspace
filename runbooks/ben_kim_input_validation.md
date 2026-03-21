# Runbook: Ben_Kim Input Validation

## Purpose
Краткий runbook проверки входных feature-пакетов от `Jack` перед запуском анализа.

## Checks

### 1. Envelope
Проверить:
- `event_type = ben_kim_feature_packet`
- есть `packet_id`
- есть `correlation_id`
- есть `symbol`
- есть `frame`
- есть `observed_at`

### 2. Timeframe
Допустимы только:
- `1m`
- `5m`
- `60m`

### 3. Window
Проверить:
- `source_window.from`
- `source_window.to`
- оба значения в UTC
- `from < to`

### 4. Feature groups
Проверить наличие групп:
- `price`
- `levels`
- `fibonacci`
- `horizontal_volume`
- `vertical_volume`
- `rsi_macd`
- `trade_speed`
- `volatility`
- `elliott`
- `data_quality`

### 5. Data quality
Проверить:
- `data_quality.schema_ok = true`
- `data_quality.stale = false` для runtime-ready пакета
- `missing_bars` не нарушает допустимый порог

## Result handling
- если packet валиден -> допуск к анализу
- если отсутствуют отдельные feature groups -> анализ допустим, но соответствующие стратегии должны вернуться как `partial`
- если сломан envelope или window -> packet отклоняется целиком
