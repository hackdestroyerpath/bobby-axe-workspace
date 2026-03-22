# Contract Firewall Non-Empty Policy

## Status
Step 4 of 20.

## Purpose
Define how the contract firewall interprets empty vs acceptable values for mandatory fields.

This is especially important for conclusions, comments, and other fields that may exist syntactically but still be operationally useless.

---

## Core rule
A mandatory field is not acceptable merely because the key exists.

If the value is empty in a meaningful operational sense, the firewall should treat it as failing the contract.

---

## Values that should normally count as empty
The following should normally be treated as empty for mandatory textual fields:
- `null`
- empty string `""`
- whitespace-only string
- placeholder-only content that carries no real conclusion

The following should normally be treated as empty for required collections when actual content is expected:
- empty array
- empty object

---

## Important focus fields
For the current use case, the firewall must be especially strict about non-empty values for fields such as:
- `conclusion`
- summary conclusion/comment fields
- explanation/comment fields where the contract says a real explanation is required

---

## Why this matters
Without non-empty rules, the pipeline may accept:
- blank comments
- structurally present but meaningless conclusions
- empty summaries
- fake success objects that contain no usable content

This would damage downstream quality while still looking superficially “valid”.

---

## Operational interpretation
If a required textual conclusion field is empty, the object should not be treated as fully valid.

Depending on the surrounding completeness context, the outcome may become:
- `partial`
- `incomplete`
- `rejected`

---

## Example: Ben_Kim strategy result
A strategy result object with:
- correct `ticker`
- correct `frame`
- correct `strategy_id`
- but empty `conclusion`

should not pass as a fully valid strategy result.

---

## Example: Ben_Kim ticker summary
A ticker summary object with no real summary text should not satisfy the summary requirement.

---

## Acceptance for Step 4
Step 4 is complete when the firewall non-empty rule is fixed in source-of-truth documentation and makes clear that empty mandatory conclusions/comments fail the contract even when the field key exists.
