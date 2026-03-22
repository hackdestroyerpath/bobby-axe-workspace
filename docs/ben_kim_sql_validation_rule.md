# Ben_Kim SQL Validation Rule

## Status
Step 9 of 20.

## Purpose
Define how the contract firewall should validate `Ben_Kim` return completeness at the SQL/storage layer.

This document does not require final SQL implementation yet; it fixes the validation logic that later SQL checks must express.

---

## Validation target
For each expected ticker return set, SQL-level validation should be able to determine:
- how many strategy objects exist
- whether all required frames exist
- whether all required strategies exist in each frame
- whether the ticker summary object exists
- whether required conclusions are non-empty
- whether scope fields are consistent

---

## Expected storage interpretation
At SQL-level, the validator should reason over at least:
- atomic strategy objects
- ticker summary object
- producer/scope fields
- conclusion presence/non-empty state

---

## Required checks
### 1. Total object count
For one ticker, SQL validation should confirm the expected total object count.

Current Ben_Kim expectation:
- `18` atomic strategy objects
- `1` ticker summary object
- total `19`

### 2. Frame coverage
SQL validation should confirm that all required frames are present:
- `1m`
- `5m`
- `60m`

### 3. Strategy coverage inside each frame
SQL validation should confirm that each required frame contains all expected strategies.

### 4. Summary existence
SQL validation should confirm that exactly one required ticker summary object exists.

### 5. Non-empty conclusions
SQL validation should confirm that mandatory conclusions are not empty.

### 6. Scope consistency
SQL validation should confirm consistent:
- `producer`
- `snapshot_id`
- `correlation_id`
- `symbol`
across the expected return set.

---

## Suggested SQL result model
The SQL-level validation logic should be able to emit or derive fields such as:
- `expected_object_count`
- `actual_object_count`
- `required_frames_present`
- `required_strategies_present`
- `summary_present`
- `non_empty_conclusions_ok`
- `scope_consistency_ok`
- final firewall outcome

---

## Suggested final outcomes
Based on the derived checks, SQL-level evaluation should support outcomes such as:
- `accepted`
- `partial`
- `incomplete`
- `rejected`
- `mismatch`

---

## Acceptance for Step 9
Step 9 is complete when the SQL/storage-layer validation logic for Ben_Kim is fixed as source-of-truth, even if the final SQL view/procedure is implemented later.
