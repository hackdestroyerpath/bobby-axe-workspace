from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import pstdev

from .models import (
    Candle,
    EntryCandidate,
    FeatureExtractionResult,
    MarketRegime,
    MarketRegimeScores,
    MarketSnapshotFeatures,
    OrderFlowFeatures,
    PreprocessingDegradation,
    PreprocessingDegradationThresholds,
    PreprocessingFeatures,
    PreprocessingResult,
    PriceStructureFeatures,
    QualityTrustFeatures,
    RegimeFeatures,
    SupportResistance,
    SupportResistanceFeatures,
    Tick,
    TrendStructure,
    VolatilityFeatures,
    VolatilityRegime,
)

MIN_TICK_COUNT = 12
MAX_GAP_RATIO = 0.35
MAX_OUTLIER_RATIO = 0.08
MIN_SIDE_QUALITY_RATIO = 0.22
GAP_HEAVY_MIN_INTERVAL_SECONDS = 90.0
OUTLIER_RETURN_ABS_THRESHOLD = 0.02
OUTLIER_STD_MULTIPLIER = 3.0


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


def _compute_vwap(candles: tuple[Candle, ...]) -> float | None:
    if not candles:
        return None
    total_volume = sum(c.volume for c in candles)
    if total_volume <= 0:
        return None
    return sum(c.close * c.volume for c in candles) / total_volume


def _build_market_snapshot(
    *,
    clean: list[Tick],
    candles_1m: tuple[Candle, ...],
    candles_5m: tuple[Candle, ...],
    candles_15m: tuple[Candle, ...],
) -> MarketSnapshotFeatures:
    last_price = clean[-1].price if clean else 0.0
    volume_1m = sum(c.volume for c in candles_1m[-1:]) if candles_1m else 0.0
    volume_5m = sum(c.volume for c in candles_5m[-1:]) if candles_5m else 0.0
    return MarketSnapshotFeatures(
        last_price=last_price,
        vwap_1m=_compute_vwap(candles_1m[-1:]) if candles_1m else None,
        vwap_5m=_compute_vwap(candles_5m[-1:]) if candles_5m else None,
        vwap_15m=_compute_vwap(candles_15m[-1:]) if candles_15m else None,
        trade_count_1m=len([t for t in clean if candles_1m and t.ts >= candles_1m[-1].ts]) if candles_1m else 0,
        trade_count_5m=len([t for t in clean if candles_5m and t.ts >= candles_5m[-1].ts]) if candles_5m else 0,
        volume_1m=volume_1m,
        volume_5m=volume_5m,
        notional_1m=last_price * volume_1m if last_price else 0.0,
        notional_5m=last_price * volume_5m if last_price else 0.0,
    )


def _close_position(close: float | None, low: float | None, high: float | None) -> float | None:
    if close is None or low is None or high is None:
        return None
    width = high - low
    if width <= 0:
        return 0.5
    return max(0.0, min(1.0, (close - low) / width))


def _build_price_structure(
    *,
    candles_1m: tuple[Candle, ...],
    candles_5m: tuple[Candle, ...],
    candles_15m: tuple[Candle, ...],
    last_price: float,
) -> PriceStructureFeatures:
    last_1m = candles_1m[-1] if candles_1m else None
    last_5m = candles_5m[-1] if candles_5m else None
    local_high_15m = max((c.high for c in candles_15m), default=None)
    local_low_15m = min((c.low for c in candles_15m), default=None)

    return PriceStructureFeatures(
        open_1m=last_1m.open if last_1m else None,
        high_1m=last_1m.high if last_1m else None,
        low_1m=last_1m.low if last_1m else None,
        close_1m=last_1m.close if last_1m else None,
        open_5m=last_5m.open if last_5m else None,
        high_5m=last_5m.high if last_5m else None,
        low_5m=last_5m.low if last_5m else None,
        close_5m=last_5m.close if last_5m else None,
        local_high_15m=local_high_15m,
        local_low_15m=local_low_15m,
        range_width_1m=(last_1m.high - last_1m.low) if last_1m else None,
        range_width_5m=(last_5m.high - last_5m.low) if last_5m else None,
        close_position_in_1m_range=_close_position(last_1m.close if last_1m else None, last_1m.low if last_1m else None, last_1m.high if last_1m else None),
        close_position_in_5m_range=_close_position(last_5m.close if last_5m else None, last_5m.low if last_5m else None, last_5m.high if last_5m else None),
        distance_to_local_high=max((local_high_15m - last_price), 0.0) if local_high_15m is not None else None,
        distance_to_local_low=max((last_price - local_low_15m), 0.0) if local_low_15m is not None else None,
    )


