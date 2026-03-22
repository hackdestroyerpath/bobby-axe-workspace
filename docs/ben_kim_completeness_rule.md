# Ben_Kim Completeness Rule

## Status
Step 8 of 20.

## Purpose
Define what the contract firewall must treat as a complete vs incomplete return set for `Ben_Kim` per ticker.

---

## Complete Ben_Kim ticker return
A ticker return set for `Ben_Kim` should be treated as complete only if all of the following are true:

### 1. Required timeframes exist
The return set contains strategy objects for:
- `1m`
- `5m`
- `60m`

### 2. Full strategy coverage exists in each timeframe
For each required timeframe, all 6 expected strategies are present.

### 3. Summary object exists
A separate ticker summary object exists.

### 4. Mandatory conclusions are not empty
Each strategy object has a non-empty conclusion.

The ticker summary object also has a non-empty conclusion.

### 5. Scope is consistent
The objects all belong to the same expected:
- `producer`
- `snapshot_id`
- `correlation_id`
- `symbol`

---

## Incomplete return
A Ben_Kim return set should be treated as incomplete if any of the following happen:
- one or more required timeframes are missing
- one or more required strategies are missing in any timeframe
- summary object is missing
- required object count is below the expected total

---

## Partial return
A return set may be treated as partial when some valid strategy objects exist, but full contract completeness is not satisfied.

This still should not be treated as fully accepted completeness.

---

## Rejected return
A return set may be treated as rejected when the failure is severe enough that the returned data should not be accepted into the canonical valid result layer.

Examples:
- wrong producer/scope
- structurally invalid object family
- widespread empty conclusions

---

## Acceptance for Step 8
Step 8 is complete when Ben_Kim completeness is fixed as source-of-truth for ticker-level firewall evaluation.
