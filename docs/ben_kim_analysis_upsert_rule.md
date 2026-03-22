# Ben_Kim Analysis Upsert Rule

## Status
Step 3 of 10 for Ben_Kim write-side.

## Purpose
Define the canonical business key and idempotent write semantics for centralized `analysis_result` storage.

This rule is required before the physical table and write endpoint are implemented.

---

## Main requirement
`analysis_result` writeback must be idempotent.

Meaning:
- repeated safe writes of the same business result must not create duplicates
- the same logical result must converge to one canonical stored row

---

## Canonical key model
### Primary business key
Canonical business key:
- `analysis_id`

### Safety uniqueness key
Additional logical uniqueness guard:
- `snapshot_id`
- `symbol`
- `strategy`
- `frame`

This means the canonical row identity is driven by `analysis_id`, while a secondary uniqueness constraint protects the most common logical duplicates inside one snapshot.

---

## Why this choice
### Why `analysis_id` is primary
It gives Ben_Kim a stable idempotency token and keeps API behavior explicit.

### Why `snapshot_id + symbol + strategy + frame` is also important
Within one snapshot, Ben_Kim should normally produce one canonical result per:
- symbol
- strategy
- frame

So this tuple is the most useful safety duplicate check.

---

## Recommended `analysis_id` shape
Example pattern:

```text
benkim-<snapshot_id>-<symbol>-<strategy>-<frame>
```

Example:

```text
benkim-snapshot_20260321T235503Z_c0a7cb5a-BTCUSDC-rsi_macd_cluster-1m
```

This makes the key:
- deterministic
- snapshot-scoped
- human-readable

---

## Write behavior on repeated request
### Canonical behavior
Use:
- **idempotent upsert overwrite**

Meaning:
- if the same `analysis_id` comes again -> update the existing row
- if the same `(snapshot_id, symbol, strategy, frame)` comes with a different `analysis_id` -> reject as conflict or normalize to existing row, depending on implementation policy

For the first implementation, the recommended behavior is:
1. same `analysis_id` -> overwrite existing row
2. different `analysis_id` but same `(snapshot_id, symbol, strategy, frame)` -> reject with stable conflict error

This preserves clean semantics and prevents silent logical duplication.

---

## Canonical conflict rule
### Allowed overwrite
Allowed when:
- same `analysis_id`

Result:
- existing row is updated in place
- response counts as `updated`

### Conflict
Conflict when:
- different `analysis_id`
- same `snapshot_id + symbol + strategy + frame`

Result:
- row is rejected
- response should include stable conflict error

Recommended error code:
- `analysis_result_conflict`

---

## Response semantics for write endpoint
The future write endpoint should distinguish:
- `stored` — new row inserted
- `updated` — existing row updated via same `analysis_id`
- `rejected` — conflict or validation failure

---

## Downstream guarantee
Downstream consumers (`Jusetta`, `Maffi`) should be able to assume:
- at most one canonical `analysis_result` per snapshot/symbol/strategy/frame
- no duplicate rows for the same business result
- overwrite path is deterministic

---

## Batch behavior
For batch writes:
- each object is evaluated independently
- whole batch should not be rejected only because one object conflicts
- response should report per-batch counters:
  - `accepted_count`
  - `stored_count`
  - `updated_count`
  - `rejected_count`

Optional detailed errors array should reference:
- `analysis_id`
- `snapshot_id`
- `symbol`
- `strategy`
- `frame`
- `error_code`

---

## Required fields for uniqueness logic
To enforce this rule, the write layer must reliably receive:
- `analysis_id`
- `snapshot_id`
- `symbol`
- `strategy`
- `frame`

If `snapshot_id` is missing, the endpoint should reject the object or resolve it from the top-level request envelope before validation.

---

## Acceptance for Step 3
This rule is complete if it fixes:
- canonical business key
- duplicate semantics
- overwrite semantics
- conflict semantics
- batch-level interpretation

---

## Next planned step
Step 4:
- create the physical `collector.analysis_results` storage table with matching constraints
