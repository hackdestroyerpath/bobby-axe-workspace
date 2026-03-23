# Ben_Kim Storage Contamination Policy

## Status
Phase 6 hardening note.

## Purpose
Зафиксировать, как интерпретировать загрязнение в `collector.analysis_results`:
- что считать canonical row;
- что считать legacy/test contamination;
- как оператору различать это без guesswork.

---

# 1. Why this note exists

Во время controlled loops подтвердилось, что в `collector.analysis_results` уже присутствуют historical rows, которые не выглядят как чистый current canonical layer.

Это значит, что storage interpretation itself needs policy.

---

# 2. What counts as canonical row

Для `Ben_Kim` canonical row должна соответствовать одновременно следующим условиям.

## Canonical condition C1 — strategy identity
Row uses current approved canonical strategy identity:
- `price_levels_fibo_horizontal_volume`
- `vertical_volume`
- `rsi_macd`
- `trade_speed`
- `added_later_placeholder`
- `elliott_waves`

## Canonical condition C2 — row semantics
Row fits current canonical write semantics:
- correct `status/result_code` pairing
- storage-safe `signal`
- valid frame (`1m`, `5m`, `60m`)

## Canonical condition C3 — execution meaning
Row represents a real analysis_result for current analytical contract, not a scratch/test artifact.

---

# 3. What counts as contamination

## Contamination type T1 — legacy strategy naming
Rows using non-canonical or historical strategy naming.

Example observed:
- `rsi_macd_cluster`

## Contamination type T2 — test-only artifacts
Rows whose `analysis_id`, naming, or semantics indicate testing rather than current canonical production-style writeback.

## Contamination type T3 — historical intermediate contract rows
Rows written under older payload shapes, older naming contracts, or older validation assumptions.

---

# 4. Practical contamination signals

Operator should treat a row as suspicious/non-canonical if one or more of the following are true.

## Signal S1
`strategy` is outside the current approved set.

## Signal S2
`analysis_id` obviously looks like ad-hoc test/probe naming.

## Signal S3
`strategy_id` / `strategy_name` mismatch current registry expectations.

## Signal S4
Row predates current canonical contract and cannot be confidently mapped into current semantics.

---

# 5. Current correct operator rule

Until cleanup/segregation is complete:
1. do not assume every row in `collector.analysis_results` is canonical-clean
2. inspect strategy naming before interpreting duplicate conflicts
3. treat suspicious historical rows as contamination candidates
4. interpret duplicate conflicts in light of already-existing test/legacy rows

---

# 6. What this means for duplicate analysis

Duplicate conflict does not always mean:
- current canonical row already exists cleanly

It may also mean:
- a legacy/test row already occupies the logical uniqueness slot

This distinction is critical.

---

# 7. Minimally acceptable policy

A minimally acceptable storage policy should let operator answer these questions clearly:

1. Is this row canonical current output?
2. Is this row legacy/test contamination?
3. Should this row block new canonical write?
4. Should this row be ignored, isolated, migrated, or cleaned?

---

# 8. Preferred long-term policy options

## Option P1 — explicit cleanup
Remove or archive legacy/test rows from active canonical storage.

## Option P2 — explicit segregation
Keep legacy/test rows but clearly separate them from canonical active rows.

## Option P3 — explicit tagging/marking
Preserve rows in place but add enough metadata/policy so operator can distinguish them deterministically.

---

# 9. Minimum improvement target for this track

This track is improved only if:
1. operator can identify canonical vs contaminated rows without guesswork
2. duplicate conflicts can be interpreted correctly
3. canonical storage semantics become cleaner and more trustworthy

---

# 10. Current status of this track

Current status:
- contamination is observed
- contamination matters operationally
- contamination policy is not yet fully hardened

Therefore this track remains:
- open

---

# 11. Use

Этот note использовать как:
- storage interpretation baseline;
- contamination policy reference;
- input into cleanup / segregation decision.
