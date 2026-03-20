from __future__ import annotations

import argparse

try:
    from .agent import DEFAULT_CONFIG_PATH
    from .runner import BobbyReadiness, BobbyRunnerSummary, load_payloads
    from .agent import BobbyAxelrodAgent
except ImportError:
    from agent import DEFAULT_CONFIG_PATH, BobbyAxelrodAgent
    from runner import BobbyReadiness, BobbyRunnerSummary, load_payloads


def main() -> None:
    parser = argparse.ArgumentParser(description="Bobby final paper-ready cycle")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to config.json")
    parser.add_argument("--input", help="Path to JSON snapshots")
    parser.add_argument("--live", action="store_true", help="Fetch live Binance snapshots for one cycle")
    parser.add_argument("--candles-limit", type=int, default=50, help="How many candles to fetch in live mode")
    parser.add_argument("--timeout-sec", type=float, default=5.0, help="HTTP timeout for live mode")
    args = parser.parse_args()

    agent = BobbyAxelrodAgent(args.config)
    if args.live:
        payloads = agent.market_data.fetch_live_snapshots(
            symbols=agent.config["symbols"],
            timeframe=agent.config["timeframe"],
            candles_limit=args.candles_limit,
            timeout_sec=args.timeout_sec,
        )
    else:
        if not args.input:
            raise ValueError("--input is required unless --live is set")
        payloads = load_payloads(args.input)
    decisions = agent.evaluate_many(payloads)

    print("=== DECISIONS ===")
    for decision in decisions:
        print(agent.print_console_report(decision))
    print("=== SUMMARY ===")
    print(BobbyRunnerSummary.build(decisions, agent.state))
    print("=== READINESS ===")
    print(BobbyReadiness.build(decisions, agent.state))


if __name__ == "__main__":
    main()
