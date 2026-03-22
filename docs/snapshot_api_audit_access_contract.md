# Snapshot API Audit & Access Contract

## Status
Step 1 of 11.

## Purpose
This document fixes the audit and access contract for the centralized Snapshot/API layer.

Goal:
- every production read/write access must go through the centralized API layer
- every access must carry client identity
- every access must be logged
- every team participant must be individually accountable
- Jack is the key custodian and issues keys only on request

---

## In-scope participants
The audit/access model currently applies to these team participants:
- `Bobby_Axe`
- `Jack`
- `Ben_Kim`
- `Jusetta`
- `Dollar_Bill`
- `Maffi`
- `BossIgor`

Out of scope for now:
- `Maximus`

---

## Core access rule
All production access to snapshot-scoped data and related writeback paths must go through the centralized API layer.

That includes:
- snapshot lookup
- payload read
- strategy read
- analysis writeback
- stats / usage review
- snapshot save/export flows
- future downstream API reads and writes

No participant should rely on direct shared SQL access as the canonical operating path.

---

## Identity rule
Every participant must have an individual client identity.

Identity must not be shared between participants.

Identity must be represented by at least:
- `client_id`
- `nickname`
- `status`
- issued API key / key hash

---

## Key custody rule
Jack is the key custodian for this layer.

Rules:
- keys are generated and stored under Jack-controlled issuance flow
- keys are given only on request
- keys are not to be reused across participants
- keys may be rotated or disabled if needed
- inactive or revoked identities must not retain active access

---

## Mandatory accounting rule
Every production request must be attributable to one client identity.

Every access event must be loggable and reviewable later.

No silent working path is acceptable for production usage if it bypasses client identity or logging.

---

## Logging rule
Every logged event must preserve at least:
- `client_id`
- `nickname`
- `endpoint`
- request context identifier (`snapshot_id` and/or equivalent)
- selected symbol when relevant
- resolved bundle id when relevant
- request status
- request timestamp

Recommended additional fields for later steps:
- HTTP method
- response code
- latency
- agent role
- action category (`read`, `write`, `stats`, `admin`)

---

## Allowed unauthenticated exception
Only pure liveness/health routes may remain unauthenticated if needed for operations.

Examples:
- `/health`

Any data-bearing or business-bearing route should require client identity.

---

## Team accountability rule
The dashboard and accounting layer should make it possible to see, per participant:
- total requests
- recent requests
- last request time
- endpoint usage
- snapshot usage
- denied requests
- error requests
- successful requests

This is required so leadership can see who accessed what and how often.

---

## Write accountability rule
Any participant that writes data through the centralized path must be individually attributable.

That includes at minimum:
- who wrote
- what endpoint was used
- what snapshot context was targeted
- whether the write succeeded or failed

---

## Read accountability rule
Any participant that reads data through the centralized path must also be individually attributable.

Read activity is part of the audit surface, not just writes.

---

## Contract requirements for later steps
Later implementation steps must guarantee:
1. a canonical client registry for all in-scope participants;
2. one API key per participant;
3. mandatory auth coverage for production routes;
4. complete request logging for all relevant endpoints;
5. dashboard visibility into per-client usage;
6. verification that all in-scope participants are accounted for.

---

## Definition of done for the full audit/access track
This track is complete only if:
1. every in-scope participant has a distinct API identity;
2. all production API access is identity-bound;
3. all production API access is logged;
4. leadership can see per-client usage in dashboard/reporting;
5. no silent production path bypasses accounting.

---

## Step 1 result
Step 1 is complete when the centralized audit/access contract is documented and frozen before client-registry and endpoint-coverage changes begin.
