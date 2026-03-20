from __future__ import annotations

from dataclasses import dataclass, replace
import math


@dataclass(slots=True)
class RiskLimits:
    deposit_usd: float
    leverage: float
    max_exposure_pct: float
    risk_per_trade_pct: float
    max_daily_loss_pct: float
    max_consecutive_losses: int
    max_open_positions: int
    min_notional_usd: float
    qty_step: float
    price_step: float

    @property
    def max_notional_usd(self) -> float:
        return self.deposit_usd * self.leverage * self.max_exposure_pct

    @property
    def risk_budget_usd(self) -> float:
        return self.deposit_usd * self.risk_per_trade_pct

    @property
    def daily_loss_limit_usd(self) -> float:
        return self.deposit_usd * self.max_daily_loss_pct


@dataclass(slots=True)
class GridPlan:
    regime: str
    center_price: float
    lower_bound: float
    upper_bound: float
    grid_spacing: float
    levels: int
    quantity_per_level: float
    total_notional_usd: float
    invalidation_price: float
    confidence: str


class RiskEngine:
    def __init__(self, limits: RiskLimits, symbol_overrides: dict[str, dict] | None = None):
        self.limits = limits
        self.symbol_overrides = symbol_overrides or {}

    def should_lock(self, daily_pnl_usd: float, loss_streak: int, open_positions: int = 0) -> bool:
        return (
            daily_pnl_usd <= -self.limits.daily_loss_limit_usd
            or loss_streak >= self.limits.max_consecutive_losses
        )

    def at_position_limit(self, open_positions: int) -> bool:
        return open_positions >= self.limits.max_open_positions

    def build_grid_plan(self, symbol: str, regime: str, center_price: float, spacing: float, levels: int) -> GridPlan:
        limits = self._limits_for_symbol(symbol)
        if spacing <= 0:
            raise ValueError("Grid spacing must be positive")
        if levels < 2:
            raise ValueError("Grid levels must be at least 2")
        if regime not in {"LONG_GRID", "SHORT_GRID", "NEUTRAL_GRID"}:
            raise ValueError(f"Unsupported regime: {regime}")

        lower = center_price - spacing * levels
        upper = center_price + spacing * levels
        total_notional = min(limits.max_notional_usd, max(limits.min_notional_usd * levels, limits.max_notional_usd))
        level_notional = total_notional / levels
        qty = self._floor_to_step(level_notional / center_price, limits.qty_step)
        if qty <= 0:
            raise ValueError(f"Quantity became zero after rounding for {symbol}")
        if qty * center_price < limits.min_notional_usd:
            raise ValueError(f"Per-level notional below minimum threshold for {symbol}")

        total_notional_real = qty * center_price * levels
        invalidation = self._invalidation_price(regime, center_price, lower, upper, spacing)
        confidence = self._confidence(center_price, spacing)
        return GridPlan(
            regime=regime,
            center_price=self._round_price(center_price, limits.price_step),
            lower_bound=self._round_price(lower, limits.price_step),
            upper_bound=self._round_price(upper, limits.price_step),
            grid_spacing=self._round_price(spacing, limits.price_step),
            levels=levels,
            quantity_per_level=qty,
            total_notional_usd=round(total_notional_real, 4),
            invalidation_price=self._round_price(invalidation, limits.price_step),
            confidence=confidence,
        )

    def _limits_for_symbol(self, symbol: str) -> RiskLimits:
        override = self.symbol_overrides.get(symbol, {})
        if not override:
            return self.limits
        return replace(
            self.limits,
            min_notional_usd=float(override.get("min_notional_usd", self.limits.min_notional_usd)),
            qty_step=float(override.get("qty_step", self.limits.qty_step)),
            price_step=float(override.get("price_step", self.limits.price_step)),
        )

    def _invalidation_price(self, regime: str, center_price: float, lower: float, upper: float, spacing: float) -> float:
        if regime == "LONG_GRID":
            return lower - spacing
        if regime == "SHORT_GRID":
            return upper + spacing
        if center_price - lower >= upper - center_price:
            return lower - spacing
        return upper + spacing

    @staticmethod
    def _confidence(center_price: float, spacing: float) -> str:
        spacing_pct = spacing / center_price if center_price else 0.0
        if spacing_pct >= 0.0012:
            return "HIGH"
        if spacing_pct >= 0.0008:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _round_price(price: float, step: float) -> float:
        return round(round(price / step) * step, 8)

    @staticmethod
    def _floor_to_step(value: float, step: float) -> float:
        floored = math.floor(value / step) * step
        if step >= 1:
            precision = 0
        else:
            precision = max(0, int(round(-math.log10(step))))
        return round(floored, precision)


def build_risk_engine(config: dict) -> RiskEngine:
    account = config["account"]
    limits = RiskLimits(
        deposit_usd=float(account["deposit_usd"]),
        leverage=float(account["leverage"]),
        max_exposure_pct=float(account["max_exposure_pct"]),
        risk_per_trade_pct=float(account["risk_per_trade_pct"]),
        max_daily_loss_pct=float(account["max_daily_loss_pct"]),
        max_consecutive_losses=int(account["max_consecutive_losses"]),
        max_open_positions=int(account["max_open_positions"]),
        min_notional_usd=float(account["min_notional_usd"]),
        qty_step=float(account["qty_step"]),
        price_step=float(account["price_step"]),
    )
    return RiskEngine(limits, config.get("symbol_overrides", {}))
