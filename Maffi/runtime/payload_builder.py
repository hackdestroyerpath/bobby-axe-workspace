from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from TRADING_ALGOS.common.tick_normalizer import (
    PARTIAL_REASON_EMPTY_WINDOW,
    PARTIAL_REASON_GAP_HEAVY,
    PARTIAL_REASON_PAGINATION,
    PARTIAL_REASON_RETENTION,
    NormalizationResult,
)
from TRADING_ALGOS.common.tick_to_features_engine import TickToFeaturesResult

from .enums import QualityStatus
from .models import MaffiPayload, PreprocessingResult


def build_maffi_payload(
    *,
    symbol: str,
    source: str,
    window_from: datetime,
    window_to: datetime,
    normalization_result: NormalizationResult,
    feature_result: TickToFeaturesResult | None = None,
    preprocessing_result: PreprocessingResult | None = None,
) -> MaffiPayload:
    reasons: list[dict[str, Any]] = []

    if normalization_result.empty_window:
        quality = QualityStatus.BAD
        reject_score = 80.0
        reasons.append({"code": "empty_window", "severity": "error"})
    elif normalization_result.is_partial:
        quality = QualityStatus.DEGRADED
        reject_score = 40.0
        mapping = {
            PARTIAL_REASON_GAP_HEAVY: "heavy_gaps",
            PARTIAL_REASON_PAGINATION: "truncation",
            PARTIAL_REASON_RETENTION: "low_coverage",
            PARTIAL_REASON_EMPTY_WINDOW: "empty_window",
        }
        for reason in normalization_result.partial_reasons:
            reasons.append({"code": mapping.get(reason, reason), "severity": "degrade"})
    else:
        quality = QualityStatus.OK
        reject_score = 18.0

    last_price = float(normalization_result.ticks[-1].price) if normalization_result.ticks else 0.0
    support_level = last_price * 0.997 if last_price else 0.0
    resistance_level = last_price * 1.004 if last_price else 0.0
    atr = max(last_price * 0.0012, 1.0) if last_price else 0.0

    if feature_result is not None:
        candles = feature_result.candles_by_timeframe.get("1m", ())
        if candles:
            highs = [float(c.high) for c in candles if c.high is not None]
            lows = [float(c.low) for c in candles if c.low is not None]
            closes = [float(c.close) for c in candles if c.close is not None]
            if highs and lows:
                support_level = min(lows)
                resistance_level = max(highs)
                last_price = closes[-1]
                atr = max((resistance_level - support_level) / max(len(candles), 1), 1.0)

    width = max(resistance_level - support_level, 3.0)
    entries = (
        support_level + width * 0.25,
        support_level + width * 0.5,
        support_level + width * 0.75,
    )

    long_score = 72.0 if quality != QualityStatus.BAD else 20.0
    short_score = 42.0
    if quality == QualityStatus.DEGRADED:
        long_score = 65.0

    degradation_trace: dict[str, Any] | None = None
    if preprocessing_result is not None:
        degradation_trace = asdict(preprocessing_result.feature_extraction.degradation)
        for flag in preprocessing_result.feature_extraction.degradation.triggered_flags:
            reasons.append({"code": flag, "severity": "degrade"})

    return MaffiPayload(
        schema_version="maffi-v1",
        symbol=symbol,
        generated_at_utc=window_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        source=source,
        input_quality_status=quality,
        market_regime="trend",
        volatility_regime="normal",
        dominant_side="buyers" if long_score >= short_score else "sellers",
        long_score=long_score,
        short_score=short_score,
        reject_score=reject_score,
        confidence_hint=0.75 if quality == QualityStatus.OK else 0.6 if quality == QualityStatus.DEGRADED else 0.3,
        entry_candidates=entries,
        support_level=support_level,
        resistance_level=resistance_level,
        last_price=last_price,
        atr=atr,
        context={
            "payload_builder": {
                "window_from": window_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "window_to": window_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "coverage_ratio": normalization_result.coverage_ratio,
                "degradation_reasons": reasons,
                "degradation_trace": degradation_trace,
            }
        },
    )
