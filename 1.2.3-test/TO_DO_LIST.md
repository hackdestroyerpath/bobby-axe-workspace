# TO_DO_LIST.md

This file is a full handoff plan for the remaining Bobby work.

Goal: you take over the coding work from this point, finish the implementation, and then Bobby will pull the updated code and continue with final integration, stabilization, and validation.

The document is intentionally detailed and code-oriented.

---

# 1. Primary objective

Bring Bobby to the following state:
- autonomous paper-trading runtime
- Binance USDS-M market-data driven operation
- strategy chooses grid direction by itself
- risk/state transitions are consistent
- Binance symbol constraints are used as source of truth
- future path to testnet/live is clean and technically safe

Important:
- current target is **paper-first**, not live-first
- do not enable real-money execution yet
- any implementation should stay compatible with future Binance execution integration

---

# 2. What already exists

The following components already exist and should be treated as a base, not rewritten from scratch:

## Strategy / execution base
- grid strategy core
- regime classification (`LONG_GRID`, `SHORT_GRID`, `NEUTRAL_GRID`, `NO_TRADE`)
- paper execution simulator
- inventory tracking
- realized / unrealized PnL tracking
- invalidation handling
- basic TP/SL fields in grid plan
- neutral-grid removal basis

## Runtime / orchestration base
- multi-symbol scan
- runner summary
- readiness output
- heartbeat formatter
- one-shot paper cycle
- basic repeat-loop foundation

## Binance integration base
- Binance notes collected
- exchangeInfo-based symbol constraint path partially wired
- symbol filter loading path exists

## Workflow / reporting base
- roadmap
- status files
- memory files
- export package
- handoff package in `1.2.3-test/`

You do **not** need to redesign the system from zero.
You need to finish, harden, and connect the remaining moving parts.

---

# 3. Highest-priority implementation items

These are the highest-value remaining code tasks.

## 3.1. Build a real repeating paper runtime loop

Current state:
- one-shot paper cycle exists
- repeating loop foundation exists or is partially scaffolded
- runtime still needs to become truly autonomous

### Required result
A process that can run repeatedly without manually feeding `multi_snapshot.json`.

### It must do the following every cycle
1. fetch market data
2. build normalized symbol snapshots
3. run the Bobby agent evaluation
4. simulate paper behavior
5. produce summary
6. produce readiness output
7. persist state
8. persist last runtime status
9. wait until next cycle

### Files to review/update
- `paper_loop.py`
- `paper_cycle.py`
- `runner.py`
- `agent.py`
- `market_data.py`
- `binance_exchange.py`

### Suggested implementation details
- add a loop controller class or clear top-level loop routine
- allow parameters such as:
  - loop interval
  - symbol list override
  - max iterations
  - live mode / sample mode
- make sure state is saved after every cycle, including on exceptions where possible
- write a runtime status file after each cycle

### Suggested runtime outputs
- `loop_status.json`
- `loop_last_summary.txt`
- optional `loop_last_error.txt`

---

## 3.2. Connect the loop to real Binance market data

Current state:
- the strategy can run on sample snapshots
- Binance integration notes and exchange filter logic exist
- real market-data loop must become the normal path

### Required result
The runtime must build snapshots from real Binance USDS-M data.

### Snapshot must include
- symbol
- candles
- bid
- ask
- last price
- mark price

### Suggested source split
Use Binance endpoints/helpers to gather:
- klines / candles
- order-book top-of-book or best bid/ask
- mark price
- exchange info / symbol filters

### Design rule
Do not break the existing normalized payload contract used by `agent.py`.
Prefer adding an adapter layer that converts Binance data into the already supported snapshot structure.

### Files to review/update
- `binance_exchange.py`
- `market_data.py`
- `paper_loop.py`
- possibly `paper_cycle.py`

---

# 4. Strategy implementation work

This is where the operator voice-spec must be fully reflected in code.

## 4.1. Direction selection is the main edge

The strategy must primarily answer:
- should a long grid be deployed?
- should a short grid be deployed?
- should a neutral grid be deployed?
- should nothing be deployed?

### Goal
Do not behave like “always place some grid”.
Behave like “deploy only when direction/regime quality is good enough”.

### Review and improve
- trend detection quality
- pullback confirmation for directional grids
- rejection of bad structures
- threshold for acceptable edge
- market-regime blocker reasons

