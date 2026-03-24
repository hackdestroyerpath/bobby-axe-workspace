# Maffi Contract v0.1

Статус: approved draft for implementation.

## Required input fields
- schema_version (string)
- symbol (string)
- generated_at_utc (ISO-8601 UTC)
- source (string)
- input_quality_status: `ok | degraded | bad`
- market_regime: `trend | range | chaotic`
- volatility_regime: `low | normal | high`
- dominant_side: `buyers | sellers | mixed`
- long_score, short_score, reject_score (0..100)
- confidence_hint (0..1)
- entry_candidates (non-empty numeric list)
- support_level < resistance_level
- last_price (number)
- atr (>0)

## Decision outputs
- decision: `reject | long | short`
- confidence: 0..1
- selected_entry, tp, sl
- reject_reason (for reject only)
- rationale[]
- decision_trace {}

## Output envelope (formatter contract)
Formatter MUST serialize `MaffiOutput` with stable top-level keys in this exact order:
1. `schema_version`
2. `generated_at_utc`
3. `symbol`
4. `decision`
5. `confidence`
6. `selected_entry`
7. `tp`
8. `sl`
9. `input_quality_status`
10. `reject_reason`
11. `rationale`
12. `decision_trace`

Required fields for every output envelope:
- `schema_version`
- `generated_at_utc`
- `symbol`
- `decision`
- `confidence`
- `input_quality_status`
- `rationale`
- `decision_trace`

Normalization requirements for downstream:
- `rationale` is serialized as `list[str]` with trimmed, non-empty entries.
- `decision_trace` is serialized as a JSON-friendly object with recursively normalized values.
- Enum values inside trace are emitted as primitive `.value` strings.
- Mapping keys inside trace are stringified and sorted to preserve deterministic shape.

## Reject policy (hard fail vs soft degrade)
Hard reject:
1. Structural/semantic validation error.
2. `input_quality_status = bad`.
3. `reject_score >= 60`.

Soft degrade:
1. `input_quality_status = degraded` -> confidence penalty (default -0.20).
2. Cross-field warnings are added to decision trace.

## Traceability envelope
- schema_version
- generated_at_utc
- input_quality_status
- reject_reason
