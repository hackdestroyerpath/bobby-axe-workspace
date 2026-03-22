# Contract Firewall Operational Rulebook

## Status
Step 18 of 20.

## Purpose
Provide an operational rulebook for how agent return objects should be handled under the contract firewall.

This rulebook translates the firewall model into practical operating behavior.

---

## For Jack
Jack should:
1. know what return object families are expected before accepting data;
2. validate scope linkage before canonical acceptance;
3. validate non-empty mandatory conclusions/comments;
4. validate completeness against the expected return set;
5. apply the canonical outcome model before deciding storage behavior;
6. preserve validation audit trail information.

Jack should not treat arrival alone as acceptance.

---

## For agents
Agents should:
1. return the correct object family for their role;
2. return the correct scope fields;
3. avoid empty required conclusions/comments;
4. return the full expected object set when completeness is required;
5. treat the controlled contract as the real delivery target, not vague free-form output.

---

## What counts as a valid return in practice
A return is operationally valid only when it is:
- correctly typed
- in the right scope
- complete enough for the expected contract
- non-empty where required
- accepted by the firewall outcome model

---

## Acceptance for Step 18
Step 18 is complete when the contract firewall has a short operational rulebook explaining how Jack and agents should behave in practice.
