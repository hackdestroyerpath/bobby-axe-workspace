from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Iterable

from .models import (
    EntryCandidate,
    FeatureExtractionResult,
    OhlcvCandle,
    PreprocessingFeatures,
    RegimeClassification,
    RegimeScores,
    SupportResistanceLevels,
    TrendStructure,
)


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


def _floor_to_bucket(ts: datetime, bucket_minutes: int) -> datetime:
    bucket_minute = (ts.minute // bucket_minutes) * bucket_minutes
    return ts.replace(minute=bucket_minute, second=0, microsecond=0)


def aggregate_ohlcv(ticks: list[Tick], timeframe: str) -> list[OhlcvCandle]:
    minutes_by_tf = {"1m": 1, "5m": 5, "15m": 15}
    if timeframe not in minutes_by_tf:
        raise ValueError(f"unsupported timeframe: {timeframe}")

    bucket_minutes = minutes_by_tf[timeframe]
    if not ticks:
        return []

    buckets: dict[datetime, list[Tick]] = {}
    for tick in ticks:
        bucket = _floor_to_bucket(tick.ts, bucket_minutes)
        buckets.setdefault(bucket, []).append(tick)

    candles: list[OhlcvCandle] = []
    for bucket_start in sorted(buckets):
        bucket_ticks = sorted(buckets[bucket_start], key=lambda t: t.ts)
        prices = [tick.price for tick in bucket_ticks]
        candles.append(
            OhlcvCandle(
                timeframe=timeframe,
                bucket_start=bucket_start,
                open=prices[0],
                high=max(prices),
                low=min(prices),
                close=prices[-1],
                volume=sum(t.volume for t in bucket_ticks),
                trades=len(bucket_ticks),
            )
        )
    return candles


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


def compute_trend_structure(candles: list[OhlcvCandle]) -> TrendStructure:
    if len(candles) < 2:
        return TrendStructure(direction="flat", slope=0.0, strength=0.0, higher_highs=0, lower_lows=0)

    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]

    start = closes[0]
    end = closes[-1]
    slope = 0.0 if start == 0 else (end - start) / start
    higher_highs = sum(1 for idx in range(1, len(highs)) if highs[idx] > highs[idx - 1])
    lower_lows = sum(1 for idx in range(1, len(lows)) if lows[idx] < lows[idx - 1])

    if slope > 0.002:
        direction = "up"
    elif slope < -0.002:
        direction = "down"
    else:
        direction = "flat"

    structure_consistency = abs(higher_highs - lower_lows) / max(1, len(candles) - 1)
    strength = min(1.0, abs(slope) * 20 + structure_consistency * 0.5)

    return TrendStructure(
        direction=direction,
        slope=slope,
        strength=strength,
        higher_highs=higher_highs,
        lower_lows=lower_lows,
    )


def compute_support_resistance(candles: list[OhlcvCandle], *, tolerance: float = 0.002) -> SupportResistanceLevels:
    if not candles:
        return SupportResistanceLevels(support=0.0, resistance=0.0, support_touches=0, resistance_touches=0)

    lows = [c.low for c in candles]
    highs = [c.high for c in candles]
    support = min(lows)
    resistance = max(highs)

    support_touches = sum(1 for price in lows if support > 0 and abs(price - support) / support <= tolerance)
    resistance_touches = sum(
        1 for price in highs if resistance > 0 and abs(price - resistance) / resistance <= tolerance
    )

    return SupportResistanceLevels(
        support=support,
        resistance=resistance,
        support_touches=support_touches,
        resistance_touches=resistance_touches,
    )


