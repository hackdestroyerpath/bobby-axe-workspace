# Ben_Kim Mass Analysis Baseline

## Status
Final baseline.

## Purpose
Канонический документ по массовому execution-режиму `Ben_Kim`.

Документ фиксирует:
- pipeline single ticker -> batch -> universe;
- usable / partial / skip rules;
- batch segmentation;
- batch accounting;
- итоговый operational summary.

---

# 1. Execution modes

## Single ticker mode
Атомарная единица execution.

### Sequence
1. get `snapshot_id`
2. pass pre-run gate
3. read payload for one `symbol`
4. read strategy registry
5. execute `6 strategies × 3 frames`
6. build `18 conclusions`
7. pass pre-write gate
8. write result

### Core rule
Success in single ticker mode does not prove universe readiness.

---

## Batch mode
Execution for several tickers in one run.

### Sequence
1. take ticker list
2. check readiness for each ticker
3. split into `usable / partial / skip`
4. run analysis only for `usable`
5. build `18 conclusions` per usable ticker
6. write results per ticker or batch
7. produce batch summary

### Core rule
Batch success must never hide per-symbol state.

---

## Full usable universe mode
Execution for the full current universe, but only for the usable subset.

### Sequence
1. read universe list
2. build readiness map per symbol
3. segment into `usable / partial / skip`
4. analyze only usable subset
5. write canonical results
6. produce universe summary

### Core rule
Universe for analysis = usable subset, not every symbol in the raw list.

---

# 2. Classification rules

## Usable
Ticker is `usable` when:
- `snapshot_id` exists;
- ticker belongs to execution context;
- `1m = ready`;
- `5m = ready`;
- `60m = ready`;
- `payload_status = ready`;
- `result_code = ok`;
- core feature blocks usable;
- strategy registry consistent.

### Practical meaning
- full analysis cycle allowed;
- `18 conclusions` expected;
- writeback allowed after pre-write gate.

---

## Partial
Ticker is `partial` when:
- snapshot/payload partially usable;
- some layers work;
- but full production-quality cycle is not available.

### Practical meaning
- diagnostic / partial review possible;
- not a full production-quality ticker result;
- must not be silently elevated into usable.

---

## Skip
Ticker is `skip` when:
- readiness gate fails;
- critical execution layer missing;
- payload not ready;
- identity broken;
- no meaningful start allowed.

### Practical meaning
- production-analysis not started;
- no pseudo-conclusions;
- no writeback;
- ticker counted as skipped in summary.

---

# 3. Batch segmentation

Batch must always be segmented into:
1. `usable`
2. `partial`
3. `skip`

### Rule
Batch is not just a list of symbols.
It is a classified execution set.

---

# 4. Batch accounting

After batch run, Ben_Kim must report:
- `input_ticker_count`
- `usable_ticker_count`
- `partial_ticker_count`
- `skipped_ticker_count`
- `analyzed_ticker_count`
- `written_result_count`
- `expected_conclusion_count`
- `actual_conclusion_count`

---

# 5. Expected count logic

## For one usable ticker
- `6 strategies × 3 frames = 18 conclusions`

## For batch
- `usable_ticker_count × 18 = expected_conclusion_count`

---

# 6. Batch summary requirements

Every mass-run summary must include:

## Input block
- how many symbols came in

## Segmentation block
- how many usable
- how many partial
- how many skipped

## Execution block
- how many analyzed
- expected conclusions
- actual conclusions

## Writeback block
- write status
- partial write issues
- rejects/conflicts if any

## Warning block
- weak-heavy batch
- heuristic-heavy batch
- payload anomalies
- downstream-risk notes

---

# 7. Forbidden shortcuts

## Forbidden 1
Calling batch complete without usable/partial/skip breakdown.

## Forbidden 2
Treating all input tickers as analyzed tickers.

## Forbidden 3
Hiding mismatch between expected and actual conclusions.

## Forbidden 4
Treating partial tickers as fully analyzed.

## Forbidden 5
Using one successful ticker as proof that universe execution is production-ready.

---

# 8. Core scaling rules

## Rule M1
Single ticker execution is the atomic unit.

## Rule M2
Batch = controlled set of atomic ticker executions.

## Rule M3
Universe execution = batch over usable subset.

## Rule M4
Skip must remain visible.

## Rule M5
Batch success must always include symbol-level accounting.

---

# 9. Operational summary format

## Short version
`input=X | usable=Y | partial=Z | skip=K | analyzed=Y | expected_conclusions=Y*18 | actual_conclusions=N | writeback=ok/partial/error`

## Extended version
- usable symbols list
- partial symbols list
- skipped symbols list
- grouped reasons for partial/skip
- write statistics
- warnings

---

# 10. Operational use

Этот документ является baseline для:
- batch execution;
- universe execution;
- symbol classification;
- honest batch accounting;
- post-run reporting.
