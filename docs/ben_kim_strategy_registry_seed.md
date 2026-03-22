# Ben_Kim Canonical Strategy List

## Status
Step 2 of 8.

## Purpose
Fix the canonical strategy set for Ben_Kim.

This document defines the exact strategy identities that must be used as the allowed source set for Ben_Kim strategy naming.

These are the strategies proposed by Ben_Kim and approved for the naming-contract track.

---

## Canonical strategy set

| strategy_id | strategy_name |
| --- | --- |
| `price_levels_fibo_horizontal_volume` | `Price Levels + Fibo + Horizontal Volume` |
| `vertical_volume` | `Vertical Volume` |
| `rsi_macd` | `RSI + MACD` |
| `trade_speed` | `Trade Speed` |
| `added_later_placeholder` | `Added Later Placeholder` |
| `elliott_waves` | `Elliott Waves` |

---

## Rules
### 1. Allowed values only
Ben_Kim must use only strategy identities from this canonical set.

### 2. No renaming
Ben_Kim must not:
- shorten `strategy_id`
- rewrite `strategy_name`
- replace `strategy_name` with a narrative phrase
- merge multiple canonical strategies into one synthetic label

### 3. One-to-one mapping
Every `strategy_id` maps to exactly one `strategy_name`.

Every `strategy_name` maps to exactly one `strategy_id`.

### 4. Registry seed source
This list is the exact seed set to be used in the next storage/registry step.

---

## Canonical examples
### Valid
- `strategy_id = rsi_macd`
- `strategy_name = RSI + MACD`

### Invalid
- `strategy_id = rsi`
- `strategy_name = RSI`

### Invalid
- `strategy_id = momentum`
- `strategy_name = Bullish Momentum`

### Invalid
- `strategy_id = elliott`
- `strategy_name = Elliott`

---

## Migration note
Current write-side still uses a single `strategy` field in parts of the contract.

During migration, that field must align with the canonical strategy identity and later be expanded to explicit:
- `strategy_id`
- `strategy_name`

No migration step may loosen the canonical mapping defined here.

---

## Acceptance for Step 2
Step 2 is complete when the exact Ben_Kim strategy set is fixed and can be used as:
- registry seed data
- validation allowlist
- payload metadata source
- downstream naming contract
