from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Mapping, Sequence

from .common.tick_to_features_engine import CandleFeatureRow

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class StrategyComputation:
    features: Mapping[str, object]


def compute_rsi_macd(candles: Sequence[CandleFeatureRow]) -> StrategyComputation:
    usable = [c for c in candles if c.close is not None]
    closes = [c.close for c in usable]
    if len(closes) < 34:
        raise ValueError("RSI_MACD requires at least 34 candles")

    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd_line = [fast - slow for fast, slow in zip(ema12[-len(ema26):], ema26)]
    signal_line = _ema(macd_line, 9)
    histogram = [line - signal for line, signal in zip(macd_line[-len(signal_line):], signal_line)]
    rsi_value = _rsi(closes, 14)
    prev_rsi = _rsi(closes[:-1], 14) if len(closes) > 15 else rsi_value
    latest_hist = histogram[-1]
    prev_hist = histogram[-2] if len(histogram) > 1 else latest_hist
    latest_macd = macd_line[-1]
    latest_signal = signal_line[-1]

    if rsi_value >= Decimal("70"):
        rsi_zone = "overbought"
    elif rsi_value <= Decimal("30"):
        rsi_zone = "oversold"
    else:
        rsi_zone = "neutral"

    rsi_slope = "flat"
    if rsi_value > prev_rsi:
        rsi_slope = "up"
    elif rsi_value < prev_rsi:
        rsi_slope = "down"

    macd_state = "bullish" if latest_macd > latest_signal else "bearish" if latest_macd < latest_signal else "mixed"
    hist_state = "expanding" if abs(latest_hist) > abs(prev_hist) else "fading" if abs(latest_hist) < abs(prev_hist) else "flat"

    bullish_votes = sum(
        [
            latest_macd > latest_signal,
            latest_hist > 0,
            rsi_slope == "up",
            rsi_value >= Decimal("55"),
        ]
    )
    bearish_votes = sum(
        [
            latest_macd < latest_signal,
            latest_hist < 0,
            rsi_slope == "down",
            rsi_value <= Decimal("45"),
        ]
    )
    if bullish_votes >= 3:
        momentum_state = "bullish"
    elif bearish_votes >= 3:
        momentum_state = "bearish"
    else:
        momentum_state = "mixed"

    max_vote = max(bullish_votes, bearish_votes)
    momentum_strength = "strong" if max_vote >= 4 else "medium" if max_vote >= 3 else "weak"

    return StrategyComputation(
        features={
            "timestamp": usable[-1].bucket_end_utc.isoformat().replace("+00:00", "Z"),
            "timeframe": usable[-1].timeframe,
            "rsi_value": _quantize(rsi_value),
            "rsi_zone": rsi_zone,
            "rsi_slope": rsi_slope,
            "macd_line": _quantize(latest_macd),
            "signal_line": _quantize(latest_signal),
            "macd_hist": _quantize(latest_hist),
            "macd_state": macd_state,
            "hist_state": hist_state,
            "momentum_state": momentum_state,
            "momentum_strength": momentum_strength,
            "summary_state": momentum_state,
            "summary_strength": momentum_strength,
            "summary_note": f"RSI zone={rsi_zone}, MACD state={macd_state}",
        }
    )


