from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .agent import BobbyAxelrodAgent, DEFAULT_CONFIG_PATH
except ImportError:
    from agent import BobbyAxelrodAgent, DEFAULT_CONFIG_PATH


class BobbyRunnerSummary:
    @staticmethod
    def stats(decisions: list) -> dict:
        economics_blocked = []
        exchange_filter_blocked = []
        market_regime_blocked = []
        risk_blocked = []
        other_blocked = []
        for decision in decisions:
            if decision.state == "GRID_READY":
                continue
            reason = (decision.reason or "").lower()
            if "economics infeasible" in reason or "per-level notional below minimum threshold" in reason:
                economics_blocked.append(decision.symbol)
            elif "quantity became zero after rounding" in reason:
                exchange_filter_blocked.append(decision.symbol)
            elif "risk lock" in reason:
                risk_blocked.append(decision.symbol)
            elif "atr below threshold" in reason or "spread too wide" in reason or "structure too imbalanced" in reason or "price too far from range mid" in reason:
                market_regime_blocked.append(decision.symbol)
            else:
                other_blocked.append(decision.symbol)
        return {
            "scan_total": len(decisions),
            "grid_ready": sum(1 for d in decisions if d.state == "GRID_READY"),
            "no_trade": sum(1 for d in decisions if d.state == "NO_TRADE"),
            "daily_lock": sum(1 for d in decisions if d.state == "DAILY_LOCK"),
            "ready_symbols": [d.symbol for d in decisions if d.state == "GRID_READY"],
            "blocked_symbols": [d.symbol for d in decisions if d.state != "GRID_READY"],
            "economics_blocked_symbols": economics_blocked,
            "exchange_filter_blocked_symbols": exchange_filter_blocked,
            "market_regime_blocked_symbols": market_regime_blocked,
            "risk_blocked_symbols": risk_blocked,
            "other_blocked_symbols": other_blocked,
        }

    @classmethod
    def build(cls, decisions: list, state: dict) -> str:
        stats = cls.stats(decisions)
        paper = state.get("paper_summary", {})
        return " | ".join([
            f"scan_total={stats['scan_total']}",
            f"grid_ready={stats['grid_ready']}",
            f"no_trade={stats['no_trade']}",
            f"daily_lock={stats['daily_lock']}",
            f"ready_symbols={','.join(stats['ready_symbols']) if stats['ready_symbols'] else '-'}",
            f"blocked_symbols={','.join(stats['blocked_symbols']) if stats['blocked_symbols'] else '-'}",
            f"economics_blocked={','.join(stats['economics_blocked_symbols']) if stats['economics_blocked_symbols'] else '-'}",
            f"exchange_filter_blocked={','.join(stats['exchange_filter_blocked_symbols']) if stats['exchange_filter_blocked_symbols'] else '-'}",
            f"market_regime_blocked={','.join(stats['market_regime_blocked_symbols']) if stats['market_regime_blocked_symbols'] else '-'}",
            f"paper_side={paper.get('inventory_side', 'FLAT')}",
            f"realized={paper.get('realized_pnl_usd', 0.0)}",
            f"unrealized={paper.get('unrealized_pnl_usd', 0.0)}",
            f"fills={paper.get('fills_count', 0)}",
        ])


class BobbyReadiness:
    @staticmethod
    def build(decisions: list, state: dict) -> str:
        stats = BobbyRunnerSummary.stats(decisions)
        paper = state.get("paper_summary", {})
        blockers: list[str] = []
        if stats["scan_total"] == 0:
            blockers.append("no_snapshots")
        if stats["grid_ready"] == 0:
            blockers.append("no_ready_symbols")
        if stats["daily_lock"] > 0 or state.get("lock_status"):
            blockers.append("risk_lock")
        if state.get("open_positions", 0) > 1:
            blockers.append("position_limit_breach")
        if stats["grid_ready"] == 0 and stats["economics_blocked_symbols"]:
            blockers.append("economics_constraints")

        ready = len(blockers) == 0
        mode = "PAPER_READY" if ready else "PAPER_WAIT"
        return " | ".join([
            f"readiness={mode}",
            f"ready_symbols={','.join(stats['ready_symbols']) if stats['ready_symbols'] else '-'}",
            f"blockers={','.join(blockers) if blockers else '-'}",
            f"paper_side={paper.get('inventory_side', 'FLAT')}",
            f"fills={paper.get('fills_count', 0)}",
        ])


def load_payloads(path: str) -> list:
    payloads = json.loads(Path(path).read_text())
    if isinstance(payloads, dict) and "snapshots" in payloads:
        payloads = payloads["snapshots"]
    if not isinstance(payloads, list):
        raise ValueError("Runner input must be a JSON array of snapshots")
    return payloads


def main() -> None:
    parser = argparse.ArgumentParser(description="Bobby multi-symbol paper runner")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to config.json")
    parser.add_argument("--input", required=True, help="Path to JSON array of market snapshots")
    parser.add_argument("--summary-only", action="store_true", help="Print summary only")
    parser.add_argument("--with-readiness", action="store_true", help="Also print readiness line")
    args = parser.parse_args()

    agent = BobbyAxelrodAgent(args.config)
    decisions = agent.evaluate_many(load_payloads(args.input))
    if not args.summary_only:
        for decision in decisions:
            print(agent.print_console_report(decision))
    print(BobbyRunnerSummary.build(decisions, agent.state))
    if args.with_readiness:
        print(BobbyReadiness.build(decisions, agent.state))


if __name__ == "__main__":
    main()
