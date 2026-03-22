# Contract Firewall Scope Linkage

## Status
Step 3 of 20.

## Purpose
Define how the contract firewall links returned objects to the original request and execution scope.

This document prevents acceptance of objects that look structurally valid but belong to the wrong context.

---

## Core rule
A returned object is not acceptable merely because its schema looks correct.

It must also be linked to the correct execution scope.

---

## Minimum scope linkage fields
The exact set may differ by object family, but the firewall should reason using these scope anchors when applicable:
- `producer`
- `snapshot_id`
- `correlation_id`
- `symbol`
- `frame`
- `strategy_id`
- object identifier (`analysis_id`, `allocation_id`, etc.)

---

## Why linkage matters
Without scope linkage checks, the firewall might wrongly accept:
- an object from the wrong ticker
- an object from the wrong snapshot
- an object from the wrong run
- an object from the wrong producer
- an object from the wrong timeframe or strategy

---

## Linkage rule
For a returned object to pass scope linkage validation, the firewall must be able to show that:
1. the object belongs to the expected producer;
2. the object belongs to the expected request/run context;
3. the object belongs to the expected symbol or allocation scope;
4. the object belongs to the expected object family and object identifier space.

---

## Examples
### Ben_Kim analysis strategy object
Expected linkage may include:
- `producer = Ben_Kim`
- expected `snapshot_id`
- expected `correlation_id`
- expected `symbol`
- expected `frame`
- expected `strategy_id`

### Ben_Kim ticker summary object
Expected linkage may include:
- `producer = Ben_Kim`
- expected `snapshot_id`
- expected `correlation_id`
- expected `symbol`

### Dollar_Bill allocation object
Expected linkage may include:
- `producer = Dollar_Bill`
- expected `snapshot_id` and/or `correlation_id`
- expected allocation universe scope
- expected allocation object id

---

## Firewall outcome rule
If a returned object fails scope linkage, the firewall should not treat it as accepted.

Typical outcomes:
- `mismatch`
- or `rejected`

---

## Acceptance for Step 3
Step 3 is complete when scope linkage is fixed as a source-of-truth rule and clearly states that structurally valid but context-wrong objects must not be accepted.
