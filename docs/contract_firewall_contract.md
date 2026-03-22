# Contract Firewall Contract

## Status
Step 1 of 20.

## Purpose
Fix the contract firewall model for validating agent return objects before they are accepted into the canonical pipeline storage.

This firewall is intended to protect the pipeline from:
- incomplete returns
- empty mandatory fields
- missing mandatory objects
- wrong object scope
- structurally invalid return sets
- false acceptance of objects that do not satisfy the expected agent contract

---

## Core idea
Jack should not accept agent output merely because some data arrived.

Jack should accept agent output only if it passes the expected return contract checks.

This means Jack acts as a contract firewall and validation gate before canonical storage acceptance.

---

## What the firewall validates
The contract firewall should validate at least:
1. schema presence
2. mandatory object presence
3. mandatory field presence
4. non-empty mandatory value rules
5. scope consistency
6. completeness against expected return set
7. agent identity consistency
8. linkage to input/request context

---

## Expected return concept
For every agent request, Jack should know in advance:
- what input was given
- what output object types are expected
- how many objects are expected
- which fields are mandatory
- which fields may not be empty
- what makes the return accepted vs partial vs rejected

---

## Mandatory object rule
If an expected object type is required by the contract but not returned, the firewall must not treat the return set as fully valid.

Depending on policy, this should produce:
- `incomplete`
- or `rejected`

---

## Mandatory field rule
If an expected object exists but lacks a mandatory field, the firewall must not treat it as fully valid.

---

## Non-empty rule
A mandatory field may exist syntactically but still be unacceptable if it is empty.

Examples of unacceptable emptiness may include:
- `null`
- empty string
- whitespace-only string
- empty array where a populated object set is required
- empty explanation/conclusion where a real conclusion is mandatory

---

## Scope consistency rule
Returned objects must match the request scope they are supposed to satisfy.

Examples of scope fields:
- `snapshot_id`
- `correlation_id`
- `symbol`
- `frame`
- `strategy_id`
- producer/agent identity

A mismatch in scope should not be silently accepted.

---

## Input-output linkage rule
The firewall should be able to determine whether the returned objects correspond to the requested work.

This means the accepted output set must be traceable to:
- the original request context
- the expected producer
- the expected object scope

---

## Firewall outcomes
Suggested canonical outcomes:
- `accepted`
- `partial`
- `incomplete`
- `rejected`
- `mismatch`

### `accepted`
All required objects and fields are present, non-empty where required, and consistent with scope.

### `partial`
Some valid content exists, but not enough to satisfy the full expected contract.

### `incomplete`
The return set is missing mandatory objects or required structural coverage.

### `rejected`
The return set fails mandatory acceptance rules and should not enter canonical accepted storage.

### `mismatch`
The return set exists, but it does not match the expected request scope or object linkage.

---

## Storage implication
The firewall exists before canonical acceptance.

Meaning:
- not every returned object should automatically enter accepted canonical storage
- invalid/incomplete/mismatched returns may need separate handling or rejection paths

---

## Why this matters
Without a firewall, the pipeline may accept:
- empty conclusions
- half-complete return sets
- wrong ticker/frame/scope data
- structurally broken agent outputs
- misleadingly “successful” but unusable objects

The firewall prevents this.

---

## Acceptance for Step 1
Step 1 is complete when the contract firewall is fixed as source-of-truth and defines the general validation role Jack must play before accepting agent return data.
