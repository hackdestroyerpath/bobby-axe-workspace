# PROCESSES.md

- ID: PROC-BBY-001
- Name: 5-minute algo build heartbeat
- Class: PROCESS
- Purpose: Каждые 5 минут проверять реальный прогресс по алгоритму, state файлов и блокеры, и давать короткую управленческую сводку или HEARTBEAT_OK.
- Current state: active
- Last executed: 2026-03-21 11:37 Europe/Moscow
- Next step: Привязать heartbeat к repeating loop runner.
- Notes: Источник формата — HEARTBEAT.md.

- ID: PROC-BBY-002
- Name: Micro-step execution discipline
- Class: PROCESS
- Purpose: Делить работу на маленькие последовательные шаги, после каждого шага фиксировать прогресс, вычеркивать завершенное, возвращаться к последнему незакрытому шагу и продолжать без остановки.
- Current state: active
- Last executed: 2026-03-21 11:37 Europe/Moscow
- Next step: Применять к TASK-BBY-002 / TASK-BBY-008 / TASK-BBY-010.
- Notes: Self-check: если завис или остановился без блокера — выбрать следующий минимальный шаг самостоятельно.
