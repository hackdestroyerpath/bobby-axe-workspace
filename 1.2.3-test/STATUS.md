# STATUS.md

## Что сделано
- [PROJECT] PROJ-BBY-ALGO-001: контур проекта paper grid algo оформлен и поддерживается.
- [TASK] TASK-BBY-001: paper execution simulator core завершен.
- [TASK] TASK-BBY-003: базовый multi-symbol scan loop завершен.
- [TASK] TASK-BBY-004: runner-level summary и heartbeat/status formatting реализованы.
- [TASK] TASK-BBY-005: введены symbol-specific sizing overrides.
- [TASK] TASK-BBY-006: compact readiness output реализован.
- [TASK] TASK-BBY-007: final paper-ready runner cycle собран.
- [TASK] TASK-BBY-010: M2/M3/M4 внедрены — default levels сжаты к 1..5, directional TP/SL добавлены, neutral-grid removal rule задан.
- [ACTION] A-BBY-2026-03-21-03: локальный прогон после M2/M3/M4 выполнен; BTCUSDC честно показал economics blocker на текущем депозите/фильтрах.

## Что в работе
- [TASK] TASK-BBY-008: добавить repeating loop runner.
- [TASK] TASK-BBY-002: довести risk/state hardening до runner-level contract.
- [PROCESS] PROC-BBY-001: heartbeat-контур активен.
- [PROCESS] PROC-BBY-002: micro-step execution discipline активен.

## Что осталось сделать
- [TASK] TASK-BBY-008: M5-M8.
- [TASK] TASK-BBY-002: M9-M11.
- [TASK] TASK-BBY-009: связать symbol constraints и economics policy с live `exchangeInfo`/account reality.

## Классификация
- PROJECT: PROJ-BBY-ALGO-001
- TASK: TASK-BBY-002, TASK-BBY-008, TASK-BBY-009, TASK-BBY-010
- ACTION: A-BBY-2026-03-21-03
- PROCESS: PROC-BBY-001, PROC-BBY-002

## Блокеры
- Системный `crontab` для текущего пользователя пуст.
- Реальный market-data polling loop еще не собран.
- BTCUSDC при текущем депозите 30 USD и live-like filters экономически не проходит даже на neutral 3-level setup.

## Нагоняй от MAXIMUS
- Нет активного нового нагоняя.
