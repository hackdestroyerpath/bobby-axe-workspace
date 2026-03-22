# Agent Signature Contract

## Status
Step 1 of 10.

## Purpose
Fix the signature contract for agent-produced report objects in the Bobby Axe pipeline.

Initial scope:
- `Ben_Kim`
- `Dollar_Bill`

Future extension target:
- `Maffi`
- other team participants if needed

---

## Goal
Every important agent-produced object should carry a verifiable signature marker that allows Jack to:
- register the object centrally
- trace which agent produced it
- verify it against a signature ledger
- detect mismatches or unregistered objects later

---

## Core signature model
Each signed object should have two signature fields:

### 1. `signature_code`
Human-visible short signature code.

Initial format:
- 3 digits

Purpose:
- quick human reference
- visible marker on the object/report
- easy to cite in operator workflows

### 2. `signature_id`
Internal strong identifier.

Recommended format:
- UUID

Purpose:
- collision-safe internal tracking
- ledger anchoring
- verification support

---

## Why both are needed
A 3-digit code alone is too small to serve as the only strong identity for ongoing production usage.

Therefore:
- `signature_code` is the short visible signature
- `signature_id` is the internal strong ledger identity

The system should preserve both.

---

## Initial in-scope agents
### `Ben_Kim`
Signed objects may include:
- analysis-only report objects
- per-ticker analysis objects
- future analysis result packages

### `Dollar_Bill`
Signed objects may include:
- capital allocation outputs
- allocation decision objects
- future capital summary/result packages

---

## Signature creation rule
For every signed object:
1. the producing agent gets or generates a short `signature_code` under the controlled signing model;
2. Jack records a central ledger entry for that object;
3. the signed object is stored with its signature fields;
4. the ledger keeps the binding between agent identity, object identity, and signature values.

---

## Ledger binding rule
The central signature ledger must be able to bind at least:
- agent identity
- object type
- object scope
- object id / report id / analysis id / allocation id
- `signature_code`
- `signature_id`
- creation time
- status

---

## Verification rule
Later verification must be able to answer:
- does this object have a registered signature?
- does the signature belong to this agent?
- does the signature belong to this exact object scope?
- does the stored object match the central ledger record?

---

## Storage rule
The signature system should be centralized under Jack.

This means:
- Jack maintains the canonical ledger storage
- agent-specific signing records are tracked centrally
- agents do not need to run separate private SQL storage for this mechanism

---

## Initial operational direction
The first implementation should be centralized rather than federated.

Meaning:
- one controlled signing/ledger system under Jack
- agent field distinguishes owner (`Ben_Kim`, `Dollar_Bill`, later `Maffi`)
- verification is also centralized

---

## Acceptance for Step 1
Step 1 is complete when the signature contract is fixed as source-of-truth, including:
- visible short code
- strong internal id
- central ledger model
- initial in-scope agents
- verification purpose
