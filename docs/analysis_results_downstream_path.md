# Analysis Results Downstream Path

## Status
Step 10 of 10 for Ben_Kim write-side.

## Purpose
Fix the canonical downstream read path for `analysis_result` storage.

This document defines what layer downstream consumers must read after Ben_Kim writes analysis-only results.

---

## Canonical storage layer
Logical layer:
- `analysis_result`
- Ben_Kim analysis-only result layer

Physical table:
- `collector.analysis_results`

This is the canonical storage path for downstream consumers.

---

## Who must read this layer
### `Jusetta`
Must read:
- `collector.analysis_results`

Use case:
- analysis preview
- report assembly
- textual summary / tables / PDF preparation

### `Maffi`
Must read:
- `collector.analysis_results`

Use case:
- signal summarization
- grid generation input

---

## What they should not read instead
Downstream consumers should **not** treat the following as the canonical Ben_Kim output layer:
- raw feature tables directly
- mock result tables
- temporary JSON scratch files
- manually copied payload blobs

These may exist for diagnostics, but they are not the canonical analysis-only output layer.

---

## Canonical read rule
Downstream should read rows from:
- `collector.analysis_results`

Using at minimum these selectors:
- `snapshot_id`
- `symbol`
- `strategy`
- `frame`

And trust the row identity based on:
- `analysis_id`
- uniqueness guard on `(snapshot_id, symbol, strategy, frame)`

---

## Expected row semantics
Each row in `collector.analysis_results` represents one canonical Ben_Kim conclusion for:
- one snapshot
- one symbol
- one strategy
- one frame

Typical granularity:
- `1 ticker × 6 strategies × 3 frames = 18 rows`

---

## Minimal read example
```sql
SELECT
    analysis_id,
    snapshot_id,
    correlation_id,
    producer,
    symbol,
    strategy,
    frame,
    signal,
    conclusion,
    confidence,
    observed_at,
    source_window_from,
    source_window_to,
    status,
    result_code,
    details_json,
    created_at_utc,
    updated_at_utc
FROM collector.analysis_results
WHERE snapshot_id = 'snapshot_20260321T235503Z_c0a7cb5a'
  AND symbol = 'BTCUSDC'
ORDER BY strategy, frame;
```

---

## Read expectations for downstream
### For `Jusetta`
- use this layer as canonical analysis input
- do not reconstruct Ben_Kim output from raw features if analysis rows already exist

### For `Maffi`
- use this layer as canonical signal source
- do not derive production grid input from mock or preview-only artifacts

---

## Acceptance for Step 10
This downstream path is complete if it fixes:
- one canonical physical table
- one canonical logical layer
- explicit downstream readers
- explicit prohibition on mock-layer substitution

---

## Result
After Step 10, the Ben_Kim write-side flow is complete enough that:
1. Ben_Kim can read payload via centralized API
2. Ben_Kim can write analysis_result via centralized API
3. downstream can read the canonical stored layer from `collector.analysis_results`