def _atr_like(candles: tuple[Candle, ...]) -> float | None:
    if not candles:
        return None
    return sum((c.high - c.low) for c in candles) / len(candles)


def _return_std(candles: tuple[Candle, ...]) -> float | None:
    returns = []
    for prev, cur in zip(candles, candles[1:]):
        if prev.close:
            returns.append((cur.close - prev.close) / prev.close)
    if len(returns) < 2:
        return 0.0 if returns else None
    return pstdev(returns)


def _build_volatility_features(
    *,
    candles_1m: tuple[Candle, ...],
    candles_5m: tuple[Candle, ...],
    realized_vol: float,
    volatility_regime: VolatilityRegime,
) -> VolatilityFeatures:
    atr_like_1m = _atr_like(candles_1m[-5:] if candles_1m else candles_1m)
    atr_like_5m = _atr_like(candles_5m[-3:] if candles_5m else candles_5m)
    return_std_1m = _return_std(candles_1m)
    return_std_5m = _return_std(candles_5m)
    impulse_size_last_move = None
    impulse_duration_seconds = None
    if len(candles_1m) >= 2:
        impulse_size_last_move = abs(candles_1m[-1].close - candles_1m[-2].close)
        impulse_duration_seconds = (candles_1m[-1].ts - candles_1m[-2].ts).total_seconds()

    return VolatilityFeatures(
        atr_like_1m=atr_like_1m,
        atr_like_5m=atr_like_5m,
        realized_vol_1m=realized_vol * 0.6,
        realized_vol_5m=realized_vol,
        return_std_1m=return_std_1m,
        return_std_5m=return_std_5m,
        volatility_regime_label=volatility_regime.label,
        volatility_percentile_1h=min(realized_vol / 0.02, 1.0),
        impulse_size_last_move=impulse_size_last_move,
        impulse_duration_seconds=impulse_duration_seconds,
        volatility_stability_score=max(0.0, 1.0 - min(realized_vol * 8, 1.0)),
    )


def _sum_side_volume(ticks: list[Tick], *, since: datetime, side: str) -> float:
    return sum(t.volume for t in ticks if t.ts >= since and t.side.lower() == side)


def _build_order_flow_features(
    *,
    clean: list[Tick],
    candles_1m: tuple[Candle, ...],
    candles_5m: tuple[Candle, ...],
) -> OrderFlowFeatures:
    since_1m = candles_1m[-1].ts if candles_1m else (clean[-1].ts if clean else datetime.min)
    since_5m = candles_5m[-1].ts if candles_5m else (clean[-1].ts if clean else datetime.min)

    buy_volume_1m = _sum_side_volume(clean, since=since_1m, side="buy") if clean else 0.0
    sell_volume_1m = _sum_side_volume(clean, since=since_1m, side="sell") if clean else 0.0
    buy_volume_5m = _sum_side_volume(clean, since=since_5m, side="buy") if clean else 0.0
    sell_volume_5m = _sum_side_volume(clean, since=since_5m, side="sell") if clean else 0.0

    delta_1m = buy_volume_1m - sell_volume_1m
    delta_5m = buy_volume_5m - sell_volume_5m
    cumulative_delta_5m = delta_5m
    imbalance_ratio_1m = (buy_volume_1m / sell_volume_1m) if sell_volume_1m > 0 else (buy_volume_1m if buy_volume_1m > 0 else 1.0)
    imbalance_ratio_5m = (buy_volume_5m / sell_volume_5m) if sell_volume_5m > 0 else (buy_volume_5m if buy_volume_5m > 0 else 1.0)
    dominant_side = "buyers" if delta_5m >= 0 else "sellers"
    total_5m = buy_volume_5m + sell_volume_5m
    order_flow_confidence = abs(delta_5m) / total_5m if total_5m > 0 else 0.0

    return OrderFlowFeatures(
        buy_volume_1m=buy_volume_1m,
        sell_volume_1m=sell_volume_1m,
        buy_volume_5m=buy_volume_5m,
        sell_volume_5m=sell_volume_5m,
        delta_1m=delta_1m,
        delta_5m=delta_5m,
        cumulative_delta_5m=cumulative_delta_5m,
        imbalance_ratio_1m=imbalance_ratio_1m,
        imbalance_ratio_5m=imbalance_ratio_5m,
        aggression_score_buy=min(buy_volume_5m / total_5m, 1.0) if total_5m > 0 else 0.0,
        aggression_score_sell=min(sell_volume_5m / total_5m, 1.0) if total_5m > 0 else 0.0,
        dominant_side=dominant_side,
        order_flow_confidence=order_flow_confidence,
    )


