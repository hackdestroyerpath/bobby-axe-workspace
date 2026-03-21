# Definition of Done

Задача или этап считаются завершёнными только если выполнены все пункты ниже.

## 1. Scope and ownership
- Результат соответствует постановке и явно привязан к конкретной задаче или этапу.
- Ответственный модуль, decision engine или supervisor указан явно.
- Границы изменений и затронутые артефакты перечислены.

## 2. Requirements compliance
- Решение не нарушает ограничения ТЗ: только Binance API, только gridbot, только USDC futures.
- Для аналитических решений используется автономный `probabilistic_decision_engine`, публикующий `state snapshot`, `probability snapshot` и `grid proposal`.
- Для вероятностного решения зафиксированы внутренние признаки, правила деградации и границы ответственности decision/execution/risk слоёв.

## 3. Deliverable quality
- Описаны входы, выходы, зависимости и критерии проверки.
- Для grid-related задач полностью определены обязательные параметры: ticker, side, price_up, price_down, grids, SL, TP, margin/leverage expectations.
- Для risk/execution задач зафиксированы pre-trade validations, probability traceability и failure handling.

## 4. Verification
- Выполнены проверки, ревью или иные programmatic/manual checks, либо явно зафиксировано, почему они ограничены.
- Для изменений в логике есть понятный способ верификации.
- Для сценариев торговли учтены варианты LONG, SHORT и NEUTRAL там, где это применимо.
- Для деградационных сценариев подтверждено безопасное смещение в `NEUTRAL` или безопасный отказ.

## 5. Workspace memory hygiene
- Обновлены `memory/current_plan.md`, `memory/task_queue.md` и при необходимости `memory/open_questions.md`.
- Существенные решения и допущения отражены в `memory/decision_log.md`.
- Статус задачи переведён в актуальное состояние без расхождения между артефактами.

## 6. Acceptance readiness
- Артефакт готов к передаче следующему этапу или модулю без скрытых допущений.
- Ссылки на связанные спецификации, чеклисты и результаты проверки приложены.
- Нет известных блокеров, не отражённых в `memory/open_questions.md` или task queue.
