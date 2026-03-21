# Strategy Notes — 2026-03-21

Operator guidance captured from voice note:

## Core intent
- Grid bot only.
- USDC pairs only.
- Prefer maker-first / near-zero-fee path where applicable.
- Small account reference: 30 USD.
- Strategy should autonomously choose direction:
  - LONG_GRID
  - SHORT_GRID
  - NEUTRAL_GRID (use cautiously)

## Grid behavior
- Small ranges.
- Small, fast, frequent deployments.
- Prefer 1m timeframe, possibly lower later.
- Prefer 1 to 5 grid levels normally.
- Hard cap discussed: no more than 7 levels.
- Directional grids should be set with TP and SL and then left alone.
- Neutral grids require explicit removal logic; do not leave them unmanaged.

## Operator objective
- High trade frequency.
- Small/short trades instead of oversized exposure.
- Maximize clean execution frequency while keeping risk management active.

## Risk note
Operator mentioned high leverage preferences up to exchange maximums. This is captured as operator preference, not yet accepted as Bobby default operating rule. Bobby should keep risk-first logic and only convert leverage preferences into code after explicit constraint review.
