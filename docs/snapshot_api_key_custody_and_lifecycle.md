# Snapshot API Key Custody & Lifecycle

## Status
Step 8 of 11.

## Purpose
Fix the key custody and lifecycle rules for Snapshot/API client identities.

This document defines:
- who issues keys
- who stores keys
- how keys are requested
- what lifecycle states mean
- how active/disabled/revoked status should be interpreted

---

## Key custodian
Jack is the key custodian for the centralized Snapshot/API layer.

Responsibilities:
- issue keys for canonical client identities
- keep issuance flow under Jack control
- provide keys only on request
- avoid shared keys between participants
- rotate or revoke keys when needed
- preserve auditability of which client identity owns which key

---

## Issuance rule
A key may be issued only for a canonical client identity from the approved client registry.

A participant must not receive:
- an ad-hoc unnamed key
- a borrowed key from another participant
- a shared team key for production work

---

## Current canonical participants
The current in-scope client identities are:
- `bobby_axe`
- `jack`
- `ben_kim`
- `jusetta`
- `dollar_bill`
- `maffi`
- `boss_igor`

---

## Current status interpretation
### `active`
- identity exists
- key is valid
- access is permitted according to endpoint auth rules
- requests should appear in audit/accounting views

### `planned`
- identity is part of the canonical registry
- key issuance or verification is not complete yet
- should not be used as a working production client until activated

### `disabled`
- key/client identity exists
- access must be blocked
- identity remains visible for audit/history purposes

### `revoked`
- key/client identity is no longer allowed for use
- should not be silently reactivated
- replacement should happen through explicit reissuance decision

---

## Operational issuance policy
### 1. By request only
Keys are distributed only when requested and approved.

### 2. One key per client identity
Each participant gets a distinct key.

### 3. No shared operator key
Production usage should not hide behind one umbrella key.

### 4. Rotation
If a key is suspected to be exposed or no longer appropriate:
- issue a replacement key
- disable or revoke the old key
- preserve audit continuity through client identity

### 5. Storage
Jack keeps issuance control and should avoid leaking plaintext keys into broad channels.

---

## Current implementation state
As of this step, the physical registry already contains active identities for:
- `bobby_axe`
- `jack`
- `ben_kim`
- `jusetta`
- `dollar_bill`
- `maffi`
- `boss_igor`

Meaning:
- the full current team set is provisioned in physical client storage
- future work should focus on enforcement, reporting, verification, and lifecycle handling

---

## What leadership should be able to see
Leadership should be able to inspect, directly or via dashboard/reporting:
- which client identities exist
- which are active
- request counts per identity
- recent usage per identity
- denied/error activity per identity

Plaintext keys do not need to be shown in dashboard views.

---

## Acceptance for Step 8
Step 8 is complete when key custody and lifecycle rules are fixed as source-of-truth and aligned with the team-wide client registry and active provisioning model.
