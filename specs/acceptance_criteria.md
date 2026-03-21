# Acceptance Criteria

## Core acceptance criteria
- Агент умеет делегировать задачи только субагентам и не подменяет их самостоятельной реализацией production-логики.
- Все разрешённые источники анализа покрыты отдельными субагентами.
- Решение формируется только из разрешённых сигналов.
- Grid параметры генерируются полностью для каждого торгового решения.
- Risk constraints валидируются до размещения ордеров.
- Есть отдельные сценарии для `LONG`, `SHORT`, `NEUTRAL`.
- Memory-файлы обновляются после каждого шага.

## Expanded interpretation

### 1. Delegation model
- Supervisor выполняет функции планирования, декомпозиции, контроля, интеграции и приёмки.
- Аналитическая, расчётная и исполнительная логика распределена по субагентам.
- У каждой атомарной задачи есть owner и ожидаемый артефакт.

### 2. Coverage of allowed analytical sources
- Отдельно описаны субагенты для:
  - vertical volumes;
  - horizontal volumes;
  - Fibonacci levels;
  - ticks (sum + timing);
  - activity (trades per second);
  - context activity (BTC + sector + SPX и др.);
  - Elliott waves.
- В спецификациях отсутствует использование неразрешённых аналитических источников для принятия решений.

### 3. Signal governance
- Контракты сигналов фиксируют происхождение каждого сигнала.
- Signal aggregator и scoring/weighting engine принимают только whitelisted inputs.
- Финальное решение по открытию grid можно трассировать до набора разрешённых сигналов и их весов.

### 4. Grid completeness
- Для каждой proposed grid задаются instrument/ticker, direction, price range, number of grids, SL, TP.
- Для каждой proposed grid описаны isolated margin expectations и leverage validation.
- Поддерживаются сценарии генерации параметров для LONG, SHORT и NEUTRAL.

### 5. Risk validation
- До размещения выполняются проверки risk per grid, exchange constraints, leverage/margin mode и допустимости ордеров.
- При нарушении ограничений размещение блокируется или переводится в безопасный отказ.
- Risk checks задокументированы и проверяемы.

### 6. Scenario readiness
- Есть сценарии открытия, сопровождения и завершения для LONG и SHORT grid.
- Есть сценарий открытия, event/webhook-based сопровождения и снятия для NEUTRAL grid.
- Для simulation/backtest design предусмотрены тестовые сценарии для всех трёх направлений.

### 7. Memory discipline
- После каждого существенного шага актуализируются план, очередь задач и открытые вопросы по необходимости.
- Изменения статусов и решения синхронизируются между memory-артефактами.
- Приёмка невозможна, если memory-артефакты устарели относительно фактического состояния проекта.
