# Task Queue

| ID | Task | Owner | Status | Phase | Depends on | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | Описать universe scanner для USDC futures | market_data_subagent | todo | 2 | 1 | Покрыть live-сканирование всех доступных USDC futures инструментов. |
| T-002 | Описать feature extraction stage | feature_extraction_subagent | todo | 2 | 1 | Извлечение микро-признаков из ticks и market snapshots без жёсткого списка индикаторов. |
| T-003 | Описать probability engine stage | probability_engine_subagent | todo | 2 | T-002 | Нормализованные вероятности LONG / SHORT / NEUTRAL и правила деградации. |
| T-004 | Описать grid synthesis stage | grid_synthesis_subagent | todo | 3 | T-003 | Генерация диапазона, grid count, SL/TP и execution proposal. |
| T-005 | Описать neutral lifecycle stage | neutral_lifecycle_subagent | todo | 4 | T-004 | Event/webhook-based сопровождение и снятие NEUTRAL без привязки к одной аналитической школе. |
| T-006 | Описать exchange adapter | execution_subagent | todo | 4 | T-004 | Binance API, isolated margin, leverage slider checks, order placement/cancel. |
| T-007 | Описать risk validation engine | risk_subagent | todo | 4 | T-004 | Проверяет risk constraints до размещения. |
| T-008 | Описать state store | state_store_subagent | todo | 4 | T-004,T-005 | Хранение grid lifecycle, decision snapshots и execution state. |
| T-009 | Описать simulation/backtest harness | simulation_subagent | todo | 5 | T-003,T-004,T-007 | Нужен для LONG / SHORT / NEUTRAL сценариев. |
| T-010 | Описать monitoring/alerts | observability_subagent | todo | 7 | T-006,T-007,T-008 | Метрики, алерты, аварийные сценарии, webhook failures. |
| T-011 | Описать memory update workflow | supervisor | todo | 7 | T-008,T-010 | Обновление plan/queue/questions/decision log после каждого шага. |
| T-012 | Подготовить пакет приёмки | supervisor | todo | 8 | T-009,T-010,T-011 | Сверка с DoD и acceptance criteria. |