def compute_levels_fibo_hv(candles: Sequence[CandleFeatureRow]) -> StrategyComputation:
    usable = [c for c in candles if c.close is not None]
    if len(usable) < 20:
        raise ValueError("LEVELS_FIBO_HV requires at least 20 candles")

    closes = [c.close for c in usable]
    highs = [c.high for c in usable if c.high is not None]
    lows = [c.low for c in usable if c.low is not None]
    last_close = closes[-1]
    recent = usable[-20:]
    support = min((c.low for c in recent if c.low is not None), default=last_close)
    resistance = max((c.high for c in recent if c.high is not None), default=last_close)
    swing_low = min(lows[-20:])
    swing_high = max(highs[-20:])
    swing_range = swing_high - swing_low
    if swing_range <= _ZERO:
        raise ValueError("LEVELS_FIBO_HV requires non-zero swing range")

    fib_levels = {
        Decimal("0.236"): swing_high - (swing_range * Decimal("0.236")),
        Decimal("0.382"): swing_high - (swing_range * Decimal("0.382")),
        Decimal("0.5"): swing_high - (swing_range * Decimal("0.5")),
        Decimal("0.618"): swing_high - (swing_range * Decimal("0.618")),
        Decimal("0.786"): swing_high - (swing_range * Decimal("0.786")),
    }
    nearest_ratio, nearest_level = min(fib_levels.items(), key=lambda item: abs(last_close - item[1]))

    poc = _volume_profile_poc(recent)
    sorted_prices = sorted(closes[-20:])
    vah = sorted_prices[int(len(sorted_prices) * 0.7)]
    val = sorted_prices[int(len(sorted_prices) * 0.3)]
    inside_value_area = val <= last_close <= vah
    near_threshold = max(swing_range * Decimal("0.02"), Decimal("0.01"))

    if abs(last_close - nearest_level) <= near_threshold:
        price_vs_fib = "near"
    elif last_close > nearest_level:
        price_vs_fib = "above"
    else:
        price_vs_fib = "below"

    price_vs_poc = "near" if abs(last_close - poc) <= near_threshold else "above" if last_close > poc else "below"
    structure_state = "bullish" if last_close > poc and last_close > nearest_level else "bearish" if last_close < poc and last_close < nearest_level else "range"
    level_context_strength = "strong" if inside_value_area and price_vs_poc == "near" else "medium" if structure_state != "range" else "weak"

    return StrategyComputation(
        features={
            "nearest_support": _quantize(support),
            "nearest_resistance": _quantize(resistance),
            "distance_to_support": _quantize(last_close - support),
            "distance_to_resistance": _quantize(resistance - last_close),
            "nearest_fib_ratio": str(nearest_ratio),
            "nearest_fib_level": _quantize(nearest_level),
            "price_vs_fib": price_vs_fib,
            "hv_poc": _quantize(poc),
            "value_area_high": _quantize(vah),
            "value_area_low": _quantize(val),
            "inside_value_area": inside_value_area,
            "price_vs_poc": price_vs_poc,
            "structure_state": structure_state,
            "level_context_strength": level_context_strength,
            "summary_state": structure_state,
            "summary_strength": level_context_strength,
            "summary_note": f"price_vs_fib={price_vs_fib}, price_vs_poc={price_vs_poc}",
        }
    )


def compute_volume(candles: Sequence[CandleFeatureRow]) -> StrategyComputation:
    usable = [c for c in candles if c.close is not None]
    if len(usable) < 5:
        raise ValueError("VOLUME requires at least 5 candles")

    latest = usable[-1]
    history = usable[-20:-1] if len(usable) > 20 else usable[:-1]
    avg_volume = latest.relative_volume_baseline or (_mean_decimal([c.volume for c in history]) if history else latest.volume)
    relative_volume = _ZERO if avg_volume in (None, _ZERO) else latest.volume / avg_volume
    volume_spike_flag = relative_volume >= Decimal("1.5")
    imbalance_ratio = latest.imbalance
    pressure_side = "buyers" if latest.delta > 0 else "sellers" if latest.delta < 0 else "mixed"

    price_change = _ZERO
    if len(usable) > 1 and usable[-2].close is not None and latest.close is not None:
        price_change = latest.close - usable[-2].close
    directional_match = (price_change > 0 and latest.delta > 0) or (price_change < 0 and latest.delta < 0)
    if latest.volume == _ZERO:
        volume_confirmation_state = "weak"
    elif directional_match:
        volume_confirmation_state = "confirms"
    elif pressure_side == "mixed":
        volume_confirmation_state = "mixed"
    else:
        volume_confirmation_state = "weak"

    flow_strength = "strong" if volume_spike_flag and abs(imbalance_ratio) >= Decimal("0.4") else "medium" if abs(imbalance_ratio) >= Decimal("0.15") else "weak"

    return StrategyComputation(
        features={
            "current_volume": _quantize(latest.volume),
            "avg_volume": _quantize(avg_volume or _ZERO),
            "relative_volume": _quantize(relative_volume),
            "volume_spike_flag": volume_spike_flag,
            "buy_volume": _quantize(latest.buy_volume),
            "sell_volume": _quantize(latest.sell_volume),
            "volume_delta": _quantize(latest.delta),
            "imbalance_ratio": _quantize(imbalance_ratio),
            "pressure_side": pressure_side,
            "volume_confirmation_state": volume_confirmation_state,
            "flow_strength": flow_strength,
            "summary_state": pressure_side,
            "summary_strength": flow_strength,
            "summary_note": f"volume_confirmation={volume_confirmation_state}, spike={volume_spike_flag}",
        }
    )


