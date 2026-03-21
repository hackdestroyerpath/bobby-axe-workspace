# Current Plan

## Цель
Заложить стартовый roadmap по проектированию и приёмке автоматической gridbot-системы для Binance USDC futures на базе требований из `workspace_start/ТЗ.txt`.

## Phased Roadmap

### Phase 1. Формализация требований из `workspace_start/ТЗ.txt`
- Выделить функциональные, операционные и организационные требования из ТЗ.
- Нормализовать терминологию: `NEUTRAL` / `NETURAL`, `USDC futures`, `grid`, `subagent`, `allowed signals`.
- Зафиксировать явные запреты: только Binance API, только gridbot, только USDC futures, только разрешённые источники анализа.
- Уточнить недостающие требования через `memory/open_questions.md`.
- Результат этапа: согласованный baseline требований и инвариантов.

### Phase 2. Архитектура системы и роли субагентов
- Разделить систему на supervisor-слой, аналитические субагенты, execution-слой, risk-слой и observability-слой.
- Определить отдельного субагента для каждого разрешённого источника анализа.
- Зафиксировать границы ответственности между supervisor и субагентами.
- Описать orchestration flow: ingest -> analyze -> aggregate -> validate -> execute -> monitor -> review.
- Результат этапа: архитектурная схема и карта ролей субагентов.

### Phase 3. Контракты данных и сигналов
- Описать входные и выходные контракты для market data, derived signals, scoring, grid proposals и execution intents.
- Зафиксировать обязательные поля для полной генерации параметров сетки: ticker, side, price range, grids, SL, TP, leverage/margin settings.
- Определить формат сигналов от каждого субагента и единый формат их агрегации.
- Разделить сырые данные, вычисленные признаки и финальные торговые решения.
- Результат этапа: спецификация данных и интерфейсов между модулями.

### Phase 4. Risk / execution design
- Описать risk constraints до размещения ордеров: max risk per grid, isolated margin, leverage slider validation, pre-trade checks.
- Зафиксировать сценарии размещения и отмены для LONG, SHORT и NEUTRAL.
- Описать neutral-grid exit logic, включая webhook/event-based снятие и защитные условия.
- Спроектировать exchange adapter и execution orchestration с учётом высокой скорости размещения.
- Результат этапа: дизайн безопасного и проверяемого исполнения.

### Phase 5. Симуляция / backtest design
- Определить, как эмулировать live data, тики, активности и сигналы разрешённых источников.
- Спроектировать сценарии backtest/simulation для LONG, SHORT и NEUTRAL grid.
- Описать метрики успеха: expectancy, drawdown, hit rate, execution quality, cancellation behavior.
- Зафиксировать ограничения симуляции относительно реального Binance execution.
- Результат этапа: воспроизводимый дизайн валидации стратегии до live-запуска.

### Phase 6. Реализация live execution
- Подготовить план реализации ingestion, subagent orchestration, scoring, risk validation и exchange execution небольшими задачами.
- Разбить реализацию на атомарные deliverables для субагентов.
- Зафиксировать порядок интеграции модулей и критерии готовности каждого блока.
- Подготовить supervisor workflow для контроля, сборки и тестирования артефактов субагентов.
- Результат этапа: пошаговый execution plan для production-сборки.

### Phase 7. Наблюдаемость, логирование, аварийные сценарии
- Описать требования к логам, audit trail и обновлению memory-файлов.
- Определить monitoring/alerts для data gaps, risk violations, order failures, stuck grids и webhook issues.
- Зафиксировать аварийные сценарии и безопасные fallback-действия.
- Определить, как фиксируются решения supervisor и статусы задач.
- Результат этапа: план observability и operational safety.

### Phase 8. Приёмка
- Проверить соответствие acceptance criteria и definition of done.
- Убедиться, что все разрешённые источники анализа покрыты отдельными субагентами.
- Проверить, что решение формируется только из разрешённых сигналов и что grid параметры генерируются полностью.
- Подтвердить наличие сценариев для LONG, SHORT и NEUTRAL, а также pre-trade risk validation.
- Результат этапа: пакет артефактов для проектной приёмки.

## Immediate Next Steps
1. Синхронизировать `memory/task_queue.md` с фазами roadmap.
2. Уточнить открытые вопросы и зависимости перед детальной декомпозицией.
3. Связать roadmap с `specs/acceptance_criteria.md` и `checklists/definition_of_done.md`.
