from __future__ import annotations

from dataclasses import dataclass

try:
    from .market_data import Candle
except ImportError:
    from market_data import Candle


@dataclass(slots=True)
class FillEvent:
    time: str
    symbol: str
    side: str
    price: float
    qty: float
    pnl_usd: float
    note: str


class PaperExecutionSimulator:
    def sync_state(self, state: dict) -> dict:
        paper = state.setdefault("paper", {})
        paper.setdefault("inventory", {"side": "FLAT", "qty": 0.0, "avg_entry": 0.0})
        paper.setdefault("realized_pnl_usd", 0.0)
        paper.setdefault("unrealized_pnl_usd", 0.0)
        paper.setdefault("fills_count", 0)
        paper.setdefault("last_fill_time", "")
        paper.setdefault("last_realized_pnl_usd", 0.0)
        paper.setdefault("last_event", "")
        state.setdefault("loss_streak", 0)
        state.setdefault("open_positions", 0)
        return state

    def simulate_candle(self, symbol: str, candle: Candle, active_grid: dict | None, state: dict) -> list[FillEvent]:
        self.sync_state(state)
        state["paper"]["last_realized_pnl_usd"] = 0.0
        state["paper"]["last_event"] = "mark_only"

        if not active_grid:
            self._mark_unrealized(state, candle.close)
            return []

        invalidation = float(active_grid.get("invalidation", 0.0))
        if invalidation > 0 and self._hit_invalidation(active_grid.get("regime"), invalidation, candle):
            fill = self._force_flatten(symbol, candle.timestamp, invalidation, state, note="grid invalidation")
            self._mark_unrealized(state, candle.close)
            return [fill] if fill else []

        fills: list[FillEvent] = []
        regime = active_grid.get("regime")
        spacing = float(active_grid.get("spacing", 0.0))
        levels = int(active_grid.get("levels", 0))
        qty = float(active_grid.get("qty_per_level", 0.0))
        center = float(active_grid.get("center", 0.0))
        if min(spacing, qty, center) <= 0 or levels <= 0:
            self._mark_unrealized(state, candle.close)
            return []

        level_prices = self._level_prices(regime, center, spacing, levels)
        for side, price in level_prices:
            if candle.low <= price <= candle.high:
                fill = self._process_fill(symbol, candle.timestamp, side, price, qty, state)
                if fill:
                    fills.append(fill)

        self._mark_unrealized(state, candle.close)
        return fills

    @staticmethod
    def _hit_invalidation(regime: str | None, invalidation: float, candle: Candle) -> bool:
        if regime == "LONG_GRID":
            return candle.low <= invalidation
        if regime == "SHORT_GRID":
            return candle.high >= invalidation
        return candle.low <= invalidation or candle.high >= invalidation

    def _level_prices(self, regime: str, center: float, spacing: float, levels: int) -> list[tuple[str, float]]:
        prices: list[tuple[str, float]] = []
        if regime == "LONG_GRID":
            for i in range(1, levels + 1):
                prices.append(("BUY", center - spacing * i))
        elif regime == "SHORT_GRID":
            for i in range(1, levels + 1):
                prices.append(("SELL", center + spacing * i))
        else:
            half = max(1, levels // 2)
            for i in range(1, half + 1):
                prices.append(("BUY", center - spacing * i))
                prices.append(("SELL", center + spacing * i))
        return prices

    def _force_flatten(self, symbol: str, time: str, price: float, state: dict, note: str) -> FillEvent | None:
        inv = state["paper"]["inventory"]
        current_side = inv["side"]
        current_qty = float(inv["qty"])
        avg_entry = float(inv["avg_entry"])
        if current_side == "FLAT" or current_qty <= 0:
            state["paper"]["last_event"] = note + ": no inventory"
            return None

        if current_side == "LONG":
            realized = (price - avg_entry) * current_qty
            side = "SELL"
        else:
            realized = (avg_entry - price) * current_qty
            side = "BUY"

        inv.update({"side": "FLAT", "qty": 0.0, "avg_entry": 0.0})
        self._apply_realized_result(state, realized, time, note)
        return FillEvent(time=time, symbol=symbol, side=side, price=round(price, 8), qty=current_qty, pnl_usd=round(realized, 8), note=note)

    def _process_fill(self, symbol: str, time: str, side: str, price: float, qty: float, state: dict) -> FillEvent | None:
        inv = state["paper"]["inventory"]
        current_side = inv["side"]
        current_qty = float(inv["qty"])
        avg_entry = float(inv["avg_entry"])
        realized = 0.0
        note = ""

        if side == "BUY":
            if current_side in {"FLAT", "LONG"}:
                new_qty = current_qty + qty
                new_avg = ((avg_entry * current_qty) + (price * qty)) / new_qty if new_qty else 0.0
                inv.update({"side": "LONG", "qty": round(new_qty, 8), "avg_entry": new_avg})
                note = "grid long add"
            else:
                close_qty = min(current_qty, qty)
                realized = (avg_entry - price) * close_qty
                remaining = current_qty - close_qty
                if remaining > 0:
                    inv.update({"side": "SHORT", "qty": round(remaining, 8), "avg_entry": avg_entry})
                else:
                    inv.update({"side": "FLAT", "qty": 0.0, "avg_entry": 0.0})
                note = "short cover"
        else:
            if current_side in {"FLAT", "SHORT"}:
                new_qty = current_qty + qty
                new_avg = ((avg_entry * current_qty) + (price * qty)) / new_qty if new_qty else 0.0
                inv.update({"side": "SHORT", "qty": round(new_qty, 8), "avg_entry": new_avg})
                note = "grid short add"
            else:
                close_qty = min(current_qty, qty)
                realized = (price - avg_entry) * close_qty
                remaining = current_qty - close_qty
                if remaining > 0:
                    inv.update({"side": "LONG", "qty": round(remaining, 8), "avg_entry": avg_entry})
                else:
                    inv.update({"side": "FLAT", "qty": 0.0, "avg_entry": 0.0})
                note = "long reduce"

        self._apply_realized_result(state, realized, time, note)
        return FillEvent(time=time, symbol=symbol, side=side, price=round(price, 8), qty=qty, pnl_usd=round(realized, 8), note=note)

    def _apply_realized_result(self, state: dict, realized: float, time: str, note: str) -> None:
        state["paper"]["realized_pnl_usd"] = round(float(state["paper"].get("realized_pnl_usd", 0.0)) + realized, 8)
        state["paper"]["last_realized_pnl_usd"] = round(realized, 8)
        state["paper"]["fills_count"] = int(state["paper"].get("fills_count", 0)) + 1
        state["paper"]["last_fill_time"] = time
        state["paper"]["last_event"] = note
        if realized < 0:
            state["loss_streak"] = int(state.get("loss_streak", 0)) + 1
        elif realized > 0:
            state["loss_streak"] = 0
        state["daily_pnl_usd"] = round(state["paper"]["realized_pnl_usd"] + float(state["paper"].get("unrealized_pnl_usd", 0.0)), 8)
        state["open_positions"] = 0 if state["paper"]["inventory"]["side"] == "FLAT" else 1

    def _mark_unrealized(self, state: dict, mark_price: float) -> None:
        inv = state["paper"]["inventory"]
        qty = float(inv["qty"])
        avg_entry = float(inv["avg_entry"])
        side = inv["side"]
        if side == "LONG":
            unrealized = (mark_price - avg_entry) * qty
        elif side == "SHORT":
            unrealized = (avg_entry - mark_price) * qty
        else:
            unrealized = 0.0
        state["paper"]["unrealized_pnl_usd"] = round(unrealized, 8)
        state["daily_pnl_usd"] = round(float(state["paper"].get("realized_pnl_usd", 0.0)) + unrealized, 8)
        state["open_positions"] = 0 if side == "FLAT" or qty <= 0 else 1
