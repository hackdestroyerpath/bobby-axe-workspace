# Bobby Axelrod

Paper-only grid trading brain for Binance USDC futures.

## Scope
- USDC futures only
- 1m timeframe
- auto regime selection: `LONG_GRID`, `SHORT_GRID`, `NEUTRAL_GRID`
- paper mode only
- risk-first deployment

## Current logic
- validates snapshots and sizing constraints
- blocks on spread / volatility / economics filters
- classifies market into long / short / neutral grid regimes
- builds bounded grid plans with invalidation
- runs paper cycles and loop summaries locally
- writes decisions and state locally

## Main entrypoints
### One paper cycle
```bash
python3 paper_cycle.py
```
Uses `multi_snapshot.json` by default.

### Repeating paper loop
```bash
python3 paper_loop.py --input multi_snapshot.json --interval-sec 60 --iterations 3
```

### Live public-data paper loop
```bash
python3 paper_loop.py --live --interval-sec 60 --iterations 3
```

## Outputs
- `decisions.csv`
- `trades.csv`
- `daily_stats.csv`
- `state.json`

## Notes
- no live orders
- no exchange credentials required for paper mode
- intended as Bobby-native base for loop / connector / risk hardening work
