# Ben_Kim Signature Write Flow

## Status
Step 5 of 10.

## Purpose
Define how `Ben_Kim` should produce a signed analysis object under the centralized signature model.

This document fixes the write flow between:
- Ben_Kim analysis object
- visible signature fields
- central signature ledger registration

---

## Flow overview
The Ben_Kim signing flow should work as follows:

1. Ben_Kim prepares the analysis object
2. Ben_Kim includes or requests a visible short `signature_code`
3. The system binds the object to a strong `signature_id`
4. The signed object is written through the controlled path
5. Jack-side central ledger stores the registration record
6. The object and ledger can later be cross-verified

---

## Minimum signed Ben_Kim object
A signed Ben_Kim analysis object should contain at least:
- `producer = Ben_Kim`
- `analysis_id`
- `snapshot_id`
- `symbol`
- `frame`
- `strategy_id`
- `strategy_name`
- `conclusion`
- `signature_code`
- `signature_id`
- object timestamp

---

## Ledger registration content
The central ledger registration for Ben_Kim should include at least:
- `producer = Ben_Kim`
- `object_type = analysis_result` or a Ben_Kim analysis object type
- `object_id = analysis_id`
- `object_scope_json` with at least:
  - `snapshot_id`
  - `symbol`
  - `frame`
  - `strategy_id`
- `signature_code`
- `signature_id`
- optional object hash / verification payload
- status (`registered` initially)

---

## Canonical write rule
A Ben_Kim object should not be treated as properly signed unless:
1. the object carries `signature_code` and `signature_id`
2. the ledger entry exists for that same `signature_id`
3. the producer/object scope matches

---

## Recommended ordering
Recommended write ordering:
1. construct the object payload
2. establish `signature_code`
3. establish `signature_id`
4. compute verification payload or hash if used
5. write the signed object through the centralized path
6. register the central ledger entry in the same signing workflow

If atomic write/registration is possible later, that is preferred.

---

## Verification relation
A Ben_Kim signed object should be verifiable by checking:
- `signature_id`
- `signature_code`
- `producer`
- `analysis_id`
- object scope fields
- verification payload/hash if stored

---

## Scope binding note
For Ben_Kim, the signature should bind to the analysis scope, not just to the producer in general.

That means the signature must be attached to the specific analysis object context, including:
- snapshot
- symbol
- frame
- strategy

---

## Acceptance for Step 5
Step 5 is complete when the Ben_Kim signed write flow is fixed as source-of-truth and defines the relation between the analysis object and the central signature ledger.
