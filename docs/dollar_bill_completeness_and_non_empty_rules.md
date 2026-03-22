# Dollar_Bill Completeness and Non-Empty Rules

## Status
Step 13 of 20.

## Purpose
Define what the contract firewall should treat as complete, incomplete, partial, or rejected for `Dollar_Bill` return objects.

---

## Complete Dollar_Bill return
A Dollar_Bill allocation object should be treated as complete only if all of the following are true:
- required scope fields are present
- allocation result content is present
- explanation/conclusion is present when required by contract
- object belongs to the correct request scope

---

## Non-empty rule
If the contract requires an explanation/conclusion, that field must not be empty.

If the allocation result content itself is missing or effectively empty, the object should not be treated as complete.

---

## Partial return
A return may be treated as partial when some useful allocation content exists, but the full required object is not complete enough to be accepted as a valid final allocation object.

---

## Rejected return
A return may be treated as rejected when failures are strong enough that the object should not enter the canonical valid allocation layer.

Examples:
- wrong producer/scope
- missing core allocation content
- empty required explanation

---

## Acceptance for Step 13
Step 13 is complete when Dollar_Bill completeness and non-empty rules are fixed as source-of-truth for later firewall implementation.
