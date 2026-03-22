# Agent Signature Object Model

## Status
Step 2 of 10.

## Purpose
Define the object model for agent signatures.

This document separates:
- the signed business object
- the central signature ledger entry
- the verification relation between them

Initial scope:
- `Ben_Kim`
- `Dollar_Bill`

---

## 1. Signed business object
A signed business object is the agent-produced object that carries the visible and internal signature fields.

Examples:
- Ben_Kim analysis result object
- Ben_Kim per-ticker analysis package
- Dollar_Bill capital allocation object
- Dollar_Bill allocation decision package

### Minimum fields on signed object
- `producer`
- object identifier (`analysis_id`, `allocation_id`, `report_id`, or equivalent)
- object scope fields (`snapshot_id`, `symbol`, `frame`, run/correlation context where applicable)
- `signature_code`
- `signature_id`
- object payload/content
- object timestamp

---

## 2. Central signature ledger entry
A ledger entry is the canonical verification record maintained under Jack.

### Minimum ledger fields
- `signature_id`
- `signature_code`
- `producer`
- `object_type`
- `object_id`
- `object_scope_json`
- `object_hash` or equivalent verification payload
- `status`
- `created_at_utc`
- `recorded_at_utc`
- optional `notes`

---

## 3. Verification relation
The verification relation exists when:
1. a signed business object contains `signature_code` and `signature_id`
2. a central ledger entry exists with the same `signature_id`
3. the ledger entry matches the expected producer and object scope
4. the ledger entry matches the expected object identity and verification content

If any of these break, verification should fail or become partial/suspect.

---

## 4. Separation of concerns
### Business object
Represents the analytical or allocation result itself.

### Signature ledger
Represents the registration and verification record.

### Verification logic
Compares object vs ledger and decides whether the signature relationship is valid.

These should not be collapsed into one undifferentiated blob.

---

## 5. Suggested object types
Initial expected `object_type` values may include:
- `analysis_result`
- `analysis_package`
- `capital_allocation`
- `allocation_package`

This list can expand later as the pipeline evolves.

---

## 6. Suggested status values
For ledger entries:
- `registered`
- `verified`
- `mismatch`
- `revoked`
- `superseded`

This does not have to be fully implemented in Step 2, but the object model should allow it.

---

## 7. Object scope concept
The signature must bind not only to the producer, but to the object scope.

Scope may include:
- `snapshot_id`
- `correlation_id`
- `symbol`
- `frame`
- `strategy_id`
- reporting period
- other object-specific context

This prevents a signature from being treated as valid outside the object it was meant for.

---

## 8. Verification payload
For strong checking, the ledger should retain either:
- a canonical object hash
- or a deterministic verification payload from which a hash can be reproduced

This helps detect tampering or drift.

---

## Acceptance for Step 2
Step 2 is complete when the signing mechanism is split cleanly into:
- signed business object
- central ledger entry
- verification relation
and this model can guide the later storage/API design.
