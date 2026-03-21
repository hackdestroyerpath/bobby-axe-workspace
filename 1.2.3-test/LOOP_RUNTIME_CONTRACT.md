# LOOP_RUNTIME_CONTRACT.md

## Purpose
Operational contract for Bobby repeating paper loop and its shell runtime wrapper.

## Runtime entrypoints

### Python loop
```bash
python3 paper_loop.py --input multi_snapshot.json --interval-sec 60 --iterations 3
```

### Live public-data loop
```bash
python3 paper_loop.py --config config.json --live --interval-sec 60 --iterations 0 --candles-limit 50 --timeout-sec 10
```

### Shell wrapper for durable runtime
```bash
./run_bobby_live_loop.sh
```

## Input contract

### Static input mode
- `paper_loop.py --input <json>` expects a JSON payload file readable by `runner.load_payloads(...)`.
- File must contain snapshot payloads for configured symbols.
- Used for deterministic local tests and offline regression checks.

### Live mode
- `paper_loop.py --live` ignores `--input` and fetches public Binance snapshots through `agent.market_data.fetch_live_snapshots(...)`.
- Symbols come from `config.json` -> `symbols`.
- Timeframe comes from `config.json` -> `timeframe`.
- `--candles-limit` must be `>= 20`.
- `--timeout-sec` controls HTTP timeout for public market-data fetches.

## Cycle contract
For each cycle the loop must:
1. obtain payloads from static input or live fetch
2. run `agent.evaluate_many(payloads)`
3. print one console report per decision
4. print runner summary
5. print readiness line

Console markers:
- `=== CYCLE N ===`
- per-symbol decision report
- `BobbyRunnerSummary.build(...)`
- `BobbyReadiness.build(...)`

## Persistence contract
Core runtime writes remain local:
- `decisions.csv`
- `trades.csv`
- `daily_stats.csv`
- `state.json`

## Shell wrapper contract
`run_bobby_live_loop.sh` is the preferred runtime wrapper for unattended local execution.

### Environment overrides
- `PYTHON_BIN` default: `python3`
- `BOBBY_INTERVAL_SEC` default: `60`
- `BOBBY_CANDLES_LIMIT` default: `50`
- `BOBBY_TIMEOUT_SEC` default: `10`
- `BOBBY_ITERATIONS` default: `0` (run forever)
- `BOBBY_CONFIG_PATH` default: `<repo>/config.json`

### Runtime artifacts
Wrapper creates:
- log file: `tmp/runtime_logs/bobby_live_loop.log`
- status file: `tmp/runtime_logs/bobby_live_loop.status`

Status file fields during startup/running/stopped include:
- `status`
- `started_at`
- `stopped_at` or `last_launch_at`
- `pid`
- `exit_code` on stop
- `config`
- `interval_sec`
- `candles_limit`
- `timeout_sec`
- `iterations`
- `log_file`

## Safe stop contract
- Wrapper uses `trap cleanup EXIT`.
- On normal exit or signal-triggered shell exit, status file is rewritten to `status=stopped` with `exit_code` and `stopped_at`.
- Infinite mode is `--iterations 0`; bounded mode stops after requested cycle count.

## Operational policy
- Paper only; no live order placement.
- No exchange credentials required for public-data loop.
- Preferred automation path: system cron/systemd/supervisor launches `run_bobby_live_loop.sh`, not direct ad hoc shell history.
- If BTCUSDC fails economics/regime checks, runtime should skip rather than force a bad grid.

## Minimum acceptance check
```bash
BOBBY_ITERATIONS=1 ./run_bobby_live_loop.sh && tail -n 50 tmp/runtime_logs/bobby_live_loop.log && cat tmp/runtime_logs/bobby_live_loop.status
```

Expected result:
- one completed live cycle
- summary and readiness printed to log
- status file ends in `status=stopped` with `exit_code=0`
