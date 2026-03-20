# Bobby Algo Roadmap

## Current objective
Turn Bobby from a grid decision engine into a paper-trading grid algo with simulated fills, inventory tracking, and PnL.

## Execution plan
1. Add paper execution state model.
2. Add grid level generation per regime.
3. Add candle-touch fill simulator for entries/exits.
4. Track open paper inventory and realized PnL.
5. Update risk lock from paper results.
6. Add multi-symbol scan loop.
7. Add heartbeat/status formatting.

## Step status
- [x] Step 1 planned
- [x] Step 2 paper execution state model implemented
- [x] Step 3 candle-touch fill simulator v0 implemented
- [x] Step 4 open paper inventory + realized/unrealized PnL state implemented
- [~] Step 5 risk lock from paper results hardening in progress
- [x] Step 6 multi-symbol scan loop
- [ ] Step 7 heartbeat/status formatting

## Current micro-steps
1. Finalize post-invalidation state transitions.
2. Fix symbol-specific sizing constraints for BTCUSDC.
3. Add heartbeat formatter from STATUS/TASKS/ACTION_LOG.
4. Add runner-level summary output.

## Constraints
- paper only
- Binance USDC futures only
- grid only
- risk-first
