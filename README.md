# Bobby Axelrod v1

Paper-only grid decision agent for Binance USDC futures.

## Scope
- USDC futures only
- 1m timeframe
- auto regime selection: `LONG_GRID`, `SHORT_GRID`, `NEUTRAL_GRID`
- paper mode only
- risk-first deployment

## Current logic
- validates snapshot integrity
- blocks on spread and volatility filters
- classifies market into long / short / neutral grid regimes
- rejects imbalanced structures instead of forcing a grid
- builds a bounded grid plan with spacing, levels, quantity, and invalidation
- writes decisions and state locally

## Run
```bash
python3 agent.py --input sample_snapshot.json
```

## Outputs
- `decisions.csv`
- `trades.csv`
- `daily_stats.csv`
- `state.json`

## Notes
- no live orders
- no API keys required
- intended as Bobby-native base for further runner/integration work