### Files to review/update
- `grid_strategy.py`
- possibly `risk.py`

---

## 4.2. Directional grid behavior

Directional grids should behave like this:
1. choose direction
2. deploy grid
3. attach take-profit
4. attach stop-loss
5. let it resolve without manual babysitting

### Required validation
Make sure TP/SL are not just calculated but actually respected by the simulator/runtime.

### Must be true after a directional exit
After TP or SL:
- active grid is removed or cleared correctly
- inventory is updated correctly
- state is consistent
- runner summary is correct
- readiness output is correct
- the same symbol can re-arm later if a new valid setup appears

### Files to review/update
- `risk.py`
- `simulator.py`
- `agent.py`
- `runner.py`
- tests in `test_simulator.py`

---

## 4.3. Neutral grid policy

Neutral grids are allowed only with caution.
They cannot stay open indefinitely.

### Required result
A strict and explicit neutral-grid removal policy.

### Neutral grid should be removed if
- max holding bars reached
- price deviates too far from the neutral range
- structure no longer matches neutral assumptions
- another explicit invalidation condition is hit

### Must be true after removal
- no stale active grid remains
- no stale `active_grids` entry remains
- no stale readiness/summarization remains
- inventory/state is correct

### Files to review/update
- `simulator.py`
- `agent.py`
- `grid_strategy.py`
- tests

---

## 4.4. Grid levels policy

Operator guidance:
- normal operating range: **1 to 5 levels**
- hard cap: **7 levels**
- strategy should prefer small, tight, frequent deployments

### Required result
A grid-level policy that is both strategic and economically realistic.

### Strategy requirements
- default should live in 1..5
- neutral grids may use fewer levels than directional setups if needed
- never silently exceed the hard cap
- never deploy economically absurd grids just to satisfy a setup signal

### If economics does not support the requested level count
The system should explicitly choose one of the following actions:
- reduce levels
- skip the symbol
- reallocate notional
- prefer another symbol

### Files to review/update
- `config.json`
- `grid_strategy.py`
- `risk.py`

---

# 5. Economics policy under a small account

This is one of the most important remaining realities.

Current problem:
- deposit is small (`~30 USD` reference)
- some symbols, especially BTCUSDC, may become economically infeasible under exchange filters + notional + levels + risk logic

This must become explicit code behavior, not accidental behavior.

## 5.1. Implement an economics decision layer

For each symbol, Bobby should be able to answer:
1. is a grid feasible at all?
2. how many levels are feasible?
3. what minimum notional per level is required?
4. what is the blocker type?

### Recommended blocker categories
- exchange filters
- account economics
- risk constraints
- market regime
- spread/ATR issues

### Required result
The code should classify infeasibility clearly and route it into summary/readiness/state.

---

## 5.2. Explicit BTCUSDC policy

Current issue:
- BTCUSDC can fail economically depending on symbol filters, notional, and level count

### You need to implement an explicit policy
For BTCUSDC, decide in code:
- when it is tradable
- when it must be skipped
- whether it should only trade in some regimes
- whether it should only trade at lower level counts
- whether it should only trade when economics supports it after filter validation

### Important
Do not leave this as accidental behavior.
It should be an explicit policy or decision path.

---

## 5.3. ExchangeInfo final binding

Binance `exchangeInfo` must become the final constraint authority.

### Make sure the runtime uses
- `PRICE_FILTER.tickSize`
- `LOT_SIZE.stepSize`
- `MIN_NOTIONAL.notional`
- supported `orderTypes`
- supported `timeInForce`

### Make sure the runtime does NOT use
- `pricePrecision` as tick size
- `quantityPrecision` as step size

### Required result
If Binance changes symbol constraints, Bobby should adapt through `exchangeInfo`, not stale hardcoded values.

### Files to review/update
- `binance_exchange.py`
- `risk.py`
- `agent.py`
- possibly `config.json`

---

# 6. Risk/state contract hardening

This is mandatory for correctness.
If this layer is weak, the runtime will lie about its state.

## 6.1. Events that must cleanly update state
You need strict state correctness after each of these:
- invalidation
- directional take-profit exit
- directional stop-loss exit
- neutral-grid removal
- risk lock
- full close followed by later re-arm

## 6.2. What must be consistent after each event
- `active_grid`
- `active_grids`
- `paper.inventory`
- `daily_pnl_usd`
- `loss_streak`
- `open_positions`
- runner summary
- readiness output
- symbol decision state

