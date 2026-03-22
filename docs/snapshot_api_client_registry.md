# Snapshot API Client Registry

## Status
Step 2 of 11.

## Purpose
Fix the canonical client registry for the centralized Snapshot/API audit and access model.

This document defines the in-scope clients that must be represented as individual API identities.

---

## Canonical client registry

| client_id | nickname | role | status |
| --- | --- | --- | --- |
| `bobby_axe` | `BobbyAxe` | `orchestrator` | `planned` |
| `jack` | `Jack` | `infrastructure` | `planned` |
| `ben_kim` | `BenKim` | `analysis` | `active` |
| `jusetta` | `Jusetta` | `reporting` | `active` |
| `dollar_bill` | `DollarBill` | `allocation` | `planned` |
| `maffi` | `Maffi` | `grid_generation` | `planned` |
| `boss_igor` | `BossIgor` | `operator_owner` | `active` |

---

## Rules
### 1. One participant = one client identity
Each in-scope participant must have exactly one canonical client identity for this API layer.

### 2. No shared working identities
No two participants may share the same API client identity in production operation.

### 3. Stable client ids
`client_id` must be:
- lowercase
- snake_case
- stable across provisioning, logging, dashboard views, and future automation

### 4. Nickname
`nickname` is the human-readable label for dashboard and audit output.

### 5. Role
`role` describes the participant’s function in the pipeline and may be used for grouping/reporting later.

### 6. Status meanings
- `planned` — registry entry exists but issuance/verification is not complete yet
- `active` — client identity exists and is allowed to operate
- `disabled` — identity exists but access is intentionally blocked
- `revoked` — identity should no longer be used and must not be re-enabled silently

---

## Scope notes
### In scope now
- `Bobby_Axe`
- `Jack`
- `Ben_Kim`
- `Jusetta`
- `Dollar_Bill`
- `Maffi`
- `BossIgor`

### Out of scope for now
- `Maximus`

If later included, Maximus must be added as a separate canonical client identity rather than borrowing any existing key.

---

## Contract requirements for later steps
Later implementation steps must guarantee:
- physical registry storage for these identities
- one key per active participant
- audit logging keyed by `client_id`
- dashboard/reporting grouped by `client_id`
- lifecycle support for active/disabled/revoked states

---

## Acceptance for Step 2
Step 2 is complete when the team-wide canonical client registry is fixed and can be used as the basis for:
- provisioning
- logging
- dashboard accounting
- mandatory auth policy
