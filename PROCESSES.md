# PROCESSES.md

- ID: PROC-BBY-001
- Name: 5-minute algo build heartbeat
- Class: PROCESS
- Purpose: Каждые 5 минут проверять реальный прогресс по алгоритму, state файлов и блокеры, и давать короткую управленческую сводку или HEARTBEAT_OK.
- Current state: active
- What done: Формат heartbeat работает на уровне файлового/процессного контура; в контур добавлено правило немедленного перехода к действию после обновления файлов.
- What not done: Системный cron/heartbeat hook не подтвержден; runtime integration в реальный runner не готова.
- Last executed: 2026-03-20 18:46 Europe/Moscow
- Next step: Self-directive — не стоять idle; сразу собирать реальный market-data polling adapter и привязывать его к `paper_loop.py`, чтобы закрыть `TASK-BBY-010`.
- Notes: Источник формата — HEARTBEAT.md; отчет не должен заменять исполнение, если доступен следующий практический шаг.
