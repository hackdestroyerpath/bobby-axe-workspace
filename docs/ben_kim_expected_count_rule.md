# Ben_Kim Expected Count Rule

## Status
Step 7 of 20.

## Purpose
Define how many objects the contract firewall should expect from `Ben_Kim` per ticker.

This document makes the expected return count explicit so the firewall can detect incomplete or under-filled return sets.

---

## Strategy count assumption
Current Ben_Kim strategy set:
- 6 strategies

Current required timeframes:
- `1m`
- `5m`
- `60m`

---

## Expected atomic object count
For each ticker, the firewall should expect:
- 6 strategy objects for `1m`
- 6 strategy objects for `5m`
- 6 strategy objects for `60m`

That gives:
- `6 × 3 = 18` atomic strategy objects

---

## Expected summary object count
For each ticker, the firewall should also expect:
- 1 ticker summary object

---

## Total expected count per ticker
For one ticker, the expected return count is:
- `18` strategy objects
- `1` ticker summary object

Total:
- **`19` objects per ticker**

---

## Contract implication
If fewer than 19 expected objects are returned for a ticker, the firewall must not treat the return set as fully complete.

Typical outcome:
- `incomplete`
- or `partial`, depending on the surrounding rule set

---

## Acceptance for Step 7
Step 7 is complete when the expected Ben_Kim object count is fixed as source-of-truth and can be used later in completeness and SQL-level validation.
