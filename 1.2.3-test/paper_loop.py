from __future__ import annotations

import argparse
import time

try:
    from .agent import DEFAULT_CONFIG_PATH, BobbyAxelrodAgent
    from .runner import BobbyReadiness, BobbyRunnerSummary, load_payloads
except ImportError:
    from agent import DEFAULT_CONFIG_PATH, BobbyAxelrodAgent
    from runner import BobbyReadiness, BobbyRunnerSummary, load_payloads


def run_cycle(
    agent: BobbyAxelrodAgent,
    cycle_no: int,
    input_path: str | None = None,
    *,
    live: bool = False,
    candles_limit: int = 50,
    timeout_sec: float = 5.0,
) -> None:
    if live:
        payloads = agent.market_data.fetch_live_snapshots(
            symbols=agent.config["symbols"],
            timeframe=agent.config["timeframe"],
            candles_limit=candles_limit,
            timeout_sec=timeout_sec,
        )
    else:
        if not input_path:
            raise ValueError("input_path is required unless live mode is enabled")
        payloads = load_payloads(input_path)

    decisions = agent.evaluate_many(payloads)

    print(f"=== CYCLE {cycle_no} ===")
    for decision in decisions:
        print(agent.print_console_report(decision))
    print(BobbyRunnerSummary.build(decisions, agent.state))
    print(BobbyReadiness.build(decisions, agent.state))


def main() -> None:
    parser = argparse.ArgumentParser(description="Bobby repeating paper loop runner")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to config.json")
    parser.add_argument("--input", help="Path to JSON snapshots")
    parser.add_argument("--live", action="store_true", help="Fetch live Binance snapshots each cycle")
    parser.add_argument("--interval-sec", type=float, default=60.0, help="Seconds to wait between cycles")
    parser.add_argument("--iterations", type=int, default=0, help="How many cycles to run; 0 means forever")
    parser.add_argument("--candles-limit", type=int, default=50, help="How many candles to fetch in live mode")
    parser.add_argument("--timeout-sec", type=float, default=5.0, help="HTTP timeout for live mode")
    args = parser.parse_args()

    if args.interval_sec < 0:
        raise ValueError("--interval-sec must be non-negative")
    if args.iterations < 0:
        raise ValueError("--iterations must be non-negative")
    if args.candles_limit < 20:
        raise ValueError("--candles-limit must be >= 20")
    if not args.live and not args.input:
        raise ValueError("--input is required unless --live is set")

    agent = BobbyAxelrodAgent(args.config)
    cycle_no = 0

    while True:
        cycle_no += 1
        run_cycle(
            agent,
            cycle_no,
            input_path=args.input,
            live=args.live,
            candles_limit=args.candles_limit,
            timeout_sec=args.timeout_sec,
        )
        if args.iterations and cycle_no >= args.iterations:
            break
        if args.interval_sec > 0:
            time.sleep(args.interval_sec)


if __name__ == "__main__":
    main()
