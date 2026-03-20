# Imported from hackdestroyerpath/MAXIMUS

Imported on: 2026-03-20
Source: https://github.com/hackdestroyerpath/MAXIMUS

## Applied to Bobby
- Supervisory relationship preserved: MAXIMUS is Bobby's chief.
- Market scope alignment preserved: Binance USDC futures.
- Timeframe reference preserved: 1m.
- Symbols imported as preferred watchlist: BTCUSDC, ETHUSDC.
- Execution mode preserved: paper-only.
- Execution preference imported: maker-only where applicable.
- Risk posture references imported:
  - deposit reference: 30 USD
  - leverage reference: 10x
  - risk per trade reference: 2%
  - max daily loss reference: 6%
  - max consecutive losses reference: 3
  - max open positions reference: 1
- Operational preference imported: keep state/journal outputs explicit.
- Tooling preference imported: prefer thin in-house gateway over opaque all-in-one SDKs.
- Environment rule imported: separate research, paper, and future live configs.

## Not Applied Blindly
These items were intentionally not adopted as direct operating rules because they conflict with Bobby's current mission or architecture:
- MAXIMUS identity/persona takeover
- breakout/retest scalping strategy logic
- non-grid execution logic
- any assumptions that would override Bobby's paper-only grid mandate
- any secret or credential material

## Next Integration Candidate
If requested, create a Bobby-native `config.json` that maps the imported risk references into grid-specific parameters instead of scalping parameters.
