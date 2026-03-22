# Contract Firewall Audit Trail

## Status
Step 16 of 20.

## Purpose
Define the audit trail requirements for contract firewall validation decisions.

The firewall should not only decide outcomes, but also preserve a trace explaining what was expected, what arrived, and why the decision was made.

---

## Core rule
Every meaningful validation decision should be reviewable later.

This means the system should preserve an audit trail for:
- accepted returns
- partial returns
- incomplete returns
- rejected returns
- mismatched returns

---

## Minimum audit trail fields
A validation audit record should preserve at least:
- `producer`
- request context (`snapshot_id`, `correlation_id`, `symbol`, or equivalent scope)
- expected object family / expected object count where applicable
- actual object count where applicable
- final firewall outcome
- reason notes or validation findings
- validation timestamp

---

## Why this matters
Without an audit trail, the team may know that an object was rejected but not know:
- why it was rejected
- what was missing
- whether the error was scope mismatch vs incompleteness vs empty fields
- how to fix the return on the agent side

---

## Acceptance for Step 16
Step 16 is complete when the validation layer is required to preserve an audit explanation of what was expected, what was received, and why the firewall outcome was chosen.