## 6.3. Specific checks

### After invalidation
- active grid removed
- inventory flattened if required
- summary updated
- readiness updated

### After TP
- realized PnL updated
- grid removed
- inventory consistent
- no stale active state remains

### After SL
- realized PnL updated
- loss streak updated
- lock logic re-evaluated
- no stale active state remains

### After neutral removal
- neutral grid fully removed
- no stale active grid pointer
- no stale summary entry

### After lock
- lock reflected in state
- lock reflected in summary
- no deployment recommendation left active

---

# 7. Tests to add or expand

You should extend the tests to cover the missing state-contract scenarios.

## Required tests
1. invalidation -> clear state
2. TP exit -> clear state
3. SL exit -> clear state
4. neutral-grid removal -> clear state
5. lock -> summary/readiness correctness
6. same-symbol re-arm after full prior close
7. economics blocker classification
8. symbol-specific policy behavior for BTCUSDC

## Recommended style
Keep the tests lightweight and runnable with the existing direct `python3 test_simulator.py` style if needed.
Do not assume pytest exists unless you add it intentionally.

### Files to review/update
- `test_simulator.py`
- optionally split into multiple test files if you prefer

---

# 8. Paper runtime stabilization

Once the repeating loop is working, do not stop at “it runs once”.
The runtime needs repeated-cycle validation.

## Run repeated cycles and check for
- state drift
- stale grids
- wrong inventory carry
- wrong symbol carry
- false locks
- incorrect readiness
- incorrect summaries
- failure to recover after exits

## Practical validation idea
Run multiple cycles in sequence and log:
- cycle result
- symbol decisions
- summary output
- readiness output
- state changes
- blocker classification

### Goal
The runtime should remain coherent across repeated cycles, not only one-shot runs.

---

# 9. Suggested clean file responsibilities

If you want to keep the code maintainable, use the following responsibility split.

## Suggested structure
- `binance_exchange.py`
  - Binance exchange info loading
  - Binance market-data access helpers
  - filter parsing / normalization

- `market_data.py`
  - normalized candle / snapshot structures

- `grid_strategy.py`
  - regime detection
  - direction choice
  - deployment decision

- `risk.py`
  - sizing
  - economics
  - symbol constraints
  - grid plan generation

- `simulator.py`
  - fill simulation
  - TP/SL handling
  - invalidation handling
  - neutral-grid removal

- `agent.py`
  - orchestration of one decision cycle
  - state mutation coordination

- `runner.py`
  - scan aggregation
  - summary output
  - readiness output

- `paper_cycle.py`
  - one-shot operational cycle

- `paper_loop.py`
  - repeating autonomous runtime loop

This separation is not mandatory, but it is strongly recommended.

---

# 10. What should NOT be done yet

At this stage, do NOT jump early into:
- real-money execution
- production live trading
- complicated live order management
- overly broad bot orchestration beyond stable paper runtime

First finish:
- stable paper runtime
- stable economics policy
- stable state/risk contract
- stable repeated-cycle behavior

Only after that should the project move to:
- Binance testnet execution path
- live-ready architecture
- eventually real-money deployment

---

# 11. Recommended implementation order

If you want the fastest practical route, do the work in this order:

1. Finish `paper_loop.py`
2. Connect real Binance market-data input
3. Add loop-status file and safe stop mechanism
4. Finalize TP/SL and neutral-removal cleanup behavior
5. Finalize risk/state contract
6. Finalize economics policy under 30 USD conditions
7. Add explicit BTCUSDC policy
8. Run repeated paper cycles
9. Validate summary/readiness consistency
10. Hand the updated code back to Bobby for final integration and stabilization

---

# 12. Direct short summary

If reduced to the essentials, the remaining coding work is:
- autonomous runtime loop
- real Binance market-data path
- strict economics policy
- strict state/risk contract
- stable repeated paper runtime behavior

Once those are done, Bobby can come back in and finish:
- final integration
- cleanup
- memory/status updates
- testnet/live-ready progression

---

# 13. Handoff expectation

After you finish the code updates:
1. push the changes to GitHub
2. tell Bobby the updated branch/path/commit if needed
3. Bobby will pull the changes
4. Bobby will update memory + control files
5. Bobby will run final integration pass and continue from there
