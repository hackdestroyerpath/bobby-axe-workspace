# Analysis Module: Grid Synthesis Agent

## Назначение
Модуль преобразует `probability snapshot` и актуальное состояние рынка в исполнимое предложение по параметрам grid-стратегии. Документ фиксирует этап синтеза сетки, а не навязывает конкретные аналитические техники выбора диапазонов, уровней или защитных параметров.

## Роль в pipeline
`ingestion -> feature extraction -> probability engine -> grid synthesis -> neutral lifecycle`

## Входы
- `probability snapshot` из `agents/analysis/probability_engine_agent.md`;
- текущий секундный market state и связанные state snapshots;
- неизменяемые ограничения из `specs/trading_constraints.md`;
- policy исполнения и risk constraints.

## Что делает модуль
- определяет, допускается ли торговое исполнение для текущего распределения вероятностей;
- синтезирует `direction`, диапазон сетки, число уровней, защитные уровни и связанные execution constraints;
- согласует proposal с risk policy, состоянием рынка и confidence decision engine;
- создаёт `grid proposal` в том же секундном cycle, в котором probability evaluation пересекло policy-порог или зафиксировало безопасный нейтральный сценарий;
- подготавливает объяснимый `grid proposal`, который downstream-слои смогут либо исполнить, либо безопасно отклонить.

## Контракт результата
Модуль должен публиковать `grid proposal`, содержащий как минимум:
- `decision_id`;
- `symbol`;
- `timestamp`;
- `status` — `tradable`, `neutral_only` или `blocked`;
- `direction` — `LONG`, `SHORT` или `NEUTRAL`;
- `recommended_grid_bounds`;
- `grid_count`;
- `suggested_tp`;
- `suggested_sl`;
- `execution_constraints`;
- `rationale`;
- `trace_refs`.

## Правила синтеза
- Proposal должен удовлетворять диапазону уровней сетки, directional-ограничениям и risk invariants из `specs/trading_constraints.md`.
- Модуль может использовать любую внутреннюю логику вычисления границ и шагов сетки, если результат воспроизводим и объясним.
- Для `blocked` и части `neutral_only` сценариев допускается явное отсутствие исполнимых параметров, но причина должна быть описана в `rationale`.
- Grid synthesis не должен маскировать низкую уверенность probability layer: если входной snapshot слабый, статус proposal должен это отражать.

## Ограничения
- Нельзя жёстко привязывать диапазоны сетки к конкретной аналитической школе или единственной формуле как нормативному требованию документа.
- Нельзя публиковать proposal, который нарушает ограничения по числу grid-уровней, направлению, SL/TP или risk-per-grid.
- Нельзя отправлять downstream-модулям неполный proposal без явного статуса `blocked`/`neutral_only`.
- Нельзя откладывать создание live `grid proposal` до закрытия старших таймфреймов; допустим только контекст, пересчитываемый внутри секундного цикла и совместимый с `<=1m`.

## Fail-safe поведение
- При конфликте с risk constraints модуль обязан либо пересчитать proposal, либо вернуть безопасный отказ.
- При недостаточной определённости диапазона сетки модуль не должен форсировать исполнение; требуется `neutral_only` или `blocked`.
- Любая деградация синтеза должна быть трассируема до probability snapshot и входного market state.
