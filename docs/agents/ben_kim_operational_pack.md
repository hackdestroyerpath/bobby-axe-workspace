# Ben_Kim Operational Pack

## Status
Final baseline.

## Purpose
Единый operational document для ежедневного рабочего цикла `Ben_Kim`.

Содержит:
- final pre-run baseline;
- final pre-write baseline;
- short status templates;
- blocker templates;
- approval-ready summaries.

---

# 1. Final Pre-Run Baseline

## Identity
Перед запуском подтверждено:
- `snapshot_id`
- `symbol`
- `correlation_id`

## Discovery
- snapshot найден
- lookup успешен
- artifact валиден

## Readiness
- `1m = ready`
- `5m = ready`
- `60m = ready`

## Payload
- `payload_status = ready`
- `result_code = ok`
- payload соответствует правильному symbol

## Core feature integrity
- strategy core fields присутствуют
- critical indicators не semantically broken
- payload не скрыто partial

## Strategy registry integrity
- canonical registry прочитан
- `strategy_id / strategy_name` валидны
- strategy set approved for `Ben_Kim`

## Execution scope
- expected cardinality известна
- для 1 ticker ожидается `18 conclusions`

## Writeback readiness
- canonical write path известен
- downstream target понятен

---

## Pre-Run Decision Modes

### GO
Все critical blocks пройдены.

### GO WITH CAUTION
Critical blocks пройдены, но есть weak/mixed/heuristic warnings.

### NO GO
Есть хотя бы один hard blocker.

---

## Final Pre-Run Hard Blockers
1. нет `snapshot_id / symbol / correlation_id`
2. snapshot не найден
3. нет полного `1m / 5m / 60m ready`
4. `payload_status != ready`
5. critical feature blocks broken
6. strategy registry invalid
7. writeback path unknown

---

## Final Pre-Run Soft Warnings
1. payload ready, but evidence weak
2. heuristic layers dominate interpretation
3. single ticker success only
4. downstream historically drift-prone
5. expected output likely weak/mixed

---

# 2. Final Pre-Write Baseline

## Execution complete
- correct `snapshot_id`
- correct `symbol`
- covered `1m / 5m / 60m`
- covered all 6 strategies

## Cardinality complete
- expected cardinality known
- actual cardinality matches
- for 1 ticker = `18 conclusions`

## Strategy identity canonical
- `strategy_id` exists
- `strategy_name` exists
- registry mapping valid
- no narrative / legacy drift

## Semantic integrity
- `signal` matches `conclusion`
- `status` matches real execution state
- `result_code` matches real condition
- partial not masked as ready
- placeholder not presented as analytical signal

## Output schema complete
- required fields complete
- valid `analysis_id`
- valid `snapshot_id`
- valid `source_window`
- valid `frame`
- write-compatible payload shape

## Canonical write path
- approved endpoint
- canonical destination layer
- downstream target known

---

## Pre-Write Decision Modes

### WRITE
Hard blockers absent.

### WRITE WITH CAUTION
Hard blockers absent, but weak/heuristic-heavy output requires caution.

### NO WRITE
At least one hard blocker present.

---

## Final Pre-Write Hard Blockers
1. incomplete execution
2. cardinality mismatch
3. broken strategy identity
4. semantic mismatch
5. schema incomplete
6. non-canonical write path

---

## Final Pre-Write Soft Warnings
1. mostly weak conclusions
2. heuristic-heavy output
3. over-summary tendency
4. suspiciously uniform signal distribution

---

# 3. Short Status Templates

## Ready
`Ben_Kim ready for execution.`

## In progress
`Ben_Kim execution in progress.`

## Complete
`Ben_Kim execution complete.`

## Go with caution
`Ben_Kim execution allowed with caution.`

## Blocked
`Ben_Kim execution blocked.`

## Partial
`Ben_Kim partial state detected.`

## Downstream caution
`Ben_Kim downstream caution.`

## Batch summary
`Batch summary: input=X | usable=Y | partial=Z | skip=K | analyzed=Y | writeback=ok/partial/error.`

---

# 4. Blocker Templates

## General format
`Blocker: [type] | Layer: [layer] | Impact: [impact] | Required action: [action]`

## Snapshot not found
`Blocker: snapshot not found | Layer: discovery | Impact: execution cannot start | Required action: provide valid snapshot_id or restore snapshot availability`

## Incomplete readiness
`Blocker: incomplete readiness | Layer: payload/readiness | Impact: full 3TF analysis cannot start | Required action: make 1m / 5m / 60m all ready`

## Payload partial
`Blocker: payload partial | Layer: payload | Impact: analysis cannot be considered full production-quality | Required action: complete missing or semantically broken feature blocks`

## Strategy registry mismatch
`Blocker: strategy registry mismatch | Layer: strategy identity | Impact: canonical strategy execution cannot proceed safely | Required action: restore valid strategy_id / strategy_name mapping`

## Writeback unavailable
`Blocker: writeback unavailable | Layer: analysis write | Impact: result can be built but cannot be completed as canonical execution | Required action: restore canonical write path`

## Cardinality mismatch
`Blocker: cardinality mismatch | Layer: execution/output | Impact: analysis result incomplete | Required action: restore missing strategy/frame combinations before writeback`

## Semantic mismatch
`Blocker: semantic mismatch | Layer: output semantics | Impact: result is not safe to store as canonical analytical layer | Required action: align signal, conclusion, status and result_code before writeback`

## Downstream source drift
`Blocker: downstream source drift | Layer: downstream handoff | Impact: downstream may read non-canonical layer | Required action: force downstream to read collector.analysis_results as canonical source`

---

# 5. Approval-Ready Summaries

## Step complete / approve next
`Шаг завершён. Главный вывод: [краткий вывод]. Следующий шаг: [следующий шаг]. Если утверждаешь — иду дальше.`

## Phase checkpoint
`Фаза в рабочем состоянии. Завершено: [список]. Осталось: [список]. Готов перейти к следующему этапу.`

## Execution ready summary
`Snapshot usable. Payload ready. Strategy registry valid. Execution path ready. Можно запускать analysis.`

## Execution complete summary
`Analysis complete. Expected cardinality matched. Canonical writeback confirmed. Downstream can read canonical layer.`

## Blocked summary
`Execution blocked. Причина: [blocker]. Влияние: [impact]. Требуется: [required action].`

## Caution summary
`Execution possible with caution. Hard blockers absent, but evidence is weak/mixed and conclusions require guarded interpretation.`

## Downstream summary
`Canonical Ben_Kim layer ready. Downstream must read collector.analysis_results and not derived summary as source.`

---

# 6. Operational use

Этот документ является daily-use baseline для:
- pre-run decision;
- pre-write decision;
- short reporting;
- blocker escalation;
- approval loop.
