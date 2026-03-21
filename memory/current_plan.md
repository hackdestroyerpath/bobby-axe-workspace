# Current Plan

## Цель
Заложить стартовый roadmap по проектированию и приёмке автоматической gridbot-системы для Binance USDC futures на базе требований из `workspace_start/ТЗ.txt` и новой архитектуры с автономным `probabilistic_decision_engine`.

## Phased Roadmap

### Phase 1. Формализация требований из `workspace_start/ТЗ.txt`
- Выделить функциональные, операционные и организационные требования из ТЗ.
- Нормализовать терминологию: `NEUTRAL` / `NETURAL`, `USDC futures`, `grid`, `probabilistic_decision_engine`, `probability snapshot`.
- Зафиксировать явные запреты: только Binance API, только gridbot, только USDC futures.
- Уточнить недостающие требования через `memory/open_questions.md`.
- Результат этапа: согласованный baseline требований и инвариантов.

### Phase 2. Архитектура системы и центральный decision engine
- Разделить систему на ingestion-слой, `probabilistic_decision_engine`, execution-слой, risk-слой и observability-слой.
- Зафиксировать, что decision engine получает live tick stream по всем USDC futures и самостоятельно формирует рыночное состояние и вероятности.
- Описать границы ответственности между decision engine, execution и risk.
- Описать orchestration flow: ingest -> derive state -> calculate probabilities -> validate -> execute -> monitor -> review.
- Результат этапа: архитектурная схема и карта ролей модулей.

### Phase 3. Контракты данных и decision snapshots
- Описать входные и выходные контракты для market data, state snapshots, probability snapshots, grid proposals и execution intents.
- Зафиксировать обязательные поля для полной генерации параметров сетки: ticker, side, price range, grids, SL, TP, leverage/margin settings.
- Определить единый формат артефактов, публикуемых `probabilistic_decision_engine`.
- Разделить сырые данные, вычисленные признаки и финальные торговые решения.
- Результат этапа: спецификация данных и интерфейсов между модулями.

### Phase 4. Risk / execution design
- Описать risk constraints до размещения ордеров: max risk per grid, isolated margin, leverage slider validation, pre-trade checks.
- Зафиксировать сценарии размещения и отмены для LONG, SHORT и NEUTRAL.
- Описать neutral-grid exit logic, включая webhook/event-based снятие и защитные условия.
- Спроектировать exchange adapter и execution orchestration с учётом высокой скорости размещения.
- Результат этапа: дизайн безопасного и проверяемого исполнения.

### Phase 5. Симуляция / backtest design
- Определить, как эмулировать live data, tick stream, derived features и probability snapshots.
- Спроектировать сценарии backtest/simulation для LONG, SHORT и NEUTRAL grid.
- Описать метрики успеха: expectancy, drawdown, hit rate, execution quality, cancellation behavior.
- Зафиксировать ограничения симуляции относительно реального Binance execution.
- Результат этапа: воспроизводимый дизайн валидации стратегии до live-запуска.

### Phase 6. Реализация live execution
- Подготовить план реализации ingestion, decision engine, risk validation и exchange execution небольшими задачами.
- Разбить реализацию на атомарные deliverables по модулям, а не по источникам аналитики.
- Зафиксировать порядок интеграции модулей и критерии готовности каждого блока.
- Подготовить workflow для контроля, сборки и тестирования артефактов системы.
- Результат этапа: пошаговый execution plan для production-сборки.

### Phase 7. Наблюдаемость, логирование, аварийные сценарии
- Описать требования к логам, audit trail и обновлению memory-файлов.
- Определить monitoring/alerts для data gaps, risk violations, probability degradation, order failures, stuck grids и webhook issues.
- Зафиксировать аварийные сценарии и безопасные fallback-действия.
- Определить, как фиксируются расчёты decision engine, решения supervisor и статусы задач.
- Результат этапа: план observability и operational safety.

### Phase 8. Приёмка
- Проверить соответствие acceptance criteria и definition of done.
- Убедиться, что решение автономно принимает directional/neutral решения через `probabilistic_decision_engine`.
- Проверить трассировку `state snapshot` / `probability snapshot` / `grid proposal` и корректность деградации в `NEUTRAL`.
- Подтвердить наличие сценариев для LONG, SHORT и NEUTRAL, а также pre-trade risk validation.
- Результат этапа: пакет артефактов для проектной приёмки.

## Immediate Next Steps
1. Синхронизировать `memory/task_queue.md` с фазами roadmap и модульной декомпозицией.
2. Уточнить открытые вопросы и зависимости перед детальной декомпозицией decision engine.
3. Связать roadmap с `specs/acceptance_criteria.md` и `checklists/definition_of_done.md`.
