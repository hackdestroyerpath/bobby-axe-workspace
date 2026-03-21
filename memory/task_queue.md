# Task Queue

| ID | Task | Owner | Status | Phase | Depends on | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | Описать universe scanner для USDC futures | market_data_subagent | todo | 2 | 1 | Покрыть live-сканирование всех доступных USDC futures инструментов. |
| T-002 | Описать vertical volume analyzer | vertical_volume_subagent | todo | 2 | 1 | Разрешённый источник анализа 4.1 из ТЗ. |
| T-003 | Описать horizontal volume analyzer | horizontal_volume_subagent | todo | 2 | 1 | Разрешённый источник анализа 4.2 из ТЗ. |
| T-004 | Описать Fibonacci levels analyzer | fibonacci_subagent | todo | 2 | 1 | Разрешённый источник анализа 4.3 из ТЗ. |
| T-005 | Описать tick analyzer (sum + timing) | tick_subagent | todo | 2 | 1 | Разрешённый источник анализа 4.4 из ТЗ. |
| T-006 | Описать activity analyzer (trades per second) | activity_subagent | todo | 2 | 1 | Разрешённый источник анализа 4.5 из ТЗ. |
| T-007 | Описать macro/context activity analyzer | context_activity_subagent | todo | 2 | 1 | Разрешённый источник анализа 4.7: BTC + sector + SPX и т.д. |
| T-008 | Описать Elliott waves analyzer | elliott_wave_subagent | todo | 2 | 1 | Разрешённый источник анализа 4.8 из ТЗ. |
| T-009 | Описать signal aggregator | signal_aggregator_subagent | todo | 3 | T-002,T-003,T-004,T-005,T-006,T-007,T-008 | Агрегирует только разрешённые сигналы. |
| T-010 | Описать scoring/weighting engine | scoring_subagent | todo | 3 | T-009 | Формирует LONG / SHORT / NEUTRAL вероятности и веса источников. |
| T-011 | Описать grid parameter generator | grid_generation_subagent | todo | 3 | T-010 | Полностью генерирует ticker, range, grids, SL, TP, side. |
| T-012 | Описать neutral-grid exit logic | neutral_exit_subagent | todo | 4 | T-011 | Включить webhook-triggered и protective cancellation logic. |
| T-013 | Описать exchange adapter | execution_subagent | todo | 4 | T-011 | Binance API, isolated margin, leverage slider checks, order placement/cancel. |
| T-014 | Описать risk validation engine | risk_subagent | todo | 4 | T-011 | Проверяет risk constraints до размещения. |
| T-015 | Описать state store | state_store_subagent | todo | 4 | T-011 | Хранение grid lifecycle, signal snapshots и execution state. |
| T-016 | Описать simulation/backtest harness | simulation_subagent | todo | 5 | T-009,T-011,T-014 | Нужен для LONG / SHORT / NEUTRAL сценариев. |
| T-017 | Описать monitoring/alerts | observability_subagent | todo | 7 | T-013,T-014,T-015 | Метрики, алерты, аварийные сценарии, webhook failures. |
| T-018 | Описать memory update workflow | supervisor | todo | 7 | T-015,T-017 | Обновление plan/queue/questions/decision log после каждого шага. |
| T-019 | Подготовить пакет приёмки | supervisor | todo | 8 | T-016,T-017,T-018 | Сверка с DoD и acceptance criteria. |
