# Ben_Kim Downstream Handoff

## Status
Final baseline.

## Purpose
Канонический документ по передаче результатов `Ben_Kim` downstream-агентам.

Документ фиксирует:
- canonical handoff;
- handoff к `Jusetta`;
- handoff к `Maffi`;
- границу между canonical и presentation layers.

---

# 1. Canonical handoff

## Source of truth
Downstream source of truth для `Ben_Kim`:
- `collector.analysis_results`

## Canonical row minimum
Каждая canonical row должна содержать минимум:
- `analysis_id`
- `snapshot_id`
- `symbol`
- `frame`
- `strategy_id`
- `strategy_name`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `status`
- `result_code`

## Core principle
Canonical handoff:
- не сокращает strategy set;
- не меняет strategy identity;
- не убирает frame structure;
- не делает narrative reinterpretation.

---

# 2. Presentation handoff

## Definition
Presentation handoff — это derived layer, который строится поверх canonical handoff.

## What it may contain
- summary
- preview
- human-readable digest
- grouped narrative
- simplified reporting text

## Core principle
Presentation handoff:
- не является source of truth;
- не заменяет canonical analytical layer;
- допустим только как derived representation.

---

# 3. Handoff to Jusetta

## What Jusetta must read
`Jusetta` должна читать:
- `collector.analysis_results`

## What Jusetta receives
Минимально:
- `snapshot_id`
- `symbol`
- `frame`
- `strategy_id`
- `strategy_name`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `status`
- `result_code`

## What Jusetta may do
Разрешено:
- formatting
- grouping by frame
- grouping by ticker
- preview creation
- summary creation
- presentation simplification

## What Jusetta must not do
Запрещено:
- менять `strategy_id`
- менять `strategy_name`
- заменять 6 strategies на 3 narrative categories как основной слой
- схлопывать `18 conclusions` в меньшее число без маркировки derived layer
- выдавать summary-layer как canonical Ben_Kim output

## Cardinality rule for Jusetta
Если по тикеру есть:
- `6 strategies × 3 frames = 18 conclusions`

то Jusetta должна:
- иметь доступ к этим 18 logical units;
- понимать, что любое их сокращение уже является derived summary.

## Handoff correctness for Jusetta
Handoff считается корректным, если:
1. Jusetta читает canonical layer
2. strategy identity сохранена
3. frame identity сохранена
4. snapshot binding сохранён
5. summary явно вторичен
6. canonical cardinality не потеряна

---

# 4. Handoff to Maffi

## What Maffi must read
`Maffi` должен читать:
- `collector.analysis_results`

## What Maffi receives
Минимально:
- `analysis_id`
- `snapshot_id`
- `symbol`
- `frame`
- `strategy_id`
- `strategy_name`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `status`
- `result_code`

## Why this matters
Для `Maffi` Ben_Kim output — это:
- strategy-level analytical basis;
- frame-level evidence;
- upstream decision-support layer.

## What Maffi must not do
Запрещено:
- читать human-readable summary как primary source;
- игнорировать strategy identity;
- терять frame-level distinctions;
- строить grid logic по preview-layer вместо canonical rows.

## Handoff correctness for Maffi
Handoff считается корректным, если:
1. Maffi читает canonical analytical layer
2. получает strategy-level rows
3. сохраняет frame-level distinctions
4. сохраняет snapshot binding
5. агрегирует сам, а не читает чужую summary-агрегацию

---

# 5. Canonical vs presentation boundary

## Canonical handoff answers
"Что реально сказал Ben_Kim?"

## Presentation handoff answers
"Как это удобнее показать человеку?"

## Forbidden mixing
Запрещено:
1. presentation handoff выдавать как canonical result
2. сначала схлопывать strategy/frame structure, а потом считать это analytical source
3. менять strategy identities внутри presentation layer без явной маркировки
4. использовать presentation handoff как source для decision-stage downstream

---

# 6. Operational test for source type

## If YES to all below -> canonical handoff
- сохраняется `strategy_id`?
- сохраняется `strategy_name`?
- сохраняется `frame`?
- сохраняется `snapshot_id`?
- сохраняется исходная cardinality logical units?

## If NO to any of the above -> likely presentation handoff
И такой слой нельзя использовать как primary source of truth.

---

# 7. Downstream correctness rules

## Rule D1
Downstream должен читать canonical source.

## Rule D2
Strategy identity должна доживать downstream.

## Rule D3
Frame identity должна доживать downstream.

## Rule D4
Snapshot identity должна доживать downstream.

## Rule D5
Summary/preview/reporting layers должны быть явно marked as derived.

## Rule D6
Mock/test/preview layers не могут выступать production source.

## Rule D7
Weak/strong distinctions нельзя завышать downstream-пересказом.

---

# 8. Operational use

Этот документ является baseline для:
- downstream handoff validation;
- Jusetta consumption discipline;
- Maffi consumption discipline;
- separation of canonical vs presentation layers.
