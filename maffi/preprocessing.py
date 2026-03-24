from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Tick:
    ts: datetime
    price: float
    volume: float
    side: str


def sanitize_ticks(ticks: Iterable[Tick]) -> list[Tick]:
    cleaned = sorted(ticks, key=lambda x: x.ts)
    deduped: list[Tick] = []
    seen: set[tuple[datetime, float, float, str]] = set()
    for tick in cleaned:
        key = (tick.ts, tick.price, tick.volume, tick.side)
        if tick.price <= 0 or tick.volume < 0:
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tick)
    return deduped


def volatility_features(ticks: list[Tick]) -> dict[str, float]:
    if len(ticks) < 2:
        return {"realized_vol": 0.0, "price_range": 0.0}
    prices = [t.price for t in ticks]
    returns = [abs(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices)) if prices[i - 1] > 0]
    return {
        "realized_vol": float(mean(returns)) if returns else 0.0,
        "price_range": max(prices) - min(prices),
    }


def order_flow_features(ticks: list[Tick]) -> dict[str, float | str]:
    buy_volume = sum(t.volume for t in ticks if t.side == "buy")
    sell_volume = sum(t.volume for t in ticks if t.side == "sell")
    total = buy_volume + sell_volume
    imbalance = 0.0 if total <= 0 else (buy_volume - sell_volume) / total
    dominant_side = "buyers" if imbalance > 0.1 else "sellers" if imbalance < -0.1 else "mixed"
    return {
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "imbalance": imbalance,
        "dominant_side": dominant_side,
    }
