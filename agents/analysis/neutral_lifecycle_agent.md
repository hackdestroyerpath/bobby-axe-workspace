# Analysis Module: Neutral Lifecycle Agent

## Назначение
Модуль определяет правила сопровождения, переоценки и снятия сценария `NEUTRAL` после публикации grid proposal. Документ описывает lifecycle-логику для нейтрального режима, а не фиксирует конкретные триггеры одной аналитической школы.

## Роль в pipeline
`ingestion -> feature extraction -> probability engine -> grid synthesis -> neutral lifecycle`

## Входы
- `grid proposal` и `probability snapshot` текущего decision cycle;
- live execution state по активной `NEUTRAL`-сетке;
- event/webhook-события, влияющие на валидность нейтрального сценария;
- risk and exchange state, включая рассинхронизацию с биржей и нарушение инвариантов.

## Что делает модуль
- определяет условия активации, сопровождения и снятия `NEUTRAL`-сценария;
- отслеживает потерю актуальности диапазона, деградацию качества данных и изменения risk/exchange state;
- инициирует пересмотр `NEUTRAL`-grid при существенном изменении вероятностного режима;
- формирует причины для `neutral_grid_activate`, `neutral_grid_update`, `neutral_grid_remove`, `neutral_grid_invalidated`;
- обеспечивает безопасное завершение `NEUTRAL`, если сопровождение больше не соответствует policy.

## Контракт результата
Модуль должен публиковать lifecycle-решения со следующими полями:
- `decision_id`;
- `symbol`;
- `timestamp`;
- `neutral_state` — `pending`, `active`, `update_required`, `remove_required`, `invalidated`, `closed`;
- `trigger_type` — `probability_change`, `market_structure_change`, `risk_violation`, `exchange_desync`, `webhook`, `manual_override`, и т.д.;
- `action` — `keep`, `update`, `remove`, `block_reentry`;
- `reason_codes[]`;
- `trace_refs`.

## Правила сопровождения
- `NEUTRAL`-режим должен регулярно переоцениваться на основе нового probability snapshot и execution state.
- Снятие `NEUTRAL` обязательно при нарушении risk constraints, потере согласованности с биржей или явной невалидности диапазона.
- Event/webhook-based управление допускается, но не заменяет обязательные fail-safe проверки.
- Модуль обязан различать временную необходимость обновления сетки и окончательную инвалидацию сценария.

## Ограничения
- Нельзя определять lifecycle только через один-единственный тип аналитического сигнала.
- Нельзя сохранять активную `NEUTRAL`-сетку, если downstream-состояние противоречит risk policy или exchange reality.
- Нельзя снимать `NEUTRAL` без фиксированных причин и traceability.

## Fail-safe поведение
- При неизвестном или конфликтном состоянии биржи модуль должен инициировать безопасную остановку/снятие `NEUTRAL`.
- При пропаже подтверждения lifecycle-state модуль обязан перейти к консервативному сценарию и потребовать повторную синхронизацию.
- При резком изменении вероятностного режима модуль обязан либо потребовать update, либо завершить текущий `NEUTRAL`-сценарий.
