# STATUS.md

## Что сделано
- [PROJECT] PROJ-BBY-ALGO-001: контур проекта paper grid algo оформлен и поддерживается.
- [TASK] TASK-BBY-001: paper execution simulator core завершен.
- [TASK] TASK-BBY-003: базовый multi-symbol scan loop завершен — добавлены `evaluate_many`, `runner.py`, per-symbol decisions в state.
- [TASK] TASK-BBY-004: runner-level summary и heartbeat/status formatting реализованы через `runner.py` и `heartbeat_check.py`.
- [TASK] TASK-BBY-005: введены symbol-specific sizing overrides; BTCUSDC больше не падает на rounding-zero.
- [TASK] TASK-BBY-006: compact readiness output реализован.
- [TASK] TASK-BBY-007: final paper-ready runner cycle собран через `paper_cycle.py`.
- [TASK] TASK-BBY-008: базовый repeating loop runner подтвержден через `paper_loop.py` и локальный двухцикловый прогон.
- [ACTION] A-BBY-2026-03-20-04: изучены ключевые Binance USDS-M docs; операционные ограничения и retry/rate-limit правила занесены в память и `BINANCE_NOTES.md`.

## Что в работе
- [TASK] TASK-BBY-002: довести risk/state hardening до полной связки с runner-level transitions.
- [TASK] TASK-BBY-009: заменить/валидировать symbol constraints через реальные `exchangeInfo` filters Binance.
- [PROCESS] PROC-BBY-001: heartbeat-контур активен на уровне процесса/файлов, системный cron не подтвержден.

## Что осталось сделать
- [TASK] TASK-BBY-002: завершить финальный runner-state contract review и формально снять остаток по risk/state hardening.
- [TASK] TASK-BBY-010: привязать repeating loop к реальному market-data polling/runtime automation, а не только к статическому snapshot input.
- [TASK] TASK-BBY-002: формально снять остаток по финальному runner-state contract review, если при polling integration не всплывут новые state-разрывы.

## Классификация
- PROJECT: PROJ-BBY-ALGO-001
- TASK: TASK-BBY-001, TASK-BBY-002, TASK-BBY-003, TASK-BBY-004, TASK-BBY-005, TASK-BBY-006, TASK-BBY-007, TASK-BBY-008, TASK-BBY-009
- ACTION: A-BBY-2026-03-20-01, A-BBY-2026-03-20-02, A-BBY-2026-03-20-03, A-BBY-2026-03-20-04
- PROCESS: PROC-BBY-001

## Блокеры
- Системный `crontab` для текущего пользователя пуст. Автоконтроль через cron не подтвержден в этом runtime.
- Реальный market-data polling loop еще не собран.

## Нагоняй от MAXIMUS
- Нет активного нового нагоняя.
�.

## Нагоняй от MAXIMUS
- Нет активного нового нагоняя.
 собран.

## Нагоняй от MAXIMUS
- Нет активного нового нагоняя.
