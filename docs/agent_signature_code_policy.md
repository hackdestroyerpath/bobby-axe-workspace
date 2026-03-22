# Agent Signature Code Policy

## Status
Step 3 of 10.

## Purpose
Define how the human-visible 3-digit `signature_code` should behave.

This document covers:
- generation
- uniqueness scope
- collision handling
- reuse policy
- relationship to strong internal identity

---

## 1. Signature code format
`signature_code` is a human-visible short code.

Initial format:
- exactly 3 digits
- examples: `042`, `317`, `905`

The code should be stored as text, not integer, so leading zeroes are preserved.

---

## 2. Why code alone is not enough
A 3-digit code has only 1000 possibilities.

Therefore:
- it is useful as a short visible marker
- it is not strong enough to be the sole durable identity in production

The durable identity remains:
- `signature_id`

---

## 3. Generation rule
The short `signature_code` should be generated under the controlled signing path.

Acceptable direction:
- agent-side generation logic may propose the visible 3-digit code
- Jack-side centralized ledger must still register the final object and strong identity

This means the code may originate with the agent logic, but validity comes only from successful ledger registration.

---

## 4. Uniqueness scope
`signature_code` should not be treated as globally unique forever.

Instead, uniqueness should be interpreted within a controlled scope, for example:
- producer
- object_type
- object_scope
- bounded time window or registration event

The authoritative unique identity is still:
- `signature_id`

---

## 5. Collision policy
If the same 3-digit code appears again, this is not automatically a failure.

The system should decide using the stronger tuple:
- `producer`
- `object_type`
- `object_id` / scope
- `signature_id`

### Collision handling rule
If a proposed `signature_code` collides inside an invalid or ambiguous scope:
- either regenerate a new code
- or mark the attempt as collision and retry registration

The ledger must not rely on the 3-digit code alone for uniqueness.

---

## 6. Reuse policy
The same 3-digit code may be reused across time, provided the strong ledger identity remains distinct.

It should not be treated as a permanent globally unique serial number.

---

## 7. Recommended registration tuple
The practical signing tuple should be:
- `producer`
- `object_type`
- `object_id`
- `signature_code`
- `signature_id`

This lets operators talk in short human codes while the system still remains safe under strong internal identity.

---

## 8. Verification rule
Verification should never accept an object solely because the 3-digit code looks familiar.

Verification must check at least:
- `signature_id`
- expected producer
- expected object identity/scope
- optionally a verification hash/payload

---

## 9. Operational guidance
The 3-digit code is for:
- visibility
- quick reference
- operator workflow
- report annotation

The 3-digit code is not the only trust anchor.

---

## Acceptance for Step 3
Step 3 is complete when the 3-digit signature code is defined as a short visible marker with clear rules for generation, collision handling, reuse, and relationship to strong internal identity.