def _build_regime_features(*, regime: MarketRegime) -> RegimeFeatures:
    trend_strength_score = regime.scores.trend
    trend_persistence_score = min(1.0, regime.scores.trend * 0.9)
    mean_reversion_score = regime.scores.ranging
    chop_score = min(1.0, regime.scores.ranging * 0.75)
    noise_score = regime.scores.noisy
    reversal_frequency_score = min(1.0, regime.scores.ranging * 0.6)
    regime_confidence = max(regime.scores.trend, regime.scores.ranging, regime.scores.noisy)
    return RegimeFeatures(
        market_regime_label=regime.label,
        regime_confidence=regime_confidence,
        trend_strength_score=trend_strength_score,
        trend_persistence_score=trend_persistence_score,
        mean_reversion_score=mean_reversion_score,
        chop_score=chop_score,
        noise_score=noise_score,
        reversal_frequency_score=reversal_frequency_score,
    )


def _build_support_resistance_features(
    *,
    support_resistance: SupportResistance,
    last_price: float,
    atr_like_5m: float | None,
) -> SupportResistanceFeatures:
    buffer = max((atr_like_5m or 0.0) * 0.25, 0.01)
    support_zone_low = support_resistance.support
    support_zone_high = support_resistance.support + buffer
    resistance_zone_low = support_resistance.resistance - buffer
    resistance_zone_high = support_resistance.resistance
    nearest_support_distance = max(last_price - support_resistance.support, 0.0)
    nearest_resistance_distance = max(support_resistance.resistance - last_price, 0.0)
    total_touches = support_resistance.support_touches + support_resistance.resistance_touches
    boundary_reaction_score = min(total_touches / 4.0, 1.0)
    bounce_frequency_score = min(max(support_resistance.support_touches, support_resistance.resistance_touches) / 3.0, 1.0)
    wick_rejection_score_upper = min(support_resistance.resistance_touches / 3.0, 1.0)
    wick_rejection_score_lower = min(support_resistance.support_touches / 3.0, 1.0)
    level_respect_score = min((support_resistance.support_touches + support_resistance.resistance_touches) / 6.0, 1.0)
    return SupportResistanceFeatures(
        support_zone_low=support_zone_low,
        support_zone_high=support_zone_high,
        resistance_zone_low=resistance_zone_low,
        resistance_zone_high=resistance_zone_high,
        nearest_support_distance=nearest_support_distance,
        nearest_resistance_distance=nearest_resistance_distance,
        boundary_reaction_score=boundary_reaction_score,
        bounce_frequency_score=bounce_frequency_score,
        wick_rejection_score_upper=wick_rejection_score_upper,
        wick_rejection_score_lower=wick_rejection_score_lower,
        level_respect_score=level_respect_score,
    )


