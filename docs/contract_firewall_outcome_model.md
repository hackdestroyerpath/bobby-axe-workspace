# Contract Firewall Outcome Model

## Status
Step 14 of 20.

## Purpose
Define the canonical validation outcomes for the contract firewall.

These outcomes should be used consistently when deciding whether an agent return set or object can be accepted into canonical storage.

---

## Canonical outcomes
### `accepted`
The return satisfies all mandatory contract rules for the evaluated scope.

Typical meaning:
- required object set is present
- required fields are present
- required non-empty values are present
- scope is consistent
- expected completeness is satisfied

### `partial`
Some useful content exists, but the full contract is not satisfied.

Typical meaning:
- some valid objects are present
- but mandatory completeness is not fully achieved
- the result may be inspectable but should not be treated as fully complete

### `incomplete`
The return set is missing mandatory objects or mandatory structural coverage.

Typical meaning:
- expected object count is too low
- one or more required object families are missing
- one or more required frames/strategies are missing

### `rejected`
The return fails important contract rules strongly enough that it should not enter the canonical accepted layer.

Typical meaning:
- core required fields are missing
- mandatory explanations are empty
- critical decision content is absent
- structural validity is too weak

### `mismatch`
The return exists, but belongs to the wrong scope or wrong identity context.

Typical meaning:
- wrong producer
- wrong snapshot
- wrong symbol
- wrong run/correlation context
- wrong object linkage

---

## Interpretation rule
The firewall should not collapse all failures into a generic error bucket.

The outcome model should preserve enough meaning to tell the difference between:
- an almost complete return
- a structurally incomplete return
- a context-wrong return
- a fully unusable return

---

## Acceptance for Step 14
Step 14 is complete when the contract firewall has a single canonical outcome vocabulary that later SQL/runtime validation can reuse consistently.
