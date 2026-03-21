# Task Queue

| ID | Task | Owner | Status | Depends on | Notes |
| --- | --- | --- | --- | --- | --- |
| T-001 | Уточнить архитектурную схему системы | supervisor | todo | ТЗ | Отразить в `specs/system_architecture.md` |
| T-002 | Описать торговые ограничения и инварианты | risk_agent | todo | ТЗ | Сверить с Binance USDC futures ограничениями позже |
| T-003 | Сформировать контракты всех субагентов | orchestration_agent | todo | T-001 | Зафиксировать входы/выходы |
| T-004 | Разбить систему на атомарные задачи реализации | supervisor | todo | T-001,T-003 | Создать файлы в `tasks/` |
