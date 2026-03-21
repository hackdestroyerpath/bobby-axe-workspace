# TOOLS.md — Bobby Tool Notes

## Purpose
Operational notes for the Bobby stack.

## Expected Components
- market data adapter
- grid strategy engine
- risk engine
- journal
- Telegram notifier
- loop runner
- thin in-house execution/paper gateway preference over opaque all-in-one SDKs

## Imported Stack Notes
- Preferred symbols from imported MAXIMUS stack: BTCUSDC, ETHUSDC.
- Keep research, paper, and any future live environment configs separated.
- Prefer storing credential references/paths only, never raw secrets.
- Maker-first execution preference where the strategy remains valid.
- Binance API is expected to be a frequent core integration path for Bobby.
- When using Binance trading constraints, prefer live `exchangeInfo` filters over static hardcoded symbol precision.

## Secret Policy
- Never store bot tokens or API secrets here.
- Use .env for local secrets.
