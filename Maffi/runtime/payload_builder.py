from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any, Iterable, Mapping

from TRADING_ALGOS.common.tick_normalizer import (
    PARTIAL_REASON_EMPTY_WINDOW,
    PARTIAL_REASON_GAP_HEAVY,
    PARTIAL_REASON_PAGINATION,
    PARTIAL_REASON_RETENTION,
    NormalizationResult,
    normalize_ticks,
)
from TRADING_ALGOS.common.tick_to_features_engine import (
    CandleFeatureRow,
    TickToFeaturesResult,
    build_tick_feature_candles,
)
from new_collector.models import TickTrade

from .enums import DominantSide, MarketRegime, QualityStatus, VolatilityRegime
from .models import MaffiInputPayload, now_utc_iso

COVERAGE_DEGRADED_THRESHOLD = 0.65
COVERAGE_BAD_THRESHOLD = 0.30


def build_maffi_payload(
    *,
    symbol: str,
    source: str,
    window_from: datetime,
    window_to: datetime,
    trades: Iterable[TickTrade | Mapping[str, Any]] | None = None,
    normalization_result: NormalizationResult | None = None,
    feature_result: TickToFeaturesResult | None = None,
    gap_threshold: timedelta = timedelta(minutes=2),
    page_complete: bool = True,
    retention_floor: datetime | None = None,
) -> MaffiInputPayload:
    """Build a contract-complete Maffi input payload from collector/features inputs."""

    if normalization_result is None:
        normalization_result = normalize_ticks(
            tuple(_as_raw_tick(trade) for trade in (trades or ())),
            window_from=window_from,
            window_to=window_to,
            gap_threshold=gap_threshold,
            page_complete=page_complete,
            retention_floor=retention_floor,
        )

    if feature_result is None:
        feature_result = build_tick_feature_candles(
            normalization_result.ticks,
            window_from=normalization_result.window_from,
            window_to=normalization_result.window_to,
            include_incomplete_candle=True,
        )

    one_minute_rows = tuple(feature_result.candles_by_timeframe.get("1m", ()))
    quality_status, degradation_reasons = _quality_from_normalization(normalization_result)

    support_level, resistance_level, atr, last_price = _levels_and_atr(one_minute_rows)
    long_score, short_score = _directional_scores(one_minute_rows)

    reject_score = _reject_score(
        quality_status=quality_status,
        degradation_reasons=degradation_reasons,
        long_score=long_score,
        short_score=short_score,
    )
    market_regime = _market_regime(one_minute_rows, long_score, short_score)
    volatility_regime = _volatility_regime(atr, last_price)
    dominant_side = _dominant_side(one_minute_rows)
    confidence_hint = _confidence_hint(quality_status, long_score, short_score, reject_score)
    entry_candidates = _entry_candidates(support_level, resistance_level)

    context = {
        "payload_builder": {
            "degradation_reasons": degradation_reasons,
            "normalization": {
                "coverage_ratio": normalization_result.coverage_ratio,
                "is_partial": normalization_result.is_partial,
                "partial_reasons": list(normalization_result.partial_reasons),
                "gap_count": normalization_result.gap_count,
                "tick_count": normalization_result.tick_count,
                "empty_window": normalization_result.empty_window,
            },
            "feature_trace": {
                "one_minute_candle_count": len(one_minute_rows),
                "incomplete_candle_count": sum(1 for row in one_minute_rows if row.is_incomplete),
                "empty_candle_count": sum(1 for row in one_minute_rows if row.is_empty),
            },
        }
    }

    return MaffiInputPayload(
        schema_version="maffi-v1",
        symbol=symbol,
        generated_at_utc=now_utc_iso(),
        source=source,
        input_quality_status=quality_status,
        market_regime=market_regime,
        volatility_regime=volatility_regime,
        dominant_side=dominant_side,
        long_score=long_score,
        short_score=short_score,
        reject_score=reject_score,
        confidence_hint=confidence_hint,
        entry_candidates=entry_candidates,
        support_level=support_level,
        resistance_level=resistance_level,
        last_price=last_price,
        atr=atr,
        context=context,
    )


