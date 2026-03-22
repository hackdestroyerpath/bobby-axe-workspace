# Maffi Return Object Contract

## Status
Step 10 of 20.

## Purpose
Define the expected return object for `Maffi` under the contract firewall.

This contract describes the canonical object family that Maffi should return for a ticker-level grid proposal.

---

## Object type
Suggested conceptual object type:
- `grid_proposal`

---

## One object means exactly
One Maffi return object should correspond to exactly:
- one `symbol`
- one `snapshot_id` and/or `correlation_id`
- one grid proposal decision for the expected ticker scope

For the current pipeline direction, the effective decision focus is the `5m` grid proposal layer.

---

## Minimum mandatory fields
A valid Maffi grid proposal object should contain at least:
- `producer = Maffi`
- `snapshot_id`
- `correlation_id`
- `symbol`
- `frame = 5m`
- object identifier (`grid_id` or equivalent)
- decision fields such as:
  - `direction`
  - `grid_upper_price`
  - `grid_lower_price`
  - `grid_count`
  - `sl`
  - `tp`
- `conclusion` or explanation field

---

## Contract rule
The firewall should treat this object as invalid if it:
- lacks required scope fields
- lacks required decision fields
- uses the wrong effective frame for Maffi output
- has an empty explanation/conclusion where explanation is required
- belongs to the wrong request scope

---

## Acceptance for Step 10
Step 10 is complete when the expected Maffi return object is fixed as source-of-truth for later completeness and non-empty validation.
