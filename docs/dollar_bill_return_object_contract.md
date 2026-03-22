# Dollar_Bill Return Object Contract

## Status
Step 12 of 20.

## Purpose
Define the expected return object for `Dollar_Bill` under the contract firewall.

This contract describes the canonical object family that Dollar_Bill should return for allocation results.

---

## Object type
Suggested conceptual object type:
- `capital_allocation`

---

## One object means exactly
One Dollar_Bill return object should correspond to exactly:
- one allocation object identity
- one allocation scope
- one run/snapshot context

Depending on the later packaging model, the allocation object may cover one ticker allocation record or a coherent allocation set. The firewall should still know which scope is being validated.

---

## Minimum mandatory fields
A valid Dollar_Bill allocation object should contain at least:
- `producer = Dollar_Bill`
- `snapshot_id` and/or `correlation_id`
- object identifier (`allocation_id` or equivalent)
- allocation scope fields
- allocation result content
- explanation/conclusion field where required

---

## Contract rule
The firewall should treat this object as invalid if it:
- lacks required scope fields
- lacks allocation result content
- lacks required explanation where explanation is mandatory
- belongs to the wrong request scope

---

## Acceptance for Step 12
Step 12 is complete when the expected Dollar_Bill return object is fixed as source-of-truth for later completeness and non-empty validation.
