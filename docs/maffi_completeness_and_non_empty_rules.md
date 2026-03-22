# Maffi Completeness and Non-Empty Rules

## Status
Step 11 of 20.

## Purpose
Define what the contract firewall should treat as complete, incomplete, partial, or rejected for `Maffi` return objects.

---

## Complete Maffi return
A Maffi return object should be treated as complete only if all of the following are true:
- required scope fields are present
- `frame = 5m`
- required grid decision fields are present
- explanation/conclusion is non-empty
- object belongs to the correct request scope

---

## Required grid decision fields
For the current model, the firewall should expect at least:
- `direction`
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `sl`
- `tp`

If any of these are missing, the object should not be treated as fully complete.

---

## Non-empty rule
The Maffi explanation/conclusion field must not be empty if the contract requires a real explanation for the proposal.

---

## Partial return
A return may be treated as partial when some useful fields are present, but the full required object is not complete enough to be treated as fully accepted.

---

## Rejected return
A return may be treated as rejected when failures are strong enough that the object should not enter the canonical valid proposal layer.

Examples:
- wrong producer/scope
- wrong frame
- major missing required fields
- empty explanation where explanation is mandatory

---

## Acceptance for Step 11
Step 11 is complete when Maffi completeness and non-empty rules are fixed as source-of-truth for later firewall implementation.
