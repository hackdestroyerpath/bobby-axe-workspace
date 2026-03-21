from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Mapping


DEFAULT_STATE = {
    "date": "",
    "state": "IDLE",
    "symbol_in_focus": "",
    "last_regime": "NEUTRAL_GRID",
    "lock_status": False,
    "decision_count": 0,
    "daily_pnl_usd": 0.0,
    "loss_streak": 0,
    "open_positions": 0,
    "active_grid": None,
    "active_grids": {},
    "symbol_decisions": {},
    "last_scan": [],
    "scan_count": 0,
    "paper": {
        "inventory": {"symbol": "", "side": "FLAT", "qty": 0.0, "avg_entry": 0.0},
        "realized_pnl_usd": 0.0,
        "unrealized_pnl_usd": 0.0,
        "fills_count": 0,
        "last_fill_time": ""
    }
}


class Journal:
    def __init__(self, paths: Mapping[str, str]):
        self.state_path = Path(paths["state"])
        self.decisions_path = Path(paths["decisions"])
        self.trades_path = Path(paths["trades"])
        self.daily_stats_path = Path(paths["daily_stats"])
        for path in [self.state_path, self.decisions_path, self.trades_path, self.daily_stats_path]:
            path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_csv(
            self.decisions_path,
            ["time", "symbol", "state", "regime", "confidence", "center", "lower", "upper", "spacing", "levels", "qty_per_level", "invalidation", "reason"],
        )
        self._ensure_csv(self.trades_path, ["time", "symbol", "side", "price", "qty", "pnl_usd", "note"])
        self._ensure_csv(self.daily_stats_path, ["date", "decisions", "daily_pnl_usd", "loss_streak", "locked"])

    def load_state(self, default_state: Mapping[str, object] | None = None) -> dict:
        seed = json.loads(json.dumps(DEFAULT_STATE))
        if default_state:
            seed.update(default_state)
        if not self.state_path.exists():
            self.save_state(seed)
            return seed
        current = json.loads(self.state_path.read_text())
        seed.update(current)
        if "paper" in current and isinstance(current["paper"], dict):
            merged_paper = json.loads(json.dumps(DEFAULT_STATE["paper"]))
            merged_paper.update(current["paper"])
            if "inventory" in current["paper"] and isinstance(current["paper"]["inventory"], dict):
                merged_inventory = dict(DEFAULT_STATE["paper"]["inventory"])
                merged_inventory.update(current["paper"]["inventory"])
                merged_paper["inventory"] = merged_inventory
            seed["paper"] = merged_paper
        return seed

    def save_state(self, state: Mapping[str, object]) -> None:
        self.state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    def log_decision(self, row: Mapping[str, object]) -> None:
        self._append_csv(self.decisions_path, row)

    def log_trade(self, row: Mapping[str, object]) -> None:
        self._append_csv(self.trades_path, row)

    @staticmethod
    def _ensure_csv(path: Path, headers: Iterable[str]) -> None:
        if path.exists():
            return
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(headers))
            writer.writeheader()

    @staticmethod
    def _append_csv(path: Path, row: Mapping[str, object]) -> None:
        with path.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            writer.writerow(row)
