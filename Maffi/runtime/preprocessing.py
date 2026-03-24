from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import pstdev

from .models import (
    Candle,
    EntryCandidate,
    MarketRegime,
    MarketRegimeScores,
    PreprocessingFeatures,
    PreprocessingResult,
    SupportResistance,
    Tick,
    TrendStructure,
    VolatilityRegime,
)


def sanitize_ticks(ticks: list[Tick]) -> list[Tick]:
    dedup: dict[tuple[datetime, float, float, str], Tick] = {}
    for tick in ticks:
        if tick.price <= 0 or tick.volume <= 0:
            continue
        dedup[(tick.ts, tick.price, tick.volume, tick.side)] = tick
    return sorted(dedup.values(), key=lambda t: t.ts)


def aggregate_ohlcv(ticks: list[Tick], timeframe: str) -> tuple[Candle, ...]:
    seconds = {"1m": 60, "5m": 300, "15m": 900}[timeframe]
    buckets: dict[datetime, list[Tick]] = defaultdict(list)
    for tick in ticks:
        epoch = int(tick.ts.timestamp())
        bucket_epoch = epoch - (epoch % seconds)
        bucket_ts = datetime.fromtimestamp(bucket_epoch, tz=tick.ts.tzinfo)
        buckets[bucket_ts].append(tick)

    rows: list[Candle] = []
    for ts in sorted(buckets):
        group = buckets[ts]
        prices = [t.price for t in group]
        rows.append(
            Candle(
                ts=ts,
                open=group[0].price,
                high=max(prices),
                low=min(prices),
                close=group[-1].price,
                volume=sum(t.volume for t in group),
            )
        )
    return tuple(rows)


def compute_trend_structure(candles: tuple[Candle, ...]) -> TrendStructure:
    if len(candles) < 2:
        return TrendStructure(direction="flat", strength=0.0)
    first = candles[0].close
    last = candles[-1].close
    direction = "up" if last > first else "down" if last < first else "flat"
    avg = (abs(first) + abs(last)) / 2 or 1.0
    slope = abs(last - first) / max(len(candles), 1)
    strength = min((abs(last - first) / avg) * 1.8 + slope * 0.05, 1.0)
    return TrendStructure(direction=direction, strength=strength)


def classify_market_regime(*, trend: TrendStructure, volatility: float) -> MarketRegime:
    directional_boost = 0.25 if trend.direction in {"up", "down"} else 0.0
    trend_score = max(0.0, min(1.0, trend.strength * 1.25 + directional_boost - volatility * 2))
    ranging_score = max(0.0, min(1.0, 0.85 - trend_score * 0.7 - volatility * 1.5))
    noisy_score = max(0.0, min(1.0, volatility * 3.5))
    if trend_score >= ranging_score and trend_score >= noisy_score:
        label = "trend"
    elif ranging_score >= noisy_score:
        label = "ranging"
    else:
        label = "noisy"
    return MarketRegime(label=label, scores=MarketRegimeScores(trend=trend_score, ranging=ranging_score, noisy=noisy_score))


def classify_volatility_regime(realized_vol: float) -> VolatilityRegime:
    if realized_vol < 0.003:
        return VolatilityRegime(label="low")
    if realized_vol < 0.012:
        return VolatilityRegime(label="normal")
    return VolatilityRegime(label="high")


def compute_support_resistance(candles: tuple[Candle, ...]) -> SupportResistance:
    lows = [c.low for c in candles]
    highs = [c.high for c in candles]
    support = min(lows)
    resistance = max(highs)
    support_touches = sum(1 for c in candles if abs(c.low - support) < 1e-9)
    resistance_touches = sum(1 for c in candles if abs(c.high - resistance) < 1e-9)
    return SupportResistance(support=support, resistance=resistance, support_touches=support_touches, resistance_touches=resistance_touches)


def extract_preprocessing_features(ticks: list[Tick]) -> PreprocessingResult:
    clean = sanitize_ticks(ticks)
    candles_1m = aggregate_ohlcv(clean, "1m")
    candles_5m = aggregate_ohlcv(clean, "5m")
    candles_15m = aggregate_ohlcv(clean, "15m")

    returns: list[float] = []
    for prev, cur in zip(candles_1m, candles_1m[1:]):
        if prev.close:
            returns.append((cur.close - prev.close) / prev.close)
    realized_vol = pstdev(returns) if len(returns) > 1 else 0.0

    trend = compute_trend_structure(candles_5m if candles_5m else candles_1m)
    regime = classify_market_regime(trend=trend, volatility=realized_vol)
    vol_regime = classify_volatility_regime(realized_vol)
    sr = compute_support_resistance(candles_1m if candles_1m else candles_5m)

    span = max(sr.resistance - sr.support, 1e-6)
    entries = (
        EntryCandidate(price=sr.support + span * 0.2, quality=0.72),
        EntryCandidate(price=sr.support + span * 0.5, quality=0.78),
        EntryCandidate(price=sr.support + span * 0.8, quality=0.74),
    )

    return PreprocessingResult(
        sanitized_ticks=tuple(clean),
        features=PreprocessingFeatures(
            tick_count=len(clean),
            ohlcv_by_timeframe={"1m": candles_1m, "5m": candles_5m, "15m": candles_15m},
            market_regime=regime,
            volatility_regime=vol_regime,
            realized_vol=realized_vol,
            support_resistance=sr,
            entry_candidates=entries,
        ),
    )