def payload_to_dict(payload: MaffiInputPayload) -> dict[str, Any]:
    serialized = asdict(payload)
    serialized["input_quality_status"] = payload.input_quality_status.value
    serialized["market_regime"] = payload.market_regime.value
    serialized["volatility_regime"] = payload.volatility_regime.value
    serialized["dominant_side"] = payload.dominant_side.value
    serialized["entry_candidates"] = list(payload.entry_candidates)
    return serialized


def _as_raw_tick(trade: TickTrade | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(trade, Mapping):
        return dict(trade)
    return {
        "source": trade.source,
        "symbol": trade.symbol,
        "trade_id": trade.trade_id or f"{trade.event_time_utc.isoformat()}-{trade.price}",
        "event_time_utc": trade.event_time_utc,
        "price": trade.price,
        "quantity": trade.quantity,
        "side": trade.side,
        "ingested_at_utc": trade.ingested_at_utc,
    }


def _quality_from_normalization(normalization: NormalizationResult) -> tuple[QualityStatus, list[dict[str, Any]]]:
    reasons: list[dict[str, Any]] = []

    if normalization.empty_window or PARTIAL_REASON_EMPTY_WINDOW in normalization.partial_reasons:
        reasons.append({"code": "empty_window", "severity": "bad", "detail": "No ticks in requested window."})

    if PARTIAL_REASON_GAP_HEAVY in normalization.partial_reasons:
        reasons.append(
            {
                "code": "heavy_gaps",
                "severity": "degraded",
                "detail": f"Gap-heavy window detected; gap_count={normalization.gap_count}.",
            }
        )

    truncation_hits = [
        reason
        for reason in normalization.partial_reasons
        if reason in {PARTIAL_REASON_RETENTION, PARTIAL_REASON_PAGINATION}
    ]
    if truncation_hits:
        reasons.append(
            {
                "code": "truncation",
                "severity": "degraded",
                "detail": f"Partial window due to: {','.join(truncation_hits)}.",
            }
        )

    if normalization.coverage_ratio < COVERAGE_BAD_THRESHOLD:
        reasons.append(
            {
                "code": "low_coverage",
                "severity": "bad",
                "detail": f"coverage_ratio={normalization.coverage_ratio:.3f} < {COVERAGE_BAD_THRESHOLD:.2f}",
            }
        )
    elif normalization.coverage_ratio < COVERAGE_DEGRADED_THRESHOLD:
        reasons.append(
            {
                "code": "low_coverage",
                "severity": "degraded",
                "detail": f"coverage_ratio={normalization.coverage_ratio:.3f} < {COVERAGE_DEGRADED_THRESHOLD:.2f}",
            }
        )

    if any(reason["severity"] == "bad" for reason in reasons):
        return QualityStatus.BAD, reasons
    if reasons:
        return QualityStatus.DEGRADED, reasons
    return QualityStatus.OK, reasons


def _levels_and_atr(rows: tuple[CandleFeatureRow, ...]) -> tuple[float, float, float, float]:
    valid_rows = [row for row in rows if row.high is not None and row.low is not None and row.close is not None]
    if not valid_rows:
        return 0.0, 1.0, 1.0, 0.5

    highs = [float(row.high) for row in valid_rows]
    lows = [float(row.low) for row in valid_rows]
    closes = [float(row.close) for row in valid_rows]
    support = min(lows)
    resistance = max(highs)

    true_ranges: list[float] = []
    previous_close: float | None = None
    for row in valid_rows:
        high = float(row.high)
        low = float(row.low)
        if previous_close is None:
            tr = high - low
        else:
            tr = max(high - low, abs(high - previous_close), abs(low - previous_close))
        true_ranges.append(max(tr, 0.0))
        previous_close = float(row.close)

    atr = max(mean(true_ranges), 1e-6)
    last_price = closes[-1]

    if resistance <= support:
        resistance = support + max(atr, 1.0)
    if last_price < support:
        support = last_price - max(atr, 1.0)
    if last_price > resistance:
        resistance = last_price + max(atr, 1.0)

    return support, resistance, atr, last_price


def _directional_scores(rows: tuple[CandleFeatureRow, ...]) -> tuple[float, float]:
    valid_rows = [row for row in rows if row.open is not None and row.close is not None]
    if not valid_rows:
        return 10.0, 10.0

    bull_moves = sum(1 for row in valid_rows if float(row.close) > float(row.open))
    bear_moves = sum(1 for row in valid_rows if float(row.close) < float(row.open))
    total_moves = max(bull_moves + bear_moves, 1)

    bullish_ratio = bull_moves / total_moves
    bearish_ratio = bear_moves / total_moves

    long_score = min(100.0, max(0.0, 30.0 + bullish_ratio * 50.0))
    short_score = min(100.0, max(0.0, 30.0 + bearish_ratio * 50.0))
    return long_score, short_score


def _reject_score(
    *,
    quality_status: QualityStatus,
    degradation_reasons: list[dict[str, Any]],
    long_score: float,
    short_score: float,
) -> float:
    score = 10.0
    if quality_status == QualityStatus.DEGRADED:
        score += 20.0
    if quality_status == QualityStatus.BAD:
        score += 55.0

    for reason in degradation_reasons:
        if reason["code"] == "heavy_gaps":
            score += 8.0
        elif reason["code"] == "truncation":
            score += 6.0
        elif reason["code"] == "low_coverage":
            score += 12.0
        elif reason["code"] == "empty_window":
            score += 20.0

    directional_uncertainty = 1.0 - min(abs(long_score - short_score) / 100.0, 1.0)
    score += directional_uncertainty * 15.0
    return min(100.0, max(0.0, score))


def _market_regime(rows: tuple[CandleFeatureRow, ...], long_score: float, short_score: float) -> MarketRegime:
    valid_rows = [row for row in rows if row.open is not None and row.close is not None]
    if len(valid_rows) < 4:
        return MarketRegime.CHAOTIC
    drift = float(valid_rows[-1].close) - float(valid_rows[0].open)
    score_spread = abs(long_score - short_score)
    if score_spread <= 8.0:
        return MarketRegime.RANGE
    if abs(drift) > 0:
        return MarketRegime.TREND
    return MarketRegime.CHAOTIC


def _volatility_regime(atr: float, last_price: float) -> VolatilityRegime:
    ratio = 0.0 if last_price <= 0 else atr / last_price
    if ratio < 0.002:
        return VolatilityRegime.LOW
    if ratio < 0.01:
        return VolatilityRegime.NORMAL
    return VolatilityRegime.HIGH


def _dominant_side(rows: tuple[CandleFeatureRow, ...]) -> DominantSide:
    if not rows:
        return DominantSide.MIXED

    delta = sum(float(row.delta) for row in rows)
    if delta > 0:
        return DominantSide.BUYERS
    if delta < 0:
        return DominantSide.SELLERS
    return DominantSide.MIXED


def _confidence_hint(quality: QualityStatus, long_score: float, short_score: float, reject_score: float) -> float:
    spread_boost = min(abs(long_score - short_score) / 100.0, 0.35)
    base = 0.45 + spread_boost - (reject_score / 200.0)
    if quality == QualityStatus.DEGRADED:
        base -= 0.1
    if quality == QualityStatus.BAD:
        base = min(base, 0.15)
    return max(0.0, min(1.0, base))


def _entry_candidates(support_level: float, resistance_level: float) -> tuple[float, float, float]:
    width = max(resistance_level - support_level, 1.0)
    return (
        support_level + width * 0.25,
        support_level + width * 0.50,
        support_level + width * 0.75,
    )