def generate_entry_candidates(last_price: float, sr: SupportResistanceLevels, trend: TrendStructure) -> tuple[EntryCandidate, ...]:
    support_bias = max(0.0, (last_price - sr.support) / max(last_price, 1e-9))
    resistance_bias = max(0.0, (sr.resistance - last_price) / max(last_price, 1e-9))

    pullback = (last_price + sr.support) / 2 if sr.support > 0 else last_price
    breakout = sr.resistance * 1.001 if sr.resistance > 0 else last_price * 1.001
    mean_revert = (sr.support + sr.resistance) / 2 if sr.support > 0 and sr.resistance > 0 else last_price

    pullback_quality = max(0.0, min(1.0, 0.6 + support_bias - trend.strength * 0.25))
    breakout_quality = max(0.0, min(1.0, 0.5 + resistance_bias + (0.3 if trend.direction == "up" else -0.15)))
    mean_revert_quality = max(0.0, min(1.0, 0.4 + (0.3 if trend.direction == "flat" else 0.0)))

    return (
        EntryCandidate(price=round(pullback, 6), strategy="pullback", quality=round(pullback_quality, 6)),
        EntryCandidate(price=round(breakout, 6), strategy="breakout", quality=round(breakout_quality, 6)),
        EntryCandidate(price=round(mean_revert, 6), strategy="mean_revert", quality=round(mean_revert_quality, 6)),
    )


def classify_market_regime(*, trend: TrendStructure, volatility: float) -> RegimeClassification:
    trend_score = min(1.0, abs(trend.slope) * 35 + trend.strength * 0.5)
    range_score = min(1.0, max(0.0, 1 - trend_score) + (0.25 if trend.direction == "flat" else 0.0))
    noisy_score = min(1.0, volatility * 50)

    scores = RegimeScores(
        trend=round(trend_score, 6),
        ranging=round(range_score, 6),
        noisy=round(noisy_score, 6),
    )
    dominant = max(("trend", scores.trend), ("ranging", scores.ranging), ("noisy", scores.noisy), key=lambda item: item[1])[0]
    rationale = (
        f"trend_slope={trend.slope:.5f}",
        f"trend_strength={trend.strength:.3f}",
        f"realized_vol={volatility:.5f}",
    )
    return RegimeClassification(label=dominant, scores=scores, rationale=rationale)


def classify_volatility_regime(realized_vol: float) -> RegimeClassification:
    calm = max(0.0, 1 - realized_vol * 120)
    normal = max(0.0, 1 - abs(realized_vol - 0.008) * 160)
    high = min(1.0, realized_vol * 120)
    scores = RegimeScores(trend=round(calm, 6), ranging=round(normal, 6), noisy=round(high, 6))
    label = "high" if high >= max(calm, normal) else "calm" if calm >= normal else "normal"
    rationale = (f"realized_vol={realized_vol:.5f}", f"calm_score={calm:.3f}", f"high_score={high:.3f}")
    return RegimeClassification(label=label, scores=scores, rationale=rationale)


def extract_preprocessing_features(ticks: Iterable[Tick]) -> FeatureExtractionResult:
    sanitized = sanitize_ticks(ticks)
    vol = volatility_features(sanitized)
    flow = order_flow_features(sanitized)

    candles_1m = aggregate_ohlcv(sanitized, "1m")
    candles_5m = aggregate_ohlcv(sanitized, "5m")
    candles_15m = aggregate_ohlcv(sanitized, "15m")

    trend = compute_trend_structure(candles_5m if candles_5m else candles_1m)
    support_resistance = compute_support_resistance(candles_15m if candles_15m else candles_5m)

    last_price = sanitized[-1].price if sanitized else 0.0
    entries = generate_entry_candidates(last_price, support_resistance, trend)

    market_regime = classify_market_regime(trend=trend, volatility=vol["realized_vol"])
    volatility_regime = classify_volatility_regime(vol["realized_vol"])

    side_distribution = Counter(t.side for t in sanitized)
    features = PreprocessingFeatures(
        tick_count=len(sanitized),
        last_price=last_price,
        realized_vol=vol["realized_vol"],
        price_range=vol["price_range"],
        buy_volume=float(flow["buy_volume"]),
        sell_volume=float(flow["sell_volume"]),
        imbalance=float(flow["imbalance"]),
        dominant_side=str(flow["dominant_side"]),
        trend=trend,
        support_resistance=support_resistance,
        market_regime=market_regime,
        volatility_regime=volatility_regime,
        entry_candidates=entries,
        side_distribution=dict(side_distribution),
        ohlcv_by_timeframe={"1m": candles_1m, "5m": candles_5m, "15m": candles_15m},
    )
    return FeatureExtractionResult(features=features, sanitized_ticks=tuple(sanitized))
