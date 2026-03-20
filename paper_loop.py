from __future__ import annotations

import argparse
import time

try:
    from .agent import DEFAULT_CONFIG_PATH, BobbyAxelrodAgent
    from .runner import BobbyReadiness, BobbyRunnerSummary, load_payloads
except ImportError:
    from agent import DEFAULT_CONFIG_PATH, BobbyAxelrodAgent
    from runner import BobbyReadiness, BobbyRunnerSummary, load_payloads


def run_cycle(agent: BobbyAxelrodAgent, input_path: str, cycle_no: int) -> None:
    decisions = agent.evaluate_many(load_payloads(input_path))

    print(f"=== CYCLE {cycle_no} ===")
    for decision in decisions:
        print(agent.print_console_report(decision))
    print(BobbyRunnerSummary.build(decisions, agent.state))
    print(BobbyReadiness.build(decisions, agent.state))


def main() -> None:
    parser = argparse.ArgumentParser(description="Bobby repeating paper loop runner")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to config.json")
    parser.add_argument("--input", required=True, help="Path to JSON snapshots")
    parser.add_argument("--interval-sec", type=float, default=60.0, help="Seconds to wait between cycles")
    parser.add_argument("--iterations", type=int, default=0, help="How many cycles to run; 0 means forever")
    args = parser.parse_args()

    if args.interval_sec < 0:
        raise ValueError("--interval-sec must be non-negative")
    if args.iterations < 0:
        raise ValueError("--iterations must be non-negative")

    agent = BobbyAxelrodAgent(args.config)
    cycle_no = 0

    while True:
        cycle_no += 1
        run_cycle(
            agent,
            args.input,
            cycle_no,
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
interval-sec must be non-negative")
    if args.iterations < 0:
        raise ValueError("--iterations must be non-negative")

    agent = BobbyAxelrodAgent(args.config)
    cycle_no = 0

    while True:
        cycle_no += 1
        run_cycle(agent, args.input, cycle_no)
        if args.iterations and cycle_no >= args.iterations:
            break
        if args.interval_sec > 0:
            time.sleep(args.interval_sec)


if __name__ == "__main__":
    main()
