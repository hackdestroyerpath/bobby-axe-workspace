# Bobby Algo Status

## Version
v1.4 paper-ready cycle assembled

## Implemented
- snapshot parsing
- spread filter
- ATR filter
- regime classifier: LONG_GRID / SHORT_GRID / NEUTRAL_GRID / reject
- grid builder with lower/upper bounds
- per-level quantity sizing
- invalidation price
- local decision/state journaling
- candle-touch paper fill simulator
- paper inventory tracking
- realized/unrealized PnL state
- invalidation flatten logic
- loss_streak update from losing realized fills
- multi-symbol scan loop
- per-symbol decision tracking in state
- symbol-specific sizing overrides
- runner-level scan summary
- readiness output
- heartbeat/status formatter
- final paper-ready cycle script
- smoke tests for simulator, sizing, readiness

## Current decision states
- `GRID_READY`
- `NO_TRADE`
- `DAILY_LOCK`

## Current constraints
- paper only
- no exchange connector yet
- no repeating live loop runner yet
- no live execution
- cron heartbeat not confirmed at system level in current runtime

## Latest local run
- BTCUSDC: `GRID_READY`
- ETHUSDC: `NO_TRADE`
- Summary: `scan_total=2 | grid_ready=1 | no_trade=1 | daily_lock=0 | ready_symbols=BTCUSDC | blocked_symbols=ETHUSDC`
- Readiness: `PAPER_READY`

## Next build steps
1. Finish TASK-BBY-002 state transitions around locks/invalidation.
2. Add repeating paper loop runner.
3. Then Bobby can run paper cycles without manual launch.