def compute_elliott(candles: Sequence[CandleFeatureRow]) -> StrategyComputation:
    usable = [c for c in candles if c.close is not None]
    if len(usable) < 10:
        raise ValueError("ELLIOTT requires at least 10 candles")

    pivots = _pivot_points(usable[-15:])
    last_close = usable[-1].close
    first_close = usable[-5].close
    trend_state = "up" if last_close > first_close else "down" if last_close < first_close else "flat"
    structure_state = "intact" if len(pivots) >= 4 else "weakening" if len(pivots) >= 2 else "broken"
    last_leg = last_close - usable[-2].close
    current_leg_direction = "up" if last_leg > 0 else "down" if last_leg < 0 else "flat"
    current_leg_strength = "strong" if abs(last_leg) >= Decimal("3") else "medium" if abs(last_leg) >= Decimal("1") else "weak"

    rolling_span = max((max(c.high for c in usable[-10:] if c.high is not None) - min(c.low for c in usable[-10:] if c.low is not None)), Decimal("0.01"))
    correction_depth = abs(last_close - min(c.close for c in usable[-3:])) / rolling_span
    correction_depth_state = "shallow" if correction_depth < Decimal("0.33") else "normal" if correction_depth < Decimal("0.66") else "deep"

    pattern_candidate = "impulse_candidate" if trend_state in {"up", "down"} and structure_state == "intact" else "range_candidate"
    pattern_state = "candidate" if structure_state != "broken" else "unclear"
    elliott_candidate_family = "motive" if pattern_candidate == "impulse_candidate" else "corrective"
    elliott_direction_candidate = trend_state if trend_state in {"up", "down"} else "unclear"
    elliott_confidence_state = "medium" if structure_state == "intact" and len(pivots) >= 5 else "low"

    return StrategyComputation(
        features={
            "trend_state": trend_state,
            "structure_state": structure_state,
            "current_leg_direction": current_leg_direction,
            "current_leg_strength": current_leg_strength,
            "correction_depth_state": correction_depth_state,
            "pattern_candidate": pattern_candidate,
            "pattern_state": pattern_state,
            "elliott_candidate_family": elliott_candidate_family,
            "elliott_direction_candidate": elliott_direction_candidate,
            "elliott_confidence_state": elliott_confidence_state,
            "summary_state": trend_state,
            "summary_strength": current_leg_strength,
            "summary_note": f"candidate={pattern_candidate}, confidence={elliott_confidence_state}",
        }
    )


def _ema(values: Sequence[Decimal], period: int) -> list[Decimal]:
    if len(values) < period:
        raise ValueError(f"EMA requires at least {period} values")
    multiplier = Decimal("2") / Decimal(period + 1)
    ema_values = [_mean_decimal(values[:period])]
    for value in values[period:]:
        ema_values.append(((value - ema_values[-1]) * multiplier) + ema_values[-1])
    return ema_values


def _rsi(values: Sequence[Decimal], period: int) -> Decimal:
    if len(values) <= period:
        raise ValueError(f"RSI requires more than {period} closes")
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for previous, current in zip(values, values[1:]):
        change = current - previous
        gains.append(change if change > 0 else _ZERO)
        losses.append(abs(change) if change < 0 else _ZERO)
    avg_gain = _mean_decimal(gains[-period:])
    avg_loss = _mean_decimal(losses[-period:])
    if avg_loss == _ZERO:
        return Decimal("100")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    values = list(values)
    if not values:
        return _ZERO
    return sum(values, _ZERO) / Decimal(len(values))


def _volume_profile_poc(candles: Sequence[CandleFeatureRow]) -> Decimal:
    buckets: dict[Decimal, Decimal] = {}
    for candle in candles:
        if candle.close is None:
            continue
        key = candle.close.quantize(Decimal("1"))
        buckets[key] = buckets.get(key, _ZERO) + candle.volume
    if not buckets:
        return _ZERO
    return max(buckets.items(), key=lambda item: (item[1], item[0]))[0]


def _pivot_points(candles: Sequence[CandleFeatureRow]) -> list[Decimal]:
    pivots: list[Decimal] = []
    for left, center, right in zip(candles, candles[1:], candles[2:]):
        if center.high is not None and left.high is not None and right.high is not None:
            if center.high >= left.high and center.high >= right.high:
                pivots.append(center.high)
        if center.low is not None and left.low is not None and right.low is not None:
            if center.low <= left.low and center.low <= right.low:
                pivots.append(center.low)
    return pivots


def _quantize(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.0001")))
