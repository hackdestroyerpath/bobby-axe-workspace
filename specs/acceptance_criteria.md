# Acceptance Criteria

## Core acceptance criteria
- Система автономно принимает торговое решение внутри `probabilistic_decision_engine`, а не опирается на отдельные directional-сигналы аналитических субагентов.
- Решение формируется на основе live market data, внутренних признаков и нормализованного `probability snapshot`.
- Расчёт вероятностей `LONG`, `SHORT`, `NEUTRAL` трассируем и воспроизводим через audit artifacts.
- При недостатке качества данных или уверенности система корректно деградирует в `NEUTRAL` или безопасный отказ.
- Grid параметры генерируются полностью для каждого исполнимого торгового решения.
- Risk constraints валидируются до размещения ордеров.
- Есть отдельные сценарии для `LONG`, `SHORT`, `NEUTRAL`.
- Memory-файлы обновляются после каждого шага.

## Expanded interpretation

### 1. Autonomous decision model
- Центральный decision engine выполняет аналитическую и вероятностную обработку самостоятельно.
- Supervisor и downstream-модули не подменяют production-логику ручной интерпретацией рынка.
- У каждого расчётного цикла есть owner, набор входных данных и воспроизводимый decision artifact.

### 2. Probability-driven governance
- Контракты данных фиксируют происхождение market state, derived features и итоговых вероятностей.
- Финальное решение по открытию grid можно трассировать до `state snapshot`, `probability snapshot` и правил деградации.
- В архитектуре отсутствует требование покрывать фиксированный список аналитических источников отдельными субагентами.

### 3. Traceability and explainability
- Для каждого решения сохраняются ссылки на входные snapshots, calculation trace и reason codes.
- Вероятности `LONG`, `SHORT`, `NEUTRAL` нормализованы и объяснимы через derived features.
- Любое понижение уверенности или отказ от directional-сделки сопровождается явными `degradation_flags` или neutral fallback reason.

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
