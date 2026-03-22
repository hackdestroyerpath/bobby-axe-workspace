# Database Access Policy

## Status
Step 7 of 12.

## Purpose
Fix the database access policy for the Bobby Axe team working on the centralized market-data and Snapshot/API stack.

This document defines who is allowed to treat the database as an operational working layer and who must instead use the controlled service/API layer.

---

## Core rule
The database is a controlled storage and system layer.

It is not a shared playground for arbitrary direct production queries by all participants.

For the team operating model:
- Jack is the infrastructure and storage custodian
- other participants should use controlled service/API paths for production work
- random direct database access is not the canonical working model

---

## Custody rule
Jack owns the operational database access discipline for this stack.

Responsibilities include:
- ingestion/storage correctness
- schema control
- access discipline
- recoverability
- preventing uncontrolled production query patterns

---

## Allowed operational model
### Jack
Jack may access the database directly when needed for:
- ingestion operations
- storage maintenance
- schema changes
- quality checks
- recovery procedures
- service debugging
- controlled audits and validation

### Other participants
Other participants should use:
- centralized API endpoints
- controlled service interfaces
- approved downstream read/write paths

This includes:
- `Ben_Kim`
- `Jusetta`
- `Maffi`
- `Dollar_Bill`
- `Bobby_Axe`
- `BossIgor` for operator/dashboard usage

---

## Forbidden working model
The following should not be treated as normal production operation for non-Jack participants:
- arbitrary direct SQL reads as the default workflow
- arbitrary direct SQL writes
- bypassing the API/service layer for routine work
- temporary shadow data paths that are not identity-bound or logged
- uncontrolled manual querying against production data stores

---

## Why this policy exists
This policy exists to ensure:
- deterministic access paths
- auditability
- clear ownership
- reduced accidental schema misuse
- reduced hidden side effects
- team-wide consistency

---

## Canonical production paths
For normal team operation, the expected production path is:
1. Jack maintains storage and service layer
2. participants access data through controlled API/service routes
3. requests remain identity-bound and auditable
4. downstream results are written back through controlled paths

---

## Exceptions
Any exception to this policy should be explicit and intentional.

If a non-Jack participant requires direct database access for a justified reason, that should be treated as an exception, not the baseline model.

Exceptions should not silently become the default operating pattern.

---

## Alignment with current stack
This policy is aligned with the current architecture direction:
- snapshot lookup is centralized
- payload reads are centralized
- strategy reads are centralized
- analysis writes are centralized
- access logging/accounting is centralized

---

## Acceptance for Step 7
Step 7 is complete when the database access discipline is fixed as source-of-truth and clearly states that the production working model is controlled access via Jack/API rather than uncontrolled direct DB usage by all participants.