def _build_quality_trust_features(
    *,
    clean: list[Tick],
    degradation: PreprocessingDegradation,
    last_price: float,
) -> QualityTrustFeatures:
    largest_gap_seconds = degradation.gap_ratio * GAP_HEAVY_MIN_INTERVAL_SECONDS
    liquidity_quality_score = max(0.0, min(len(clean) / max(MIN_TICK_COUNT * 4, 1), 1.0))
    penalty = min(
        (0.35 if degradation.sparse_input else 0.0)
        + (0.25 if degradation.gap_heavy_sequence else 0.0)
        + (0.2 if degradation.outlier_noise_flags else 0.0)
        + (0.2 if degradation.low_side_quality else 0.0),
        0.85,
    )
    payload_confidence = max(0.1, 1.0 - penalty)
    return QualityTrustFeatures(
        coverage_ratio=max(0.0, 1.0 - degradation.gap_ratio),
        largest_gap_seconds=largest_gap_seconds,
        outlier_ratio=degradation.outlier_ratio,
        liquidity_quality_score=liquidity_quality_score,
        payload_confidence=payload_confidence,
        degradation_flags=degradation.triggered_flags,
    )


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
    market_snapshot = _build_market_snapshot(clean=clean, candles_1m=candles_1m, candles_5m=candles_5m, candles_15m=candles_15m)
    price_structure = _build_price_structure(candles_1m=candles_1m, candles_5m=candles_5m, candles_15m=candles_15m, last_price=market_snapshot.last_price)
    volatility_features = _build_volatility_features(candles_1m=candles_1m, candles_5m=candles_5m, realized_vol=realized_vol, volatility_regime=vol_regime)
    order_flow_features = _build_order_flow_features(clean=clean, candles_1m=candles_1m, candles_5m=candles_5m)
    regime_features = _build_regime_features(regime=regime)
    support_resistance_features = _build_support_resistance_features(
        support_resistance=sr,
        last_price=market_snapshot.last_price,
        atr_like_5m=volatility_features.atr_like_5m,
    )

    span = max(sr.resistance - sr.support, 1e-6)
    entries = (
        EntryCandidate(price=sr.support + span * 0.2, quality=0.72),
        EntryCandidate(price=sr.support + span * 0.5, quality=0.78),
        EntryCandidate(price=sr.support + span * 0.8, quality=0.74),
    )

    intervals = [(cur.ts - prev.ts).total_seconds() for prev, cur in zip(clean, clean[1:])]
    gap_ratio = (
        sum(1 for interval in intervals if interval >= GAP_HEAVY_MIN_INTERVAL_SECONDS) / len(intervals)
        if intervals
        else 0.0
    )

    outlier_ratio = 0.0
    if returns:
        returns_std = pstdev(returns) if len(returns) > 1 else 0.0
        outlier_count = 0
        for value in returns:
            abs_value = abs(value)
            is_outlier = abs_value >= OUTLIER_RETURN_ABS_THRESHOLD
            if returns_std > 0:
                is_outlier = is_outlier or (abs_value / returns_std) >= OUTLIER_STD_MULTIPLIER
            if is_outlier:
                outlier_count += 1
        outlier_ratio = outlier_count / len(returns)

    side_counts = defaultdict(int)
    for tick in clean:
        side_counts[tick.side.lower()] += 1
    buy_count = side_counts.get("buy", 0)
    sell_count = side_counts.get("sell", 0)
    total_known_side = buy_count + sell_count
    side_quality_ratio = min(buy_count, sell_count) / total_known_side if total_known_side else 0.0

    sparse_input = len(clean) < MIN_TICK_COUNT
    gap_heavy_sequence = gap_ratio > MAX_GAP_RATIO
    outlier_noise_flags = outlier_ratio > MAX_OUTLIER_RATIO
    low_side_quality = side_quality_ratio < MIN_SIDE_QUALITY_RATIO

    triggered_flags = tuple(
        flag
        for condition, flag in (
            (sparse_input, "sparse_input"),
            (gap_heavy_sequence, "gap_heavy_sequence"),
            (outlier_noise_flags, "outlier_noise_flags"),
            (low_side_quality, "low_side_quality"),
        )
        if condition
    )

    degradation = PreprocessingDegradation(
        sparse_input=sparse_input,
        gap_heavy_sequence=gap_heavy_sequence,
        outlier_noise_flags=outlier_noise_flags,
        low_side_quality=low_side_quality,
        triggered_flags=triggered_flags,
        tick_count=len(clean),
        gap_ratio=gap_ratio,
        outlier_ratio=outlier_ratio,
        side_quality_ratio=side_quality_ratio,
        thresholds=PreprocessingDegradationThresholds(
            min_tick_count=MIN_TICK_COUNT,
            max_gap_ratio=MAX_GAP_RATIO,
            max_outlier_ratio=MAX_OUTLIER_RATIO,
            min_side_quality_ratio=MIN_SIDE_QUALITY_RATIO,
        ),
    )
    quality_trust = _build_quality_trust_features(clean=clean, degradation=degradation, last_price=market_snapshot.last_price)

    return PreprocessingResult(
        sanitized_ticks=tuple(clean),
        feature_extraction=FeatureExtractionResult(
            features=PreprocessingFeatures(
                tick_count=len(clean),
                ohlcv_by_timeframe={"1m": candles_1m, "5m": candles_5m, "15m": candles_15m},
                market_snapshot=market_snapshot,
                price_structure=price_structure,
                volatility=volatility_features,
                order_flow=order_flow_features,
                regime=regime_features,
                support_resistance_features=support_resistance_features,
                quality_trust=quality_trust,
                market_regime=regime,
                volatility_regime=vol_regime,
                realized_vol=realized_vol,
                support_resistance=sr,
                entry_candidates=entries,
            ),
            degradation=degradation,
        ),
    )
