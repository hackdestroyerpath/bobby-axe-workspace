# Ben_Kim Analysis Write Response Contract

## Status
Step 7 of 10 for Ben_Kim write-side.

## Purpose
Define the stable response contract for centralized `analysis_result` writeback.

This response must be returned by the future write endpoint after single or batch write attempts.

---

## Endpoint
Planned/implemented endpoint:
- `POST /analysis/write`

---

## Canonical response shape
```json
{
  "status": "ok",
  "accepted_count": 18,
  "stored_count": 18,
  "updated_count": 0,
  "rejected_count": 0,
  "errors": [],
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a"
}
```

---

## Required fields
- `status`
- `accepted_count`
- `stored_count`
- `updated_count`
- `rejected_count`
- `errors`
- `snapshot_id`
- `correlation_id`

---

## `status` semantics
### `ok`
All accepted objects were written successfully.

### `partial`
At least one object was written successfully, but at least one object was rejected.

### `error`
Nothing was stored or updated successfully.

---

## Counter semantics
### `accepted_count`
How many objects the request tried to submit.

### `stored_count`
How many objects were newly inserted.

### `updated_count`
How many objects updated existing rows via the same `analysis_id`.

### `rejected_count`
How many objects failed validation or conflicted.

---

## `errors[]`
Type:
- array of structured error objects

Recommended fields per item:
- `analysis_id`
- `error_code`
- `message`

Example:
```json
{
  "analysis_id": "benkim-snapshot_...-BTCUSDC-rsi_macd_cluster-1m",
  "error_code": "validation_error",
  "message": "missing fields: ['snapshot_id']"
}
```

---

## Example responses
### Full success
```json
{
  "status": "ok",
  "accepted_count": 18,
  "stored_count": 18,
  "updated_count": 0,
  "rejected_count": 0,
  "errors": [],
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a"
}
```

### Partial success
```json
{
  "status": "partial",
  "accepted_count": 18,
  "stored_count": 16,
  "updated_count": 0,
  "rejected_count": 2,
  "errors": [
    {
      "analysis_id": "benkim-snapshot_...-BTCUSDC-rsi_macd_cluster-1m",
      "error_code": "validation_error",
      "message": "snapshot_id is required"
    }
  ],
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a"
}
```

### Full failure
```json
{
  "status": "error",
  "accepted_count": 18,
  "stored_count": 0,
  "updated_count": 0,
  "rejected_count": 18,
  "errors": [
    {
      "analysis_id": null,
      "error_code": "validation_error",
      "message": "mode must be single or batch"
    }
  ],
  "snapshot_id": "snapshot_20260321T235503Z_c0a7cb5a",
  "correlation_id": "snapshot_run_20260321T235503Z_c0a7cb5a"
}
```

---

## Acceptance for Step 7
This contract is complete if it fixes:
- top-level response fields
- stable status semantics
- write counters
- structured errors
- snapshot/correlation traceability

---

## Next planned step
Step 8:
- execute and verify single write against the live endpoint
