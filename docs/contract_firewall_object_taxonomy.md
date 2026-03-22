# Contract Firewall Object Taxonomy

## Status
Step 2 of 20.

## Purpose
Define the object taxonomy used by the contract firewall.

The firewall should validate explicit object types, not vague undifferentiated payload blobs.

---

## Core principle
Every agent return should be understood as a set of typed objects.

The firewall must know what object types are expected before it can correctly determine:
- completeness
- missing items
- empty required content
- wrong object family
- scope mismatch

---

## Initial object families
### 1. Strategy-level analysis object
Used for agent conclusions at the level of:
- one ticker
- one timeframe
- one strategy

Initial producer focus:
- `Ben_Kim`

Suggested conceptual type:
- `analysis_strategy_result`

---

### 2. Ticker summary object
Used for an overall conclusion for one ticker across the relevant strategy/frame result set.

Initial producer focus:
- `Ben_Kim`

Suggested conceptual type:
- `analysis_ticker_summary`

---

### 3. Grid proposal object
Used for a grid or trade-setup proposal derived from upstream analysis.

Initial producer focus:
- `Maffi`

Suggested conceptual type:
- `grid_proposal`

---

### 4. Allocation object
Used for capital allocation or allocation-decision output.

Initial producer focus:
- `Dollar_Bill`

Suggested conceptual type:
- `capital_allocation`

---

### 5. Future package object
Used for bundled or packaged outputs when an agent later emits a combined artifact rather than only atomic records.

Possible conceptual types:
- `analysis_package`
- `allocation_package`
- future package families

---

## Why taxonomy matters
Without explicit types, the firewall cannot reliably know:
- whether an expected result is missing
- whether a returned object belongs to the wrong family
- whether the object count is sufficient
- whether summary vs atomic records are being confused

---

## Initial usage by agent
### `Ben_Kim`
Expected to return:
- `analysis_strategy_result`
- `analysis_ticker_summary`

### `Maffi`
Expected to return later:
- `grid_proposal`

### `Dollar_Bill`
Expected to return later:
- `capital_allocation`

---

## Firewall interpretation rule
The firewall should not validate “some JSON” in the abstract.

It should validate a typed return set composed of known object families.

---

## Acceptance for Step 2
Step 2 is complete when the return-validation layer has a fixed object taxonomy that can be used to express exact expected outputs for Ben_Kim, Maffi, and Dollar_Bill.
