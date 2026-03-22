# Agent Signature Verification Model

## Status
Step 7 of 10.

## Purpose
Define how signed agent objects should be verified against the centralized signature ledger.

Initial scope:
- `Ben_Kim`
- `Dollar_Bill`

---

## Verification goal
Verification should answer whether a signed object is:
- properly registered
- attributable to the claimed producer
- bound to the expected object scope
- consistent with the canonical ledger record

---

## Minimum verification inputs
To verify a signed object, the system should inspect at least:
- `producer`
- object id (`analysis_id`, `allocation_id`, or equivalent)
- object scope fields
- `signature_code`
- `signature_id`
- optional object hash / verification payload

---

## Verification steps
### Step 1. Signature presence
Check that the object contains:
- `signature_code`
- `signature_id`

If missing, verification result should fail.

### Step 2. Ledger existence
Check that a ledger row exists for the same `signature_id`.

If no row exists, verification result should fail.

### Step 3. Producer match
Check that the object `producer` matches the ledger `producer`.

If different, verification result should fail or become mismatch.

### Step 4. Object identity match
Check that the object id matches the ledger `object_id`.

If different, verification result should fail or become mismatch.

### Step 5. Scope match
Check that the object scope matches the expected ledger scope.

If materially different, verification result should fail or become mismatch.

### Step 6. Optional hash/payload check
If verification payload or object hash is stored, compare it.

If mismatch exists, verification should fail or become suspect/mismatch.

---

## Suggested verification outcomes
### `verified`
- signature fields exist
- ledger row exists
- producer matches
- object identity matches
- scope matches
- optional verification payload/hash matches if used

### `missing_signature`
- object does not carry required signature fields

### `unregistered`
- object has signature fields but no corresponding ledger row exists

### `mismatch`
- ledger exists but producer/object/scope/hash do not match

### `revoked`
- ledger entry exists but status is revoked

### `superseded`
- ledger entry exists but object should be treated as replaced by a later registration

---

## Verification rule
The system should not treat a signed object as trustworthy merely because it has a 3-digit visible code.

Trust should come from the full verification path.

---

## Operational interpretation
### If result is `verified`
The object is acceptable as a properly registered signed object.

### If result is `missing_signature` or `unregistered`
The object should not be treated as fully signed.

### If result is `mismatch`
The object and ledger are inconsistent and should be treated as suspect.

### If result is `revoked`
The object should not be treated as active/valid for normal use.

---

## Acceptance for Step 7
Step 7 is complete when the verification logic and outcome model are fixed as source-of-truth for later API/storage implementation.
