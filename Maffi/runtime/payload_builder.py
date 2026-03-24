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
from .models import (
    AlgoPayload,
    GridCandidateScore,
    GridCandidatesBlock,
    GridGeometryHintsBlock,
    MarketRegimeBlock,
    MarketSnapshotBlock,
    MaffiPayload,
    OrderFlowBlock,
    PreprocessingResult,
    PriceStructureBlock,
    PromptControlBlock,
    QualityTrustBlock,
    RequestContextBlock,
    SupportResistanceBlock,
    VolatilityBlock,
)


def build_llm_algo_payload(
    *,
    symbol: str,
    window_from: datetime,
    window_to: datetime,
    quality: QualityStatus,
    last_price: float,
    support_level: float,
    resistance_level: float,
    atr: float,
    coverage_ratio: float,
    reasons: list[dict[str, Any]],
    preprocessing_result: PreprocessingResult | None = None,
) -> AlgoPayload:
    degradation_flags: tuple[str, ...] = ()
    data_quality_score = 0.90 if quality == QualityStatus.OK else 0.62 if quality == QualityStatus.DEGRADED else 0.20
    payload_confidence = 0.82 if quality == QualityStatus.OK else 0.58 if quality == QualityStatus.DEGRADED else 0.25
    largest_gap_seconds = None
    outlier_ratio = None
    liquidity_quality_score = 0.86 if quality == QualityStatus.OK else 0.58 if quality == QualityStatus.DEGRADED else 0.22

    market_regime = "trend_up"
    volatility_regime = "normal"
    trend_strength_score = 0.72
    trend_persistence_score = 0.68
    mean_reversion_score = 0.31
    chop_score = 0.24
    noise_score = 0.21
    reversal_frequency_score = 0.29

    realized_vol_5m = atr / max(last_price, 1.0)
    realized_vol_1m = realized_vol_5m * 0.6

    support_zone_low = support_level
    support_zone_high = support_level + atr * 0.25
    resistance_zone_low = resistance_level - atr * 0.25
    resistance_zone_high = resistance_level

    recommended_price_down = support_level
    recommended_price_up = resistance_level
    recommended_grid_count_min = 6
    recommended_grid_count_max = 12
    recommended_grid_step = max((recommended_price_up - recommended_price_down) / recommended_grid_count_max, 1.0)

    if preprocessing_result is not None:
        features = preprocessing_result.features
        degradation = preprocessing_result.feature_extraction.degradation
        degradation_flags = tuple(str(flag) for flag in degradation.triggered_flags)
        largest_gap_seconds = float(features.quality_trust.largest_gap_seconds)
        outlier_ratio = float(features.quality_trust.outlier_ratio)
        data_quality_score = max(0.0, min((features.quality_trust.coverage_ratio + features.quality_trust.liquidity_quality_score + features.quality_trust.payload_confidence) / 3.0, 1.0))
        payload_confidence = float(features.quality_trust.payload_confidence)
        liquidity_quality_score = float(features.quality_trust.liquidity_quality_score)

        market_regime_map = {"trend": "trend_up", "ranging": "range_balanced", "noisy": "chaotic_high_risk"}
        market_regime = market_regime_map.get(features.regime.market_regime_label, "range_balanced")
        volatility_regime = features.volatility_regime.label
        trend_strength_score = round(float(features.regime.trend_strength_score), 6)
        trend_persistence_score = round(float(features.regime.trend_persistence_score), 6)
        mean_reversion_score = round(float(features.regime.mean_reversion_score), 6)
        chop_score = round(float(features.regime.chop_score), 6)
        noise_score = round(float(features.regime.noise_score), 6)
        reversal_frequency_score = round(float(features.regime.reversal_frequency_score), 6)

        support_level = float(features.support_resistance.support)
        resistance_level = float(features.support_resistance.resistance)
        last_price = float(features.market_snapshot.last_price)
        support_zone_low = float(features.support_resistance_features.support_zone_low)
        support_zone_high = float(features.support_resistance_features.support_zone_high)
        resistance_zone_low = float(features.support_resistance_features.resistance_zone_low)
        resistance_zone_high = float(features.support_resistance_features.resistance_zone_high)
        recommended_price_down = float(features.support_resistance_features.support_zone_low)
        recommended_price_up = float(features.support_resistance_features.resistance_zone_high)
        realized_vol_1m = float(features.volatility.realized_vol_1m or 0.0)
        realized_vol_5m = float(features.volatility.realized_vol_5m or 0.0)
        atr = float(features.volatility.atr_like_5m or atr)
        volatility_regime = features.volatility.volatility_regime_label

    width = max(recommended_price_up - recommended_price_down, 3.0)
    candidate_scores = (
        GridCandidateScore(
            candidate_id="gc-1",
            price_down=recommended_price_down,
            price_up=recommended_price_up,
            grid_count=8,
            grid_step=width / 8,
            efficiency_score=0.78,
            range_utilization_score=0.74,
            oscillation_score=0.72,
            step_quality_score=0.77,
            stability_score=0.76,
            boundary_respect_score=0.79,
            candidate_notes=("baseline corridor",),
        ),
        GridCandidateScore(
            candidate_id="gc-2",
            price_down=recommended_price_down + width * 0.05,
            price_up=recommended_price_up - width * 0.05,
            grid_count=10,
            grid_step=(width * 0.9) / 10,
            efficiency_score=0.83,
            range_utilization_score=0.81,
            oscillation_score=0.79,
            step_quality_score=0.82,
            stability_score=0.78,
            boundary_respect_score=0.84,
            candidate_notes=("tightened efficient corridor",),
        ),
        GridCandidateScore(
            candidate_id="gc-3",
            price_down=recommended_price_down + width * 0.1,
            price_up=recommended_price_up - width * 0.1,
            grid_count=12,
            grid_step=(width * 0.8) / 12,
            efficiency_score=0.76,
            range_utilization_score=0.73,
            oscillation_score=0.80,
            step_quality_score=0.70,
            stability_score=0.74,
            boundary_respect_score=0.78,
            candidate_notes=("dense inner corridor",),
        ),
    )

    return AlgoPayload(
        request_context=RequestContextBlock(
            ticker=symbol,
            timeframe="1m",
            request_ts_utc=window_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
            direction="long",
            exchange="binance",
            lookback_window_minutes=max(int((window_to - window_from).total_seconds() // 60), 1),
            payload_version="maffi-llm-v1",
        ),
        market_snapshot=MarketSnapshotBlock(
            last_price=last_price,
            mark_price=last_price,
            index_price=last_price,
            vwap_1m=features.market_snapshot.vwap_1m if preprocessing_result is not None else last_price,
            vwap_5m=features.market_snapshot.vwap_5m if preprocessing_result is not None else last_price,
            vwap_15m=features.market_snapshot.vwap_15m if preprocessing_result is not None else last_price,
            trade_count_1m=features.market_snapshot.trade_count_1m if preprocessing_result is not None else 3,
            trade_count_5m=features.market_snapshot.trade_count_5m if preprocessing_result is not None else 12,
            volume_1m=features.market_snapshot.volume_1m if preprocessing_result is not None else 1.0,
            volume_5m=features.market_snapshot.volume_5m if preprocessing_result is not None else 5.0,
            notional_1m=features.market_snapshot.notional_1m if preprocessing_result is not None else last_price,
            notional_5m=features.market_snapshot.notional_5m if preprocessing_result is not None else last_price * 5,
        ),
        price_structure=PriceStructureBlock(
            open_1m=features.price_structure.open_1m if preprocessing_result is not None else last_price,
            high_1m=features.price_structure.high_1m if preprocessing_result is not None else resistance_level,
            low_1m=features.price_structure.low_1m if preprocessing_result is not None else support_level,
            close_1m=features.price_structure.close_1m if preprocessing_result is not None else last_price,
            open_5m=features.price_structure.open_5m if preprocessing_result is not None else last_price,
            high_5m=features.price_structure.high_5m if preprocessing_result is not None else resistance_level,
            low_5m=features.price_structure.low_5m if preprocessing_result is not None else support_level,
            close_5m=features.price_structure.close_5m if preprocessing_result is not None else last_price,
            local_high_15m=features.price_structure.local_high_15m if preprocessing_result is not None else resistance_level,
            local_low_15m=features.price_structure.local_low_15m if preprocessing_result is not None else support_level,
            range_width_1m=features.price_structure.range_width_1m if preprocessing_result is not None else max(resistance_level - support_level, 0.0),
            range_width_5m=features.price_structure.range_width_5m if preprocessing_result is not None else max(resistance_level - support_level, 0.0),
            close_position_in_1m_range=features.price_structure.close_position_in_1m_range if preprocessing_result is not None else 0.5,
            close_position_in_5m_range=features.price_structure.close_position_in_5m_range if preprocessing_result is not None else 0.5,
            distance_to_local_high=features.price_structure.distance_to_local_high if preprocessing_result is not None else max(resistance_level - last_price, 0.0),
            distance_to_local_low=features.price_structure.distance_to_local_low if preprocessing_result is not None else max(last_price - support_level, 0.0),
        ),
        volatility=VolatilityBlock(
            atr_like_1m=features.volatility.atr_like_1m if preprocessing_result is not None else atr * 0.6,
            atr_like_5m=features.volatility.atr_like_5m if preprocessing_result is not None else atr,
            realized_vol_1m=realized_vol_1m,
            realized_vol_5m=realized_vol_5m,
            return_std_1m=features.volatility.return_std_1m if preprocessing_result is not None else realized_vol_1m,
            return_std_5m=features.volatility.return_std_5m if preprocessing_result is not None else realized_vol_5m,
            volatility_percentile_1h=features.volatility.volatility_percentile_1h if preprocessing_result is not None else 0.55,
            volatility_regime=volatility_regime,
            impulse_size_last_move=features.volatility.impulse_size_last_move if preprocessing_result is not None else atr * 1.5,
            impulse_duration_seconds=features.volatility.impulse_duration_seconds if preprocessing_result is not None else 300.0,
            volatility_stability_score=features.volatility.volatility_stability_score if preprocessing_result is not None else max(0.1, 1.0 - noise_score),
        ),
        order_flow=OrderFlowBlock(
            buy_volume_1m=features.order_flow.buy_volume_1m if preprocessing_result is not None else 1.2,
            sell_volume_1m=features.order_flow.sell_volume_1m if preprocessing_result is not None else 0.8,
            buy_volume_5m=features.order_flow.buy_volume_5m if preprocessing_result is not None else 6.5,
            sell_volume_5m=features.order_flow.sell_volume_5m if preprocessing_result is not None else 4.2,
            delta_1m=features.order_flow.delta_1m if preprocessing_result is not None else 0.4,
            delta_5m=features.order_flow.delta_5m if preprocessing_result is not None else 2.3,
            cumulative_delta_5m=features.order_flow.cumulative_delta_5m if preprocessing_result is not None else 3.1,
            imbalance_ratio_1m=features.order_flow.imbalance_ratio_1m if preprocessing_result is not None else 1.2,
            imbalance_ratio_5m=features.order_flow.imbalance_ratio_5m if preprocessing_result is not None else 1.3,
            aggression_score_buy=features.order_flow.aggression_score_buy if preprocessing_result is not None else 0.66,
            aggression_score_sell=features.order_flow.aggression_score_sell if preprocessing_result is not None else 0.42,
            dominant_side=features.order_flow.dominant_side if preprocessing_result is not None else "buyers",
            order_flow_confidence=features.order_flow.order_flow_confidence if preprocessing_result is not None else 0.71,
        ),
        market_regime=MarketRegimeBlock(
            market_regime=market_regime,
            regime_confidence=features.regime.regime_confidence if preprocessing_result is not None else 0.74,
            trend_strength_score=trend_strength_score,
            trend_persistence_score=trend_persistence_score,
            mean_reversion_score=mean_reversion_score,
            chop_score=chop_score,
            noise_score=noise_score,
            reversal_frequency_score=reversal_frequency_score,
        ),
        support_resistance=SupportResistanceBlock(
            support_zone_low=support_zone_low,
            support_zone_high=support_zone_high,
            resistance_zone_low=resistance_zone_low,
            resistance_zone_high=resistance_zone_high,
            nearest_support_distance=features.support_resistance_features.nearest_support_distance if preprocessing_result is not None else max(last_price - support_level, 0.0),
            nearest_resistance_distance=features.support_resistance_features.nearest_resistance_distance if preprocessing_result is not None else max(resistance_level - last_price, 0.0),
            boundary_reaction_score=features.support_resistance_features.boundary_reaction_score if preprocessing_result is not None else 0.76,
            bounce_frequency_score=features.support_resistance_features.bounce_frequency_score if preprocessing_result is not None else 0.64,
            wick_rejection_score_upper=features.support_resistance_features.wick_rejection_score_upper if preprocessing_result is not None else 0.59,
            wick_rejection_score_lower=features.support_resistance_features.wick_rejection_score_lower if preprocessing_result is not None else 0.62,
            level_respect_score=features.support_resistance_features.level_respect_score if preprocessing_result is not None else 0.73,
        ),
        grid_geometry_hints=GridGeometryHintsBlock(
            recommended_price_down=recommended_price_down,
            recommended_price_up=recommended_price_up,
            recommended_grid_step=recommended_grid_step,
            recommended_grid_count_min=recommended_grid_count_min,
            recommended_grid_count_max=recommended_grid_count_max,
            recommended_tp_zone=recommended_price_up + atr * 0.35,
            recommended_sl_zone=recommended_price_down - atr * 0.35,
            grid_width_hint=width,
            grid_density_hint="balanced" if width / max(recommended_grid_count_max, 1) >= atr * 0.08 else "dense",
        ),
        grid_candidates=GridCandidatesBlock(candidates=candidate_scores),
        quality_trust=QualityTrustBlock(
            input_quality_status=quality.value,
            data_quality_score=data_quality_score,
            coverage_ratio=features.quality_trust.coverage_ratio if preprocessing_result is not None else coverage_ratio,
            largest_gap_seconds=largest_gap_seconds,
            outlier_ratio=outlier_ratio,
            liquidity_quality_score=liquidity_quality_score,
            payload_confidence=payload_confidence,
            degradation_flags=degradation_flags,
        ),
        prompt_control=PromptControlBlock(),
        metadata={
            "source": "payload_builder",
            "degradation_reasons": reasons,
        },
    )


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

    algo_payload = build_llm_algo_payload(
        symbol=symbol,
        window_from=window_from,
        window_to=window_to,
        quality=quality,
        last_price=last_price,
        support_level=support_level,
        resistance_level=resistance_level,
        atr=atr,
        coverage_ratio=normalization_result.coverage_ratio,
        reasons=reasons,
        preprocessing_result=preprocessing_result,
    )

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
                "algo_payload": asdict(algo_payload),
            }
        },
    )
