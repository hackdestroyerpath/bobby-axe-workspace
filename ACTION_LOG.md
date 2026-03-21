# ACTION_LOG.md

- Time: 2026-03-20 15:50 Europe/Moscow
- Related class: PROJECT
- Related ID: PROJ-BBY-ALGO-001
- Done: Оформлен проектный и task-контур для Bobby paper grid algo.
- Result: Появились PROJECTS.md / TASKS.md / PROCESSES.md со статусами и зависимостями.
- Next: Закрыть TASK-BBY-002 и перейти к scanner loop.

- Time: 2026-03-20 15:50 Europe/Moscow
- Related class: TASK
- Related ID: TASK-BBY-002
- Done: Усилен risk lock от paper results.
- Result: Добавлены invalidation flatten, loss_streak update, устранен ложный DAILY_LOCK от open position.
- Next: Довести state transitions и runner integration.

- Time: 2026-03-20 15:50 Europe/Moscow
- Related class: ACTION
- Related ID: A-BBY-2026-03-20-01
- Done: Добавлены и прогнаны тесты симулятора.
- Result: `test_simulator.py` проходит, `agent.py` исполняется.
- Next: Перейти к multi-symbol scanner.

- Time: 2026-03-20 15:50 Europe/Moscow
- Related class: PROCESS
- Related ID: PROC-BBY-001
- Done: Проверен системный cron-контур.
- Result: `crontab -l` пуст; heartbeat подтвержден только на уровне процесса/файлов, не системного cron.
- Next: Использовать heartbeat-процесс и при необходимости позже поднять cron отдельно.

- Time: 2026-03-20 16:25 Europe/Moscow
- Related class: TASK
- Related ID: TASK-BBY-003
- Done: Реализован multi-symbol scanner loop.
- Result: Добавлены `runner.py`, `evaluate_many`, `multi_snapshot.json`, per-symbol decisions; тесты проходят.
- Next: Исправить symbol-specific sizing constraints и runner-level summary.

- Time: 2026-03-20 16:25 Europe/Moscow
- Related class: ACTION
- Related ID: A-BBY-2026-03-20-02
- Done: Выполнен локальный прогон multi-symbol runner.
- Result: BTCUSDC сначала отклонялся по sizing, ETHUSDC оценивался штатно.
- Next: Ввести symbol-specific sizing/filtering.

- Time: 2026-03-20 16:59 Europe/Moscow
- Related class: TASK
- Related ID: TASK-BBY-005
- Done: Исправлены symbol-specific sizing constraints.
- Result: Добавлены `symbol_overrides` и symbol-aware risk engine; BTCUSDC теперь проходит sizing и выдает `GRID_READY` в локальном прогоне.
- Next: Добавить runner-level summary и heartbeat/status formatting.

- Time: 2026-03-20 17:39 Europe/Moscow
- Related class: TASK
- Related ID: TASK-BBY-004
- Done: Реализованы runner-level summary и heartbeat/status formatting.
- Result: Добавлены `runner.py --summary-only` и `heartbeat_check.py`; локальный прогон выдает компактную сводку и heartbeat-формат.
- Next: Добавить readiness output и собрать final paper-ready runner cycle.

- Time: 2026-03-20 17:39 Europe/Moscow
- Related class: TASK
- Related ID: TASK-BBY-007
- Done: Собран final paper-ready runner cycle.
- Result: Добавлен `paper_cycle.py`; локальный прогон выдает decisions + summary + `readiness=PAPER_READY`.
- Next: Собрать repeating loop runner.

- Time: 2026-03-21 18:24 Europe/Moscow
- Related class: ACTION
- Related ID: A-BBY-2026-03-20-04
- Done: Изучена ключевая документация Binance USDS-M Futures.
- Result: В память и `BINANCE_NOTES.md` занесены base URLs, testnet URLs, `exchangeInfo` rules, rate limits, 429/418/503/-1008 handling.
- Next: Использовать эти правила для TASK-BBY-009 и future live connector design.

- Time: 2026-03-21 11:43 Europe/Moscow
- Related class: TASK
- Related ID: TASK-BBY-010
- Done: Внедрены M2 / M3 / M4.
- Result: default levels сжаты к 1..5, directional TP/SL добавлены в grid plan, neutral-grid removal rule задан; локальный прогон после изменений выявил economics blocker по BTCUSDC на текущем депозите.
- Next: Перейти к M5 — define loop input contract.
