from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Optional

try:
    from .market_data import Candle, MarketSnapshot
    from .risk import GridPlan, RiskEngine
except ImportError:
    from market_data import Candle, MarketSnapshot
    from risk import GridPlan, RiskEngine


@dataclass(slots=True)
class Decision:
    time: str
    symbol: str
    state: str
    regime: str
    confidence: str
    reason: str
    grid_plan: Optional[GridPlan]


class GridStrategy:
    def __init__(self, config: dict, risk_engine: RiskEngine):
        self.config = config
        self.risk_engine = risk_engine

    def evaluate(self, snapshot: MarketSnapshot, state: dict) -> Decision:
        if snapshot.symbol not in set(self.config["symbols"]):
            return Decision(snapshot.candles[-1].timestamp, snapshot.symbol, "NO_TRADE", "NEUTRAL_GRID", "LOW", "Symbol not in watchlist.", None)

        if self.risk_engine.should_lock(
            float(state.get("daily_pnl_usd", 0.0)),
            int(state.get("loss_streak", 0)),
            int(state.get("open_positions", 0)),
        ):
            return Decision(snapshot.candles[-1].timestamp, snapshot.symbol, "DAILY_LOCK", "LOCKED", "LOW", "Risk lock triggered.", None)

        candles = snapshot.candles
        atr = self._atr(candles, self.config["atr_period"])
        atr_pct = atr / snapshot.last_price if snapshot.last_price else 0.0
        if atr_pct < self.config["min_atr_pct"]:
            return Decision(snapshot.candles[-1].timestamp, snapshot.symbol, "NO_TRADE", "NEUTRAL_GRID", "LOW", "ATR below threshold.", None)
        if snapshot.spread_bps > self.config["max_spread_bps"]:
            return Decision(snapshot.candles[-1].timestamp, snapshot.symbol, "NO_TRADE", "NEUTRAL_GRID", "LOW", "Spread too wide.", None)

        regime = self._classify_regime(candles)
        if regime == "NO_TRADE":
            return Decision(snapshot.candles[-1].timestamp, snapshot.symbol, "NO_TRADE", "NEUTRAL_GRID", "LOW", "Structure too imbalanced for grid deployment.", None)

        midline = self._midline(candles[-self.config["regime_window"]:])
        deviation_pct = abs(snapshot.mark_price - midline) / midline if midline else 0.0
        if deviation_pct > self.config["max_deviation_from_mid_pct"] and regime == "NEUTRAL_GRID":
            return Decision(snapshot.candles[-1].timestamp, snapshot.symbol, "NO_TRADE", regime, "LOW", "Price too far from range mid for neutral grid.", None)

        spacing = max(
            atr * self.config["grid_spacing_atr"],
            snapshot.last_price * self.config["min_grid_spacing_pct"],
        )
        try:
            plan = self.risk_engine.build_grid_plan(snapshot.symbol, regime, snapshot.mark_price, spacing, int(self.config["grid_levels"]))
        except ValueError as exc:
            return Decision(snapshot.candles[-1].timestamp, snapshot.symbol, "NO_TRADE", regime, "LOW", str(exc), None)

        return Decision(
            snapshot.candles[-1].timestamp,
            snapshot.symbol,
            "GRID_READY",
            regime,
            plan.confidence,
            self._reason(regime, candles, atr_pct),
            plan,
        )

    def _classify_regime(self, candles: list[Candle]) -> str:
        window = candles[-self.config["regime_window"]:]
        closes = [c.close for c in window]
        highs = [c.high for c in window]
        lows = [c.low for c in window]
        slope_window = closes[-self.config["trend_slope_window"]:]
        slope = (slope_window[-1] - slope_window[0]) / slope_window[0] if slope_window[0] else 0.0
        total_range = max(highs) - min(lows)
        directional_move = abs(closes[-1] - closes[0])
        bias_ratio = directional_move / total_range if total_range > 0 else 0.0

        pullback_high = max(c.high for c in candles[-self.config["pullback_lookback"]:])
        pullback_low = min(c.low for c in candles[-self.config["pullback_lookback"]:])
        last_close = closes[-1]

        if abs(slope) <= self.config["range_bias_threshold"] and bias_ratio <= self.config["neutral_bias_ratio_max"]:
            return "NEUTRAL_GRID"
        if slope > self.config["range_bias_threshold"] and last_close < pullback_high:
            return "LONG_GRID"
        if slope < -self.config["range_bias_threshold"] and last_close > pullback_low:
            return "SHORT_GRID"
        return "NO_TRADE"

    @staticmethod
    def _atr(candles: list[Candle], period: int) -> float:
        recent = candles[-(period + 1):]
        true_ranges = []
        for prev, current in zip(recent, recent[1:]):
            true_ranges.append(max(current.high - current.low, abs(current.high - prev.close), abs(current.low - prev.close)))
        return mean(true_ranges) if true_ranges else 0.0

    @staticmethod
    def _midline(candles: list[Candle]) -> float:
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        return (max(highs) + min(lows)) / 2

    @staticmethod
    def _reason(regime: str, candles: list[Candle], atr_pct: float) -> str:
        closes = [c.close for c in candles[-5:]]
        drift = closes[-1] - closes[0]
        if regime == "LONG_GRID":
            return f"Trend up, pullback intact, ATR%={atr_pct:.4f}, drift={drift:.2f}."
        if regime == "SHORT_GRID":
            return f"Trend down, rebound intact, ATR%={atr_pct:.4f}, drift={drift:.2f}."
        return f"Range structure detected, ATR%={atr_pct:.4f}, drift={drift:.2f}."
