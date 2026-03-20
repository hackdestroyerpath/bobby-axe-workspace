# Bobby Algo Operational Spec / Code Plan

## Objective
Довести Bobby до управляемого paper-only grid algo для Binance USDC futures с ясным проходом:
market snapshot -> regime decision -> grid plan -> paper fills -> risk lock -> runner status/heartbeat.

## Scope
- Market: Binance USDC futures
- Symbols: BTCUSDC, ETHUSDC
- Timeframe: 1m
- Mode: paper only
- Execution style: maker-first preference
- Regimes: LONG_GRID / SHORT_GRID / NEUTRAL_GRID

## Current implemented blocks
1. Snapshot parsing and normalization (`market_data.py`)
2. Regime classification + grid decision (`grid_strategy.py`)
3. Risk sizing and invalidation price (`risk.py`)
4. Paper execution simulator with inventory/PnL (`simulator.py`)
5. State journaling to json/csv (`journal.py`)
6. Single-snapshot evaluation entrypoint (`agent.py`)

## Current hard limits from config
- deposit_usd: 30
- leverage: 10
- max_exposure_pct: 0.9
- max_daily_loss_pct: 0.06
- max_consecutive_losses: 3
- max_open_positions: 1
- grid_levels: 6
- min_atr_pct: 0.00035
- max_spread_bps: 4

## Operational flow
### 1) Input
Per symbol runner receives:
- symbol
- recent candles
- bid/ask
- last_price
- mark_price
- timestamp of latest candle

### 2) Pre-trade filters
Reject new grid if any of the below fails:
- symbol not in watchlist
- daily lock active from paper PnL / loss streak
- ATR below threshold
- spread wider than threshold
- structure unsuitable for grid
- neutral regime but price too far from range mid

### 3) Regime decision
`grid_strategy.py`
- LONG_GRID: uptrend + pullback intact
- SHORT_GRID: downtrend + rebound intact
- NEUTRAL_GRID: slope/bias sufficiently balanced
- otherwise `NO_TRADE`

### 4) Grid plan creation
`risk.py`
Build per-decision plan:
- center price = mark price
- lower/upper bounds = center +/- spacing * levels
- quantity per level rounded to qty step
- invalidation beyond outer bound by one more spacing
- confidence from spacing percent

### 5) Paper execution
`simulator.py`
Before new decision for current candle:
- simulate fills against previous `active_grid`
- if invalidation hit -> flatten inventory
- update realized/unrealized PnL
- update loss_streak
- update open_positions

### 6) State transition after decision
Target state machine:
- `NO_TRADE` -> no active grid
- `GRID_READY` -> active grid for current symbol only if not locked
- `DAILY_LOCK` -> no new grid, keep inventory flat or require forced flatten before save

### 7) Outputs
Per cycle persist:
- `state.json`
- `decisions.csv`
- `trades.csv`
- `daily_stats.csv` (next hardening step)
- console status line
- management files heartbeat/status summary

## Required invariants
- Never carry more than 1 open paper position across all symbols.
- Never keep `active_grid` after `DAILY_LOCK`.
- Invalidation must flatten inventory before new grid planning.
- `loss_streak` increments only on negative realized event.
- Positive realized event resets `loss_streak` to 0.
- Daily lock must depend on paper realized+unrealized logic only, not on raw presence of open position.
- Paper-only mode: no live exchange order placement.

## Current gaps to close
### Gap A — TASK-BBY-002 risk/state hardening
Need explicit transition rules in `agent.py`:
- clear stale `active_grid` on `NO_TRADE`
- clear `active_grid` on `DAILY_LOCK`
- avoid replacing valid inventory-management context with unrelated new symbol grid
- preserve symbol-aware paper state safely

### Gap B — TASK-BBY-003 multi-symbol runner
Need loop:
1. fetch snapshot for BTCUSDC
2. fetch snapshot for ETHUSDC
3. evaluate symbols in deterministic order
4. allow only one symbol in focus if open inventory exists
5. persist aggregate cycle result
6. emit one compact status line per cycle

### Gap C — TASK-BBY-004 heartbeat/status integration
Need formatter sourced from real runtime state:
- latest action
- active task
- remaining gaps
- blockers
- whether cron/runtime heartbeat is actually wired

## Code plan
### Step 1 — finalize state transitions
In `agent.py`:
- add explicit `_apply_decision_state()` rules
- on `DAILY_LOCK`: set `active_grid=None`
- on `NO_TRADE`: clear grid unless existing inventory requires management mode
- store `last_processed_symbol` and `last_cycle_time`

### Step 2 — symbol-aware state layout
Refactor `state.json` shape toward:
- `global`: lock, pnl, decision_count, current date
- `paper`: portfolio-level inventory/PnL
- `symbols`: last decision metadata per symbol
This keeps one portfolio but many scanned symbols.

### Step 3 — build runner
Create runner module or extend `agent.py`:
- iterate configured symbols
- read snapshots
- skip non-focus symbol when inventory exists in another symbol
- produce cycle summary
- save after each symbol or once per cycle

### Step 4 — extend tests
Add tests for:
- `DAILY_LOCK` clears active grid
- `NO_TRADE` clears stale grid
- open inventory blocks second symbol deployment
- multi-symbol loop respects single-position bias

### Step 5 — heartbeat/status formatting
Generate compact runtime summary from state + task files:
- symbol in focus
- state
- paper inventory side/qty
- realized/unrealized pnl
- lock status
- blocker status

## Acceptance criteria
- Can process BTCUSDC and ETHUSDC in one deterministic runner loop.
- Keeps at most one paper position at a time.
- Clears grid correctly on invalidation and lock.
- Writes reproducible decisions/trades/state across cycles.
- Heartbeat reflects actual runtime progress, not manual text only.

## Immediate next move
1. Implement state-transition hardening in `agent.py`.
2. Add tests for lock/no-trade grid clearing.
3. Then build multi-symbol runner.
