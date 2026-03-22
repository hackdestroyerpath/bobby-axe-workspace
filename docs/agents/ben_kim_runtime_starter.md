# Ben_Kim Runtime Starter Guide

## Status
Final baseline.

## Purpose
Короткий стартовый guide для ежедневной работы `Ben_Kim`.

Документ отвечает на вопросы:
- что открывать первым;
- в каком порядке идти по baseline-документам;
- как проходить daily cycle без путаницы.

---

# 1. What to open first

Если нужен один стартовый документ, открывать первым:
- `docs/agents/ben_kim_operational_pack.md`

Почему:
- он даёт pre-run gate;
- он даёт pre-write gate;
- он даёт short statuses, blockers, approval summaries.

---

# 2. Daily cycle — short path

Ежедневный рабочий цикл `Ben_Kim`:

1. открыть `ben_kim_operational_pack.md`
2. пройти pre-run gate
3. если execution allowed — открыть `ben_kim_strategy_rules.md`
4. во время conclusions опираться на:
   - `ben_kim_conclusion_templates.md`
   - `ben_kim_signal_discipline.md`
5. перед writeback снова свериться с:
   - `ben_kim_operational_pack.md`
   - `ben_kim_dod.md`
6. после writeback использовать:
   - `ben_kim_downstream_handoff.md`
7. если run массовый — использовать:
   - `ben_kim_mass_analysis.md`

---

# 3. Fast navigation by task

## If task = run one ticker
Open in this order:
1. `ben_kim_operational_pack.md`
2. `ben_kim_strategy_rules.md`
3. `ben_kim_conclusion_templates.md`
4. `ben_kim_signal_discipline.md`
5. `ben_kim_dod.md`

## If task = check if run may start
Open:
1. `ben_kim_operational_pack.md`

## If task = build better conclusion
Open:
1. `ben_kim_conclusion_templates.md`
2. `ben_kim_signal_discipline.md`
3. `ben_kim_strategy_rules.md`

## If task = verify result before writeback
Open:
1. `ben_kim_operational_pack.md`
2. `ben_kim_dod.md`
3. `ben_kim_signal_discipline.md`

## If task = handle downstream issue
Open:
1. `ben_kim_downstream_handoff.md`
2. `ben_kim_dod.md`

## If task = run batch/universe
Open:
1. `ben_kim_mass_analysis.md`
2. `ben_kim_operational_pack.md`
3. `ben_kim_dod.md`

---

# 4. Daily operational sequence

## Step A. Pre-run
- use `ben_kim_operational_pack.md`
- decide:
  - GO
  - GO WITH CAUTION
  - NO GO

## Step B. Strategy execution
- use `ben_kim_strategy_rules.md`
- ensure strategy logic remains canonical

## Step C. Conclusion building
- use `ben_kim_conclusion_templates.md`
- keep wording within `ben_kim_signal_discipline.md`

## Step D. Pre-write
- use `ben_kim_operational_pack.md`
- validate write readiness

## Step E. Completion check
- use `ben_kim_dod.md`
- verify technical / analytical / downstream completion logic

## Step F. Downstream handoff
- use `ben_kim_downstream_handoff.md`

## Step G. If mass-run
- use `ben_kim_mass_analysis.md`

---

# 5. Minimal runtime stack

If time is limited and only minimal stack should be used:

1. `ben_kim_operational_pack.md`
2. `ben_kim_strategy_rules.md`
3. `ben_kim_signal_discipline.md`
4. `ben_kim_dod.md`

This is the minimum safe runtime set.

---

# 6. Full runtime stack

For complete disciplined work:

1. `ben_kim_runtime_baseline.md`
2. `ben_kim_operational_pack.md`
3. `ben_kim_strategy_rules.md`
4. `ben_kim_conclusion_templates.md`
5. `ben_kim_signal_discipline.md`
6. `ben_kim_dod.md`
7. `ben_kim_downstream_handoff.md`
8. `ben_kim_mass_analysis.md`

---

# 7. One-line rule

If unsure, use this order:

`operational_pack -> strategy_rules -> conclusion_templates -> signal_discipline -> DoD -> downstream_handoff / mass_analysis`

---

# 8. Operational use

This starter guide is a quick daily reference.

For full map use:
- `docs/agents/ben_kim_runtime_baseline.md`
