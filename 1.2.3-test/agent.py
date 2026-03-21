from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from .binance_exchange import load_symbol_filters
    from .grid_strategy import Decision, GridStrategy
    from .journal import DEFAULT_STATE, Journal
    from .market_data import MarketDataClient
    from .risk import build_risk_engine
    from .simulator import PaperExecutionSimulator
except ImportError:
    from binance_exchange import load_symbol_filters
    from grid_strategy import Decision, GridStrategy
    from journal import DEFAULT_STATE, Journal
    from market_data import MarketDataClient
    from risk import build_risk_engine
    from simulator import PaperExecutionSimulator

DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")


class BobbyAxelrodAgent:
    def __init__(self, config_path: Path | str = DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.config = json.loads(self.config_path.read_text())
        self.config["symbol_overrides"] = load_symbol_filters(self.config, self.config_path)
        self.market_data = MarketDataClient()
        self.risk_engine = build_risk_engine(self.config)
        self.strategy = GridStrategy(self.config, self.risk_engine)
        self.journal = Journal(self.config["paths"])
        self.state = self.journal.load_state(DEFAULT_STATE)
        self.simulator = PaperExecutionSimulator()
        self.state = self.simulator.sync_state(self.state)

    def evaluate_snapshot(self, payload: Mapping[str, Any]) -> Decision:
        snapshot = self.market_data.build_snapshot(
            symbol=payload["symbol"],
            candles=payload["candles"],
            bid=float(payload["bid"]),
            ask=float(payload["ask"]),
            last_price=float(payload["last_price"]),
            mark_price=float(payload.get("mark_price", payload["last_price"])),
        )

        fills = self.simulator.simulate_candle(
            symbol=snapshot.symbol,
            candle=snapshot.candles[-1],
            active_grid=self._active_grid_for_symbol(snapshot.symbol),
            state=self.state,
        )
        for fill in fills:
            self.journal.log_trade({
                "time": fill.time,
                "symbol": fill.symbol,
                "side": fill.side,
                "price": fill.price,
                "qty": fill.qty,
                "pnl_usd": fill.pnl_usd,
                "note": fill.note,
            })

        decision = self.strategy.evaluate(snapshot, self.state)
        self._update_state(decision)
        self.journal.log_decision(self._decision_row(decision))
        self.journal.save_state(self.state)
        return decision

    def evaluate_many(self, payloads: list[Mapping[str, Any]]) -> list[Decision]:
        decisions: list[Decision] = []
        cycle = []
        for payload in payloads:
            decision = self.evaluate_snapshot(payload)
            decisions.append(decision)
            cycle.append({
                "symbol": decision.symbol,
                "state": decision.state,
                "regime": decision.regime,
                "confidence": decision.confidence,
                "reason": decision.reason,
            })
        self.state["last_scan"] = cycle
        self.state["scan_count"] = int(self.state.get("scan_count", 0)) + 1
        self.journal.save_state(self.state)
        return decisions

    def _update_state(self, decision: Decision) -> None:
        self.state["date"] = decision.time.split("T")[0] if "T" in decision.time else decision.time[:10]
        self.state["state"] = decision.state
        self.state["symbol_in_focus"] = decision.symbol
        self.state["last_regime"] = decision.regime
        self.state["lock_status"] = decision.state == "DAILY_LOCK"
        self.state["decision_count"] = int(self.state.get("decision_count", 0)) + 1
        self.state["last_processed_symbol"] = decision.symbol
        self.state["last_cycle_time"] = decision.time
        self._apply_decision_state(decision)
        self._refresh_symbol_decision(decision)
        self._refresh_paper_summary()

    def _apply_decision_state(self, decision: Decision) -> None:
        inventory = self.state.get("paper", {}).get("inventory", {})
        inventory_side = inventory.get("side", "FLAT")
        inventory_qty = float(inventory.get("qty", 0.0) or 0.0)
        has_inventory = inventory_side != "FLAT" and inventory_qty > 0
        active_grids = self.state.setdefault("active_grids", {})
        active_grid = self.state.get("active_grid")
        active_grid_symbol = active_grid.get("symbol") if isinstance(active_grid, dict) else None

        if decision.state == "DAILY_LOCK":
            active_grids.clear()
            self._sync_active_grid_pointer(preferred_symbol=decision.symbol)
            return

        if decision.grid_plan:
            if has_inventory and active_grid_symbol and active_grid_symbol != decision.symbol:
                self._sync_active_grid_pointer(preferred_symbol=decision.symbol)
                return
            previous = active_grids.get(decision.symbol, {}) if isinstance(active_grids.get(decision.symbol), dict) else {}
            grid_state = {
                "symbol": decision.symbol,
                "regime": decision.grid_plan.regime,
                "center": decision.grid_plan.center_price,
                "lower": decision.grid_plan.lower_bound,
                "upper": decision.grid_plan.upper_bound,
                "spacing": decision.grid_plan.grid_spacing,
                "levels": decision.grid_plan.levels,
                "qty_per_level": decision.grid_plan.quantity_per_level,
                "invalidation": decision.grid_plan.invalidation_price,
                "take_profit": decision.grid_plan.take_profit_price,
                "stop_loss": decision.grid_plan.stop_loss_price,
                "exit_after_bars": decision.grid_plan.exit_after_bars,
                "age_bars": int(previous.get("age_bars", 0)) if previous else 0,
            }
            active_grids[decision.symbol] = grid_state
            self._sync_active_grid_pointer(preferred_symbol=decision.symbol)
            return

        if decision.state == "NO_TRADE":
            if not has_inventory:
                active_grids.pop(decision.symbol, None)
            elif active_grid_symbol == decision.symbol:
                active_grids.pop(decision.symbol, None)
            self._sync_active_grid_pointer(preferred_symbol=decision.symbol)

    def _sync_active_grid_pointer(self, preferred_symbol: str | None = None) -> None:
        active_grids = self.state.get("active_grids", {})
        if not isinstance(active_grids, dict) or not active_grids:
            self.state["active_grid"] = None
            return
        if preferred_symbol and preferred_symbol in active_grids:
            self.state["active_grid"] = active_grids[preferred_symbol]
            return
        first_symbol = sorted(active_grids.keys())[0]
        self.state["active_grid"] = active_grids[first_symbol]

    def _active_grid_for_symbol(self, symbol: str) -> dict | None:
        active_grids = self.state.get("active_grids", {})
        if isinstance(active_grids, dict) and symbol in active_grids:
            return active_grids[symbol]
        active_grid = self.state.get("active_grid")
        if isinstance(active_grid, dict) and active_grid.get("symbol") == symbol:
            return active_grid
        return None

    def _refresh_symbol_decision(self, decision: Decision) -> None:
        per_symbol = self.state.setdefault("symbol_decisions", {})
        per_symbol[decision.symbol] = {
            "time": decision.time,
            "state": decision.state,
            "regime": decision.regime,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "blocker_type": self._classify_blocker(decision),
        }

    @staticmethod
    def _classify_blocker(decision: Decision) -> str:
        if decision.state == "GRID_READY":
            return "-"
        reason = (decision.reason or "").lower()
        if "economics infeasible" in reason or "per-level notional below minimum threshold" in reason:
            return "economics"
        if "quantity became zero after rounding" in reason:
            return "exchange_filters"
        if "risk lock" in reason:
            return "risk"
        if "atr below threshold" in reason or "spread too wide" in reason or "structure too imbalanced" in reason or "price too far from range mid" in reason:
            return "market_regime"
        return "other"

    def _refresh_paper_summary(self) -> None:
        self.state["paper_summary"] = {
            "inventory_side": self.state.get("paper", {}).get("inventory", {}).get("side", "FLAT"),
            "inventory_qty": self.state.get("paper", {}).get("inventory", {}).get("qty", 0.0),
            "avg_entry": self.state.get("paper", {}).get("inventory", {}).get("avg_entry", 0.0),
            "realized_pnl_usd": self.state.get("paper", {}).get("realized_pnl_usd", 0.0),
            "unrealized_pnl_usd": self.state.get("paper", {}).get("unrealized_pnl_usd", 0.0),
            "fills_count": self.state.get("paper", {}).get("fills_count", 0),
            "tracked_symbols": sorted(list(self.state.get("symbol_decisions", {}).keys())),
        }

    @staticmethod
    def _decision_row(decision: Decision) -> dict:
        row = {
            "time": decision.time,
            "symbol": decision.symbol,
            "state": decision.state,
            "regime": decision.regime,
            "confidence": decision.confidence,
            "reason": decision.reason,
        }
        if decision.grid_plan:
            row.update({
                "center": decision.grid_plan.center_price,
                "lower": decision.grid_plan.lower_bound,
                "upper": decision.grid_plan.upper_bound,
                "spacing": decision.grid_plan.grid_spacing,
                "levels": decision.grid_plan.levels,
                "qty_per_level": decision.grid_plan.quantity_per_level,
                "invalidation": decision.grid_plan.invalidation_price,
                "take_profit": decision.grid_plan.take_profit_price,
                "stop_loss": decision.grid_plan.stop_loss_price,
                "exit_after_bars": decision.grid_plan.exit_after_bars,
            })
        else:
            row.update({
                "center": "",
                "lower": "",
                "upper": "",
                "spacing": "",
                "levels": "",
                "qty_per_level": "",
                "invalidation": "",
                "take_profit": "",
                "stop_loss": "",
                "exit_after_bars": "",
            })
        return row

    def print_console_report(self, decision: Decision) -> str:
        paper = self.state.get("paper_summary", {})
        parts = [
            f"symbol={decision.symbol}",
            f"state={decision.state}",
            f"regime={decision.regime}",
            f"confidence={decision.confidence}",
            f"reason={decision.reason}",
            f"paper_side={paper.get('inventory_side', 'FLAT')}",
            f"paper_qty={paper.get('inventory_qty', 0.0)}",
            f"realized={paper.get('realized_pnl_usd', 0.0)}",
            f"unrealized={paper.get('unrealized_pnl_usd', 0.0)}",
            f"fills={paper.get('fills_count', 0)}",
        ]
        if decision.grid_plan:
            parts.extend([
                f"center={decision.grid_plan.center_price}",
                f"lower={decision.grid_plan.lower_bound}",
                f"upper={decision.grid_plan.upper_bound}",
                f"spacing={decision.grid_plan.grid_spacing}",
                f"levels={decision.grid_plan.levels}",
                f"qty={decision.grid_plan.quantity_per_level}",
                f"invalidation={decision.grid_plan.invalidation_price}",
                f"tp={decision.grid_plan.take_profit_price}",
                f"sl={decision.grid_plan.stop_loss_price}",
                f"exit_after_bars={decision.grid_plan.exit_after_bars}",
            ])
        return " | ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bobby Axelrod v1 paper grid agent")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to config.json")
    parser.add_argument("--input", required=True, help="Path to snapshot payload JSON")
    args = parser.parse_args()

    agent = BobbyAxelrodAgent(args.config)
    payload = json.loads(Path(args.input).read_text())
    decision = agent.evaluate_snapshot(payload)
    print(agent.print_console_report(decision))


if __name__ == "__main__":
    main()
