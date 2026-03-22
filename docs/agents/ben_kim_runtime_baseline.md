# Ben_Kim Runtime Baseline

## Status
Final baseline index.

## Purpose
Единая точка входа в operational baseline `Ben_Kim`.

Документ отвечает на вопросы:
- какие baseline-документы являются каноническими;
- как они связаны между собой;
- чем пользоваться в ежедневной работе;
- какой документ считать главным в конкретной ситуации.

---

# 1. Core baseline set

Ниже — канонический baseline set `Ben_Kim`.

## Strategy / analysis core
1. `docs/agents/ben_kim_strategy_rules.md`
2. `docs/agents/ben_kim_conclusion_templates.md`
3. `docs/agents/ben_kim_signal_discipline.md`
4. `docs/agents/ben_kim_dod.md`

## Operational core
5. `docs/agents/ben_kim_operational_pack.md`
6. `docs/agents/ben_kim_downstream_handoff.md`
7. `docs/agents/ben_kim_mass_analysis.md`

---

# 2. Role of each document

## ben_kim_strategy_rules.md
Главный документ по стратегиям.

Использовать, когда нужно понять:
- что читает стратегия;
- когда стратегия usable;
- когда partial;
- о чём стратегия имеет право говорить.

## ben_kim_conclusion_templates.md
Главный документ по формулировке conclusions.

Использовать, когда нужно понять:
- как строить вывод;
- как звучат weak/strong cases;
- какой wording допустим.

## ben_kim_signal_discipline.md
Главный документ по ограничению силы сигнала.

Использовать, когда нужно понять:
- чего нельзя говорить;
- как не завышать сигнал;
- как работает decision ladder.

## ben_kim_dod.md
Главный документ по критериям завершения.

Использовать, когда нужно понять:
- завершён ли execution технически;
- завершён ли он аналитически;
- downstream корректно ли его использует.

## ben_kim_operational_pack.md
Главный документ по daily operational cycle.

Использовать, когда нужно:
- пройти pre-run gate;
- пройти pre-write gate;
- быстро выдать status/blocker/approval summary.

## ben_kim_downstream_handoff.md
Главный документ по передаче результата downstream.

Использовать, когда нужно понять:
- что передавать `Jusetta`;
- что передавать `Maffi`;
- где проходит граница canonical vs presentation.

## ben_kim_mass_analysis.md
Главный документ по масштабированию execution.

Использовать, когда нужно:
- запускать batch;
- запускать universe execution;
- сегментировать usable/partial/skip;
- делать batch summary.

---

# 3. Daily-use navigation

## Scenario A — single ticker analysis
Использовать:
1. `ben_kim_operational_pack.md`
2. `ben_kim_strategy_rules.md`
3. `ben_kim_conclusion_templates.md`
4. `ben_kim_signal_discipline.md`
5. `ben_kim_dod.md`

## Scenario B — before writeback
Использовать:
1. `ben_kim_operational_pack.md`
2. `ben_kim_dod.md`
3. `ben_kim_signal_discipline.md`

## Scenario C — downstream question
Использовать:
1. `ben_kim_downstream_handoff.md`
2. `ben_kim_dod.md`

## Scenario D — batch / universe run
Использовать:
1. `ben_kim_mass_analysis.md`
2. `ben_kim_operational_pack.md`
3. `ben_kim_dod.md`

## Scenario E — strategy wording conflict
Использовать:
1. `ben_kim_strategy_rules.md`
2. `ben_kim_conclusion_templates.md`
3. `ben_kim_signal_discipline.md`

---

# 4. Canonical work order

Для ежедневного execution `Ben_Kim` должен ориентироваться на такой work order:

1. `ben_kim_operational_pack.md`
   - пройти pre-run gate
2. `ben_kim_strategy_rules.md`
   - понять стратегические рамки
3. `ben_kim_conclusion_templates.md`
   - построить conclusions
4. `ben_kim_signal_discipline.md`
   - проверить силу формулировок
5. `ben_kim_dod.md`
   - проверить completion
6. `ben_kim_downstream_handoff.md`
   - корректно передать результат downstream
7. `ben_kim_mass_analysis.md`
   - если execution batch/universe-scale

---

# 5. Main document by context

## If one document must be opened first for day-to-day work
Use:
- `docs/agents/ben_kim_operational_pack.md`

Почему:
- он даёт pre-run и pre-write logic;
- быстро приводит в рабочий execution режим;
- содержит operational statuses и blockers.

## If one document must be opened first for analytical quality
Use:
- `docs/agents/ben_kim_strategy_rules.md`

## If one document must be opened first for wording discipline
Use:
- `docs/agents/ben_kim_signal_discipline.md`

---

# 6. Operational baseline principle

Все документы baseline set нужно читать как один связанный пакет.

При конфликте логика приоритета такая:
1. `ben_kim_dod.md` — критерии завершения
2. `ben_kim_operational_pack.md` — operational execution logic
3. `ben_kim_strategy_rules.md` — strategy constraints
4. `ben_kim_signal_discipline.md` — wording and confidence limits
5. `ben_kim_conclusion_templates.md` — preferred output construction
6. `ben_kim_downstream_handoff.md` — downstream use rules
7. `ben_kim_mass_analysis.md` — scaling logic

---

# 7. Practical use

Этот index-файл использовать как:
- entry point;
- navigation map;
- reference of references.

Он не заменяет остальные baseline-документы, а связывает их в единый runtime pack.
