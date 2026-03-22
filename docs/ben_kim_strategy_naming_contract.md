# Ben_Kim Strategy Naming Contract

## Status
Step 1 of 8.

## Purpose
This document fixes the canonical naming contract for Ben_Kim strategies.

Goal:
- Ben_Kim must not invent strategy names
- Ben_Kim must not shorten them
- Ben_Kim must not replace them with narrative categories
- Ben_Kim must read canonical strategy names from one source of truth and write back the same names unchanged

---

## Core rule
For every Ben_Kim analysis result there must be an exact strategy identity.

That identity must come from a canonical source of truth.

Ben_Kim is not allowed to:
- invent a new strategy name at runtime
- rename a strategy for convenience
- collapse multiple strategies into one narrative label
- substitute strategy family/category text instead of the canonical strategy identity

---

## Naming model
Each strategy must have two separate naming fields:

### 1. `strategy_id`
Machine key.

Rules:
- stable
- lowercase
- snake_case
- immutable once published into production contracts
- used in payloads, validation, storage keys, writeback, and downstream joins

Example:
- `rsi_macd`

### 2. `strategy_name`
Canonical human-readable label.

Rules:
- stable display label
- can include spaces, `+`, and title-case formatting
- must map 1-to-1 to one `strategy_id`

Example:
- `RSI + MACD`

---

## Required behavior for Ben_Kim
Ben_Kim must:
1. read canonical strategy identities from one source of truth;
2. use the exact `strategy_id` provided there;
3. use the exact `strategy_name` provided there;
4. write back the same strategy identity without renaming;
5. keep `strategy_id` and `strategy_name` aligned on every output row.

Ben_Kim must not output only a free-form narrative label such as:
- `momentum`
- `reversal`
- `bearish setup`
- `bullish cluster`

Those may appear only inside explanation text, never as the strategy identity.

---

## Canonical source-of-truth rule
There must be exactly one canonical source of truth for Ben_Kim strategies.

Allowed implementation shapes:
- config table
- strategy registry table
- strategy metadata endpoint
- strategy dictionary embedded from one canonical backend source

But whichever implementation is chosen, it must be singular and canonical.

No secondary naming source may override it.

---

## Contract requirement for later steps
Later implementation steps must guarantee:
- Ben_Kim reads strategy names from a canonical registry source
- payload explicitly carries strategy identity
- writeback explicitly carries strategy identity
- downstream storage preserves strategy identity

---

## Minimum downstream expectation
Every stored Ben_Kim analysis row must contain at least:
- `symbol`
- `frame`
- strategy identity
- `conclusion`

Where strategy identity means either:
- `strategy_id` + `strategy_name`

or, temporarily during migration:
- a canonical `strategy` field that is proven equivalent to canonical `strategy_id`

Preferred steady-state model:
- `strategy_id`
- `strategy_name`

---

## Definition of done for the full strategy naming track
This track is complete only if:
1. Ben_Kim reads exact strategy names from the canonical source;
2. Ben_Kim writes back the same names without renaming;
3. each stored analysis record contains the strategy identity and Ben_Kim conclusion.

---

## Step 1 result
Step 1 is complete when the naming contract is documented and frozen before storage/runtime changes begin.
