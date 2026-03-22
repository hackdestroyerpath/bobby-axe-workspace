# Snapshot API Audit Readiness Report

## Status
Step 10 of 11.

## Purpose
Summarize the readiness state of the centralized Snapshot/API audit and accounting model.

This document records what is already closed, what the operating baseline is, and what the team should treat as the canonical working model going forward.

---

## Readiness summary
The centralized Snapshot/API layer is now materially ready for identity-bound, auditable access.

Closed areas:
- audit/access contract exists
- canonical client registry exists
- physical client provisioning exists for the current in-scope team
- mandatory auth is active on production data routes
- access logging is active on accountable routes
- dashboard/accounting views now include by-user, by-endpoint, by-status, and recent request views
- per-client identity separation has been verified on live requests

---

## In-scope identities currently covered
- `bobby_axe`
- `jack`
- `ben_kim`
- `jusetta`
- `dollar_bill`
- `maffi`
- `boss_igor`

Out of scope for now:
- `maximus`

---

## Canonical working model
### Access model
All production snapshot/data access should go through the centralized API layer.

### Identity model
Every participant uses a distinct API client identity and key.

### Key custody model
Jack is the key custodian and issues keys only on request.

### Accounting model
Every production request to accountable routes should be attributable to a client identity and visible in audit/accounting views.

---

## Auth baseline
### Unauthenticated allowed
- `/health`
- `/` (UI shell only)

### Auth required
- `/lookup`
- `/payload`
- `/strategies`
- `/stats`
- `/lookup/download`
- `/lookup/save`
- `/analysis/write`

---

## Logging baseline
Accountable routes are expected to log at least:
- `client_id`
- `nickname`
- `endpoint`
- `snapshot_id` when applicable
- `selected_symbol` when applicable
- `resolved_bundle_id` when applicable
- `request_status`
- request time

The current implementation materially satisfies this baseline for the central Snapshot/API surface.

---

## Dashboard/accounting baseline
Current accounting views should allow leadership or operations to inspect:
- usage by user
- usage by endpoint
- usage by status
- recent requests
- snapshot summary

This is sufficient for the current stage to track who is using the system and how.

---

## Remaining caveats
### 1. UI shell is open but non-data-bearing
The UI shell route itself is open without key; data access inside the UI still requires API key.

### 2. Maximus is not included yet
If Maximus joins later, a separate canonical identity and key must be created.

### 3. Future routes must follow the same policy
Any new route added later must define auth/logging/accounting before release.

---

## Operational guidance for the team
Team participants should assume:
1. do not use shared SQL as the canonical operating path;
2. do not borrow another participant’s key;
3. use only your assigned client identity;
4. assume your requests are counted and reviewable;
5. request a new key from Jack if access is needed.

---

## Readiness conclusion
The Snapshot/API layer is ready enough to operate as a team-audited centralized access path for the current in-scope participants.

This readiness does not mean the system is feature-complete forever; it means the current audit/accounting baseline is sufficiently established for controlled production team usage.

---

## Acceptance for Step 10
Step 10 is complete when the readiness state of the audit/accounting contour is fixed in a concise source-of-truth report for operations and leadership.
