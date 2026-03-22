# Contract Firewall Storage Behavior

## Status
Step 15 of 20.

## Purpose
Define how the contract firewall should influence storage behavior after validation.

The firewall should decide not only the validation outcome, but also how the system treats the returned data for canonical storage purposes.

---

## Core rule
Not every returned object should enter the canonical accepted layer.

Storage behavior must depend on the firewall outcome.

---

## Canonical storage behavior by outcome
### `accepted`
The object or return set may enter the canonical accepted layer.

### `partial`
The object or return set may be stored for inspection or diagnostics, but should not be treated as fully accepted canonical output.

### `incomplete`
The object or return set may be stored for inspection/audit, but should not be promoted as a complete canonical result.

### `rejected`
The object or return set should not enter the canonical accepted layer.

It may still be stored in a reject/error/validation record path for audit and debugging.

### `mismatch`
The object or return set should not enter the canonical accepted layer.

It may still be stored in a mismatch/review path for investigation.

---

## Operational implication
The firewall should separate:
- accepted canonical data
- non-accepted but retained validation evidence

This keeps the pipeline auditable without allowing bad objects to silently look accepted.

---

## Acceptance for Step 15
Step 15 is complete when storage behavior is fixed as source-of-truth and clearly states that acceptance into canonical storage depends on firewall outcome.
