# PROJECTS.md

- ID: PROJ-BBY-ALGO-001
- Name: Bobby paper grid trading algo
- Class: PROJECT
- Status: active
- Owner: Bobby_Axe
- Goal: Довести Bobby до рабочего paper-trading алгоритма для Binance USDC futures grid с симуляцией исполнений, учетом inventory/PnL, risk lock, heartbeat и runner loop.
- реально сделано: оформлен управленческий контур, завершен simulator core, оформлен operational spec, усилен risk/state hardening, добавлены и пройдены state tests, реализован базовый multi-symbol runner cycle (`runner.py`) и тест его прохода, снят ложный runtime `DAILY_LOCK` через symbol-aware inventory/mark-to-market fix и подтвержден свежий live `PAPER_READY`.
- не сделано: системный cron не подтвержден; runtime automation регулярного запуска не доведена; по BTCUSDC еще нужна явная symbol-aware policy при economics/regime constraints.
- Related tasks: TASK-BBY-001, TASK-BBY-002, TASK-BBY-003, TASK-BBY-004, TASK-BBY-005
- Last update: 2026-03-20 16:24 Europe/Moscow
- Notes: Live trading не входит в текущий контур. Только paper-only.
