# Dollar_Bill Signature Write Flow

## Status
Step 6 of 10.

## Purpose
Define how `Dollar_Bill` should produce a signed allocation object under the centralized signature model.

This document fixes the write flow between:
- Dollar_Bill allocation object
- visible signature fields
- central signature ledger registration
- optional linkage to upstream analytical context

---

## Flow overview
The Dollar_Bill signing flow should work as follows:

1. Dollar_Bill prepares the allocation object
2. Dollar_Bill includes or requests a visible short `signature_code`
3. The system binds the object to a strong `signature_id`
4. The signed object is written through the controlled path
5. Jack-side central ledger stores the registration record
6. The object and ledger can later be cross-verified

---

## Minimum signed Dollar_Bill object
A signed Dollar_Bill allocation object should contain at least:
- `producer = Dollar_Bill`
- `allocation_id` or equivalent object id
- `snapshot_id` and/or `correlation_id`
- allocation scope (ticker set / universe scope / run scope)
- allocation payload/result
- `signature_code`
- `signature_id`
- object timestamp

---

## Ledger registration content
The central ledger registration for Dollar_Bill should include at least:
- `producer = Dollar_Bill`
- `object_type = capital_allocation` or equivalent allocation object type
- `object_id = allocation_id`
- `object_scope_json` with at least:
  - `snapshot_id` and/or `correlation_id`
  - allocation universe scope
  - run or report scope where applicable
- `signature_code`
- `signature_id`
- optional object hash / verification payload
- status (`registered` initially)

---

## Optional upstream linkage
Dollar_Bill may also need to preserve references to upstream objects used in the decision.

Examples:
- Ben_Kim analysis objects
- Maffi grid objects

These references do not replace Dollar_Bill’s own signature.

They simply preserve lineage context for later verification.

---

## Canonical write rule
A Dollar_Bill object should not be treated as properly signed unless:
1. the object carries `signature_code` and `signature_id`
2. the ledger entry exists for that same `signature_id`
3. the producer/object scope matches

---

## Scope binding note
For Dollar_Bill, the signature should bind to the allocation scope, not just to the agent in general.

That means the signature must be attached to the specific allocation decision context, including:
- run/snapshot scope
- allocation universe
- object identity

---

## Verification relation
A Dollar_Bill signed object should be verifiable by checking:
- `signature_id`
- `signature_code`
- `producer`
- `allocation_id`
- allocation scope fields
- verification payload/hash if stored

---

## Acceptance for Step 6
Step 6 is complete when the Dollar_Bill signed write flow is fixed as source-of-truth and defines the relation between the allocation object and the central signature ledger.
