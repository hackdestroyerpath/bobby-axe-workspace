# Allowed vs Forbidden Data Paths

## Status
Step 8 of 12.

## Purpose
Fix the practical path discipline for how team participants are expected to access or write data in the centralized Snapshot/API architecture.

This document complements the database access policy by defining what is operationally allowed and what should be treated as a model violation.

---

## Allowed data paths
### 1. Controlled API read paths
Allowed examples:
- `GET /lookup`
- `GET /payload`
- `GET /strategies`
- `GET /stats`
- `GET /lookup/download`
- `GET /lookup/save`

Reason:
- identity-bound
- auditable
- consistent with centralized access model

### 2. Controlled API write paths
Allowed examples:
- `POST /analysis/write`
- future centralized downstream write endpoints following the same model

Reason:
- identity-bound
- validated
- auditable
- consistent with centralized write discipline

### 3. Jack operational storage access
Allowed when performed by Jack for operational reasons such as:
- storage maintenance
- schema migration
- validation
- recoverability
- diagnostics
- service repair

### 4. Dashboard/operator usage through UI + API key
Allowed for leadership/operator visibility and controlled inspection.

---

## Forbidden paths as normal team workflow
### 1. Direct arbitrary SQL by non-Jack participants
Forbidden as baseline workflow.

### 2. Direct writes into production tables by non-Jack participants
Forbidden as baseline workflow.

### 3. Ad-hoc shadow JSON/files as production exchange layer
Forbidden if they bypass the canonical service path.

### 4. Borrowed key usage
Forbidden for normal production work.

### 5. Unlogged manual production data access
Forbidden as a normal operating model.

### 6. Any route that bypasses identity-bound accounting
Forbidden for production usage if it becomes a working path.

---

## Exception handling
Exceptions may exist, but they are not the baseline.

A valid exception should be:
- explicit
- justified
- limited in scope
- not silently converted into normal operating practice

---

## How to interpret violations
The following should be treated as policy violations or at least discipline breaks:
- non-Jack agents reading production data directly from DB as their default mode
- non-Jack agents writing directly into production storage tables
- production work happening through side channels that are not reflected in audit/accounting
- one participant operating under another participant’s identity

---

## Canonical expectation by role
### Jack
- may access DB directly for infrastructure/storage reasons
- maintains the controlled data platform

### Bobby_Axe
- should use centralized visibility/control paths
- not direct DB as baseline

### Ben_Kim
- should read via payload/strategy/API paths
- should write via analysis writeback path

### Maffi
- should use centralized downstream read/write paths

### Dollar_Bill
- should use centralized downstream read/write paths

### Jusetta
- should use centralized downstream read/write paths

### BossIgor
- should use dashboard/operator API paths

---

## Acceptance for Step 8
Step 8 is complete when allowed and forbidden data paths are fixed in a practical source-of-truth document that the team can use as an operational rulebook.
