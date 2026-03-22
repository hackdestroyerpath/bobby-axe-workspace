# Agent Signature API Design

## Status
Step 8 of 10.

## Purpose
Define the API/service design for centralized agent signature registration and verification.

Initial scope:
- `Ben_Kim`
- `Dollar_Bill`

---

## Design goal
The signing mechanism should work through controlled service/API paths rather than ad-hoc manual registration.

This keeps signature creation and verification:
- centralized
- auditable
- consistent with the broader access model

---

## Recommended API surfaces
### 1. Signature registration path
Purpose:
- register a signed object in the central ledger
- persist the link between object identity and signature identity

Suggested conceptual endpoint:
- `POST /signatures/register`

### 2. Signature verification path
Purpose:
- verify a signed object or object reference against the central ledger

Suggested conceptual endpoint:
- `POST /signatures/verify`

### 3. Signature lookup path
Purpose:
- inspect previously registered signatures by object/agent/scope

Suggested conceptual endpoint:
- `GET /signatures?...`

---

## Registration request concept
A registration request should include at least:
- `producer`
- `object_type`
- `object_id`
- `object_scope`
- `signature_code`
- `signature_id`
- optional verification payload / object hash
- optional notes

---

## Registration response concept
A successful registration response should include at least:
- `status`
- `producer`
- `object_type`
- `object_id`
- `signature_code`
- `signature_id`
- `ledger_status`
- timestamps

---

## Verification request concept
A verification request should include enough to test the signature relationship, for example:
- `producer`
- `object_type`
- `object_id`
- `signature_code`
- `signature_id`
- optional object scope and verification payload/hash

---

## Verification response concept
A verification response should include at least:
- `verification_status`
- `producer`
- `object_type`
- `object_id`
- `signature_code`
- `signature_id`
- mismatch notes if any

---

## Link to business-object write flow
The signature API should integrate with the business-object write flow rather than float as an isolated side feature.

Meaning:
- a signed Ben_Kim analysis object should either register its signature as part of the same controlled workflow,
- or the write path should call the signature registration path as a deterministic sub-step.

The same applies later to Dollar_Bill signed objects.

---

## Auth/accounting expectation
Signature registration and verification should follow the same access principles as the rest of the centralized stack:
- identity-bound access
- API key based access
- audit logging
- attributable usage

---

## Acceptance for Step 8
Step 8 is complete when the centralized signature API/service model is fixed as source-of-truth and clearly separates registration, verification, and lookup functions.
