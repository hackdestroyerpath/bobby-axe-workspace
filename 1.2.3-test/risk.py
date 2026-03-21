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
    take_profit_price: float | None
    stop_loss_price: float | None
    exit_after_bars: int | None
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

    def build_grid_plan(
        self,
        symbol: str,
        regime: str,
        center_price: float,
        spacing: float,
        levels: int,
        *,
        directional_tp_spacing_mult: float = 2.0,
        directional_sl_spacing_mult: float = 1.0,
        neutral_exit_after_bars: int = 6,
    ) -> GridPlan:
        limits = self._limits_for_symbol(symbol)
        if spacing <= 0:
            raise ValueError("Grid spacing must be positive")
        if levels < 1:
            raise ValueError("Grid levels must be at least 1")
        if regime not in {"LONG_GRID", "SHORT_GRID", "NEUTRAL_GRID"}:
            raise ValueError(f"Unsupported regime: {regime}")

        min_qty = self._min_qty_for_notional(center_price, limits.min_notional_usd, limits.qty_step)
        min_level_notional = min_qty * center_price
        min_total_notional = min_level_notional * levels

        lower = center_price - spacing * levels
        upper = center_price + spacing * levels
        total_notional = limits.max_notional_usd
        if total_notional < min_total_notional:
            raise ValueError(self._economics_infeasible_reason(symbol=symbol, levels=levels, min_level_notional=min_level_notional, available_total_notional=total_notional))
        level_notional = total_notional / levels if levels else 0.0
        if level_notional < min_level_notional:
            raise ValueError(self._economics_infeasible_reason(symbol=symbol, levels=levels, min_level_notional=min_level_notional, available_total_notional=total_notional))

        qty = self._floor_to_step(level_notional / center_price, limits.qty_step)
        if qty <= 0:
            raise ValueError(f"Quantity became zero after rounding for {symbol}")
        if qty * center_price < limits.min_notional_usd:
            raise ValueError(f"Per-level notional below minimum threshold for {symbol}: need {limits.min_notional_usd:.2f} USD, got {qty * center_price:.2f} USD")

        invalidation = self._invalidation_price(regime, center_price, lower, upper, spacing)
        take_profit, stop_loss, exit_after_bars = self._exit_plan(
            regime,
            center_price,
            spacing,
            lower,
            upper,
            directional_tp_spacing_mult,
            directional_sl_spacing_mult,
            neutral_exit_after_bars,
        )
        confidence = self._confidence(center_price, spacing)
        return GridPlan(
            regime=regime,
            center_price=self._round_price(center_price, limits.price_step),
            lower_bound=self._round_price(lower, limits.price_step),
            upper_bound=self._round_price(upper, limits.price_step),
            grid_spacing=self._round_price(spacing, limits.price_step),
            levels=levels,
            quantity_per_level=qty,
            total_notional_usd=round(qty * center_price * levels, 4),
            invalidation_price=self._round_price(invalidation, limits.price_step),
            take_profit_price=self._round_price(take_profit, limits.price_step) if take_profit is not None else None,
            stop_loss_price=self._round_price(stop_loss, limits.price_step) if stop_loss is not None else None,
            exit_after_bars=exit_after_bars,
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

    def _economics_infeasible_reason(self, *, symbol: str, levels: int, min_level_notional: float, available_total_notional: float) -> str:
        available_per_level = available_total_notional / levels if levels else 0.0
        feasible_levels = int(available_total_notional // min_level_notional) if min_level_notional > 0 else 0
        suggestion = f"max feasible levels at current settings: {feasible_levels}" if feasible_levels > 0 else "max feasible levels at current settings: 0"
        return (
            f"Grid economics infeasible for {symbol}: exchange filters require about {min_level_notional:.2f} USD per level, "
            f"but account/risk settings allow only {available_per_level:.2f} USD per level ({available_total_notional:.2f} USD total across {levels} levels); {suggestion}; reduce levels or increase max notional."
        )

    def _exit_plan(self, regime: str, center_price: float, spacing: float, lower: float, upper: float, tp_mult: float, sl_mult: float, neutral_exit_after_bars: int) -> tuple[float | None, float | None, int | None]:
        if regime == "LONG_GRID":
            return upper + spacing * tp_mult, lower - spacing * sl_mult, None
        if regime == "SHORT_GRID":
            return lower - spacing * tp_mult, upper + spacing * sl_mult, None
        return None, None, neutral_exit_after_bars

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
    def _step_precision(step: float) -> int:
        if step >= 1:
            return 0
        return max(0, int(round(-math.log10(step))))

    @classmethod
    def _min_qty_for_notional(cls, center_price: float, min_notional_usd: float, qty_step: float) -> float:
        raw_qty = min_notional_usd / center_price if center_price else 0.0
        steps = math.ceil(raw_qty / qty_step) if qty_step > 0 else 0
        return round(steps * qty_step, cls._step_precision(qty_step))

    @classmethod
    def _floor_to_step(cls, value: float, step: float) -> float:
        floored = math.floor(value / step) * step
        return round(floored, cls._step_precision(step))


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
