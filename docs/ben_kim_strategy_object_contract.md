# Ben_Kim Strategy Object Contract

## Status
Step 5 of 20.

## Purpose
Define the atomic strategy-level return object for `Ben_Kim`.

This contract describes one object representing:
- one ticker
- one timeframe
- one strategy

The contract firewall should validate these atomic objects before they are accepted into the canonical layer.

---

## Object type
Suggested conceptual object type:
- `analysis_strategy_result`

---

## One object means exactly
One `Ben_Kim` strategy object should correspond to exactly:
- one `symbol`
- one `frame`
- one `strategy_id`

It should not bundle multiple strategies into one atomic object.

---

## Minimum mandatory fields
A valid Ben_Kim strategy object should contain at least:
- `producer = Ben_Kim`
- `snapshot_id`
- `correlation_id`
- `symbol`
- `frame`
- `strategy_id`
- `strategy_name`
- `conclusion`
- object identifier (`analysis_id` or equivalent)

---

## Field interpretation
### `symbol`
The ticker the conclusion belongs to.

### `frame`
One timeframe such as:
- `1m`
- `5m`
- `60m`

### `strategy_id`
The canonical strategy identity.

### `strategy_name`
The canonical human-readable strategy label.

### `conclusion`
The actual strategy-level conclusion/comment.

This field is mandatory and must not be empty.

### `analysis_id`
The object identity for this atomic analysis result.

---

## Contract rule
The firewall should treat this object as invalid if it:
- mixes multiple strategies in one atomic object
- lacks required scope fields
- lacks canonical strategy identity
- has an empty conclusion
- belongs to the wrong request scope

---

## Acceptance for Step 5
Step 5 is complete when the atomic Ben_Kim strategy object is fixed as source-of-truth for later completeness and SQL-level validation.
