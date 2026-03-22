# Snapshot API Endpoint Coverage

## Status
Step 6 of 11.

## Purpose
Fix the canonical auth/logging/accounting coverage matrix for Snapshot/API endpoints.

This document records which endpoints:
- require API key auth
- are logged in access audit
- are allowed to be unauthenticated
- are expected to produce accountable usage records

---

## Coverage matrix

| Endpoint | Method | Auth required | Logged | Expected status notes |
| --- | --- | --- | --- | --- |
| `/health` | `GET` | No | No | liveness only |
| `/` | `GET` | No | Yes | UI shell only; no data by itself |
| `/lookup` | `GET` | Yes | Yes | `ok` / `partial` / `denied` / `error` |
| `/payload` | `GET` | Yes | Yes | `ok` / `partial` / `denied` / `error` |
| `/strategies` | `GET` | Yes | Yes | `ok` / `denied` |
| `/stats` | `GET` | Yes | Yes | `ok` / `denied` |
| `/lookup/download` | `GET` | Yes | Yes | `ok` / `denied` |
| `/lookup/save` | `GET` | Yes | Yes | `saved` / `denied` |
| `/analysis/write` | `POST` | Yes | Yes | `ok` / `partial` / `error` / `denied` |

---

## Interpretation
### Unauthenticated exception
Only the following are allowed without API key:
- `/health`
- `/` (UI shell only)

These routes must not expose production data directly.

### Accountable routes
All production data-bearing or business-bearing routes must be:
- identity-bound
- logged
- attributable to a specific client where key is supplied

---

## Logging expectation
For logged routes, audit records should preserve at least:
- `client_id`
- `nickname`
- `endpoint`
- `snapshot_id` when applicable
- `selected_symbol` when applicable
- `resolved_bundle_id` when applicable
- `request_status`
- request timestamp

---

## Status notes by endpoint
### `/lookup`
Normal statuses:
- `ok`
- `partial`
- `denied`
- `error`

### `/payload`
Normal statuses:
- `ok`
- `partial`
- `denied`
- `error`

### `/strategies`
Normal statuses:
- `ok`
- `denied`

### `/stats`
Normal statuses:
- `ok`
- `denied`

### `/lookup/download`
Normal statuses:
- `ok`
- `denied`

### `/lookup/save`
Normal statuses:
- `saved`
- `denied`

### `/analysis/write`
Normal statuses:
- `ok`
- `partial`
- `error`
- `denied`

### `/`
Normal statuses:
- `ok` (identified UI shell open)
- `anonymous` (shell opened without key)

---

## Operational expectations
### 1. Data routes
All data routes must reject anonymous production access when auth mode is mandatory.

### 2. Dashboard accounting
Dashboard/accounting views should be able to summarize usage for all logged accountable routes.

### 3. Future route additions
Any future Snapshot/API route must define before release:
- whether auth is required
- whether it is logged
- what request statuses it emits
- whether it is accountable in dashboard reporting

---

## Acceptance for Step 6
Step 6 is complete when the endpoint coverage model is fixed in source-of-truth documentation and aligned with the current implementation.
