from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from TRADING_ALGOS.ben_kim_packaging import (
    BenKimBatch,
    BenKimSymbolObject,
    OBJECT_STATUS_BLOCKED,
    OBJECT_STATUS_PARTIAL,
    OBJECT_STATUS_READY,
)

from .enums import DominantSide, MarketRegime, QualityStatus, VolatilityRegime
from .models import MaffiInputPayload, now_utc_iso
from .payload_builder import payload_to_dict

BRIDGE_SCHEMA_VERSION = "maffi-v1"
BRIDGE_SOURCE = "Ben_Kim_orchestration"

# Explicit bridge contract: which fields affect target Maffi payload groups.
BRIDGE_MAPPING_CONTRACT: dict[str, tuple[str, ...]] = {
    "scores": (
        "summary.state",
        "summary.strength",
        "summary.confidence",
        "meta.is_partial",
        "meta.partial_reason",
        "meta.coverage_ratio",
        "features.momentum_state",
        "features.structure_state",
        "features.pressure_side",
        "features.elliott_direction_candidate",
        "features.elliott_confidence_state",
    ),
    "quality_status": (
        "status",
        "object_readiness",
        "meta.is_partial",
        "meta.partial_reason",
        "meta.coverage_ratio",
        "errors[*].severity",
        "errors[*].code",
    ),
    "candidates": (
        "features.nearest_support",
        "features.nearest_resistance",
        "features.nearest_fib_level",
        "features.hv_poc",
        "features.distance_to_support",
        "features.distance_to_resistance",
    ),
}

_STATE_TO_BIAS = {
    "bullish": 1.0,
    "buyers": 1.0,
    "up": 1.0,
    "bearish": -1.0,
    "sellers": -1.0,
    "down": -1.0,
    "mixed": 0.0,
    "range": 0.0,
    "flat": 0.0,
    "unclear": 0.0,
}

_STRENGTH_MULTIPLIER = {
    "strong": 1.0,
    "medium": 0.65,
    "weak": 0.35,
    "low": 0.35,
}

_CONFIDENCE_MULTIPLIER = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4,
}

_TIMEFRAME_WEIGHT = {
    "60m": 1.0,
    "5m": 0.75,
    "1m": 0.5,
}

_PARTIAL_REASON_REJECT_BUMP = {
    "empty_window": 40.0,
    "retention_truncation": 8.0,
    "pagination_truncation": 8.0,
    "gap_heavy_window": 12.0,
}


def symbol_object_to_maffi_payload(symbol_object: BenKimSymbolObject) -> MaffiInputPayload:
    """Translate one BenKimSymbolObject into a MaffiInputPayload."""

    return _build_payload(
        symbol=symbol_object.symbol,
        source=symbol_object.source,
        generated_at_utc=symbol_object.generated_at,
        objects=(symbol_object,),
    )


def batch_to_maffi_payload(batch: BenKimBatch) -> MaffiInputPayload:
    """Translate BenKim batch into one aggregate MaffiInputPayload."""

    source = BRIDGE_SOURCE if len(batch.objects) > 1 else batch.objects[0].source
    generated_at = max((obj.generated_at for obj in batch.objects), default=now_utc_iso())
    return _build_payload(symbol=batch.symbol, source=source, generated_at_utc=generated_at, objects=batch.objects)


def payload_dict_from_symbol_object(symbol_object: BenKimSymbolObject) -> dict[str, Any]:
    return payload_to_dict(symbol_object_to_maffi_payload(symbol_object))


def payload_dict_from_batch(batch: BenKimBatch) -> dict[str, Any]:
    return payload_to_dict(batch_to_maffi_payload(batch))


def _build_payload(
    *,
    symbol: str,
    source: str,
    generated_at_utc: str,
    objects: Iterable[BenKimSymbolObject],
) -> MaffiInputPayload:
    objects = tuple(objects)

    quality = _derive_quality_status(objects)
    market_regime = _derive_market_regime(objects)
    volatility_regime = _derive_volatility_regime(objects)
    dominant_side = _derive_dominant_side(objects)

    long_score, short_score = _directional_scores(objects)
    reject_score = _reject_score(objects, quality)
    confidence_hint = _confidence_hint(long_score, short_score, reject_score, quality)

    support, resistance, last_price, atr, candidates = _derive_candidates_and_levels(objects)

    context = {
        "bridge": {
            "mapping_contract": BRIDGE_MAPPING_CONTRACT,
            "objects_used": len(objects),
            "readiness": {"ready": 0, "partial": 0, "blocked": 0},
            "meta": [
                {
                    "machine_id": obj.machine_id,
                    "strategy": obj.strategy,
                    "timeframe": obj.timeframe,
                    "status": obj.status,
                    "object_readiness": obj.object_readiness,
                    "partial_reason": obj.meta.get("partial_reason"),
                    "coverage_ratio": obj.meta.get("coverage_ratio"),
                }
                for obj in objects
            ],
        }
    }
    for obj in objects:
        if obj.object_readiness == OBJECT_STATUS_READY:
            context["bridge"]["readiness"]["ready"] += 1
        elif obj.object_readiness == OBJECT_STATUS_PARTIAL:
            context["bridge"]["readiness"]["partial"] += 1
        else:
            context["bridge"]["readiness"]["blocked"] += 1

    return MaffiInputPayload(
        schema_version=BRIDGE_SCHEMA_VERSION,
        symbol=symbol,
        generated_at_utc=generated_at_utc,
        source=source,
        input_quality_status=quality,
        market_regime=market_regime,
        volatility_regime=volatility_regime,
        dominant_side=dominant_side,
        long_score=long_score,
        short_score=short_score,
        reject_score=reject_score,
        confidence_hint=confidence_hint,
        entry_candidates=candidates,
        support_level=support,
        resistance_level=resistance,
        last_price=last_price,
        atr=atr,
        context=context,
    )


def _derive_quality_status(objects: tuple[BenKimSymbolObject, ...]) -> QualityStatus:
    if any(obj.status == "error" or obj.object_readiness == OBJECT_STATUS_BLOCKED for obj in objects):
        return QualityStatus.BAD

    for obj in objects:
        if obj.object_readiness == OBJECT_STATUS_PARTIAL:
            return QualityStatus.DEGRADED
        if obj.meta.get("is_partial"):
            return QualityStatus.DEGRADED
        coverage_ratio = _safe_float(obj.meta.get("coverage_ratio"), default=1.0)
        if coverage_ratio < 0.65:
            return QualityStatus.DEGRADED

    return QualityStatus.OK


def _directional_scores(objects: tuple[BenKimSymbolObject, ...]) -> tuple[float, float]:
    weighted_bias = 0.0
    total_weight = 0.0

    for obj in objects:
        state = str(obj.summary.get("state") or obj.features.get("summary_state") or "mixed").lower()
        strength = str(obj.summary.get("strength") or obj.features.get("summary_strength") or "weak").lower()
        confidence = str(obj.summary.get("confidence") or "medium").lower()

        base_weight = _TIMEFRAME_WEIGHT.get(obj.timeframe, 0.4)
        strength_weight = _STRENGTH_MULTIPLIER.get(strength, 0.35)
        confidence_weight = _CONFIDENCE_MULTIPLIER.get(confidence, 0.7)

        quality_penalty = 1.0
        if obj.object_readiness == OBJECT_STATUS_PARTIAL:
            quality_penalty = 0.65
        if obj.object_readiness == OBJECT_STATUS_BLOCKED:
            quality_penalty = 0.25

        weight = base_weight * strength_weight * confidence_weight * quality_penalty
        bias = _STATE_TO_BIAS.get(state, 0.0)

        weighted_bias += bias * weight
        total_weight += weight

    if total_weight <= 0:
        return 50.0, 50.0

    normalized = max(-1.0, min(1.0, weighted_bias / total_weight))
    long_score = 50.0 + normalized * 35.0
    short_score = 50.0 - normalized * 35.0
    return round(long_score, 4), round(short_score, 4)


def _reject_score(objects: tuple[BenKimSymbolObject, ...], quality: QualityStatus) -> float:
    score = 10.0
    if quality == QualityStatus.DEGRADED:
        score += 15.0
    if quality == QualityStatus.BAD:
        score += 55.0

    for obj in objects:
        if obj.object_readiness == OBJECT_STATUS_BLOCKED:
            score += 20.0
        if obj.object_readiness == OBJECT_STATUS_PARTIAL:
            score += 8.0

        partial_reason = str(obj.meta.get("partial_reason") or "")
        score += _PARTIAL_REASON_REJECT_BUMP.get(partial_reason, 0.0)

        for error in obj.errors:
            severity = str(error.get("severity") or "warning")
            score += 12.0 if severity == "error" else 4.0

    return round(max(0.0, min(100.0, score)), 4)


def _confidence_hint(long_score: float, short_score: float, reject_score: float, quality: QualityStatus) -> float:
    separation = abs(long_score - short_score) / 100.0
    confidence = 0.45 + separation * 0.5
    confidence -= reject_score / 200.0
    if quality == QualityStatus.DEGRADED:
        confidence -= 0.1
    if quality == QualityStatus.BAD:
        confidence = 0.0
    return round(max(0.0, min(1.0, confidence)), 4)


def _derive_market_regime(objects: tuple[BenKimSymbolObject, ...]) -> MarketRegime:
    bull = 0
    bear = 0
    mixed = 0
    for obj in objects:
        state = str(obj.summary.get("state") or "mixed").lower()
        bias = _STATE_TO_BIAS.get(state, 0.0)
        if bias > 0:
            bull += 1
        elif bias < 0:
            bear += 1
        else:
            mixed += 1

    if mixed >= max(bull, bear):
        return MarketRegime.RANGE
    if abs(bull - bear) <= 1 and (bull + bear) > 0:
        return MarketRegime.CHAOTIC
    return MarketRegime.TREND


def _derive_volatility_regime(objects: tuple[BenKimSymbolObject, ...]) -> VolatilityRegime:
    spans: list[float] = []
    for obj in objects:
        if "distance_to_support" in obj.features and "distance_to_resistance" in obj.features:
            dist_support = _safe_float(obj.features.get("distance_to_support"), default=0.0)
            dist_resistance = _safe_float(obj.features.get("distance_to_resistance"), default=0.0)
            spans.append(max(0.0, dist_support + dist_resistance))
    if not spans:
        return VolatilityRegime.NORMAL

    avg_span = sum(spans) / len(spans)
    if avg_span < 40:
        return VolatilityRegime.LOW
    if avg_span > 350:
        return VolatilityRegime.HIGH
    return VolatilityRegime.NORMAL


def _derive_dominant_side(objects: tuple[BenKimSymbolObject, ...]) -> DominantSide:
    votes = defaultdict(int)
    for obj in objects:
        state = str(
            obj.features.get("pressure_side")
            or obj.summary.get("state")
            or obj.features.get("trend_state")
            or "mixed"
        ).lower()
        bias = _STATE_TO_BIAS.get(state, 0.0)
        if bias > 0:
            votes[DominantSide.BUYERS] += 1
        elif bias < 0:
            votes[DominantSide.SELLERS] += 1
        else:
            votes[DominantSide.MIXED] += 1

    if votes[DominantSide.BUYERS] > votes[DominantSide.SELLERS]:
        return DominantSide.BUYERS
    if votes[DominantSide.SELLERS] > votes[DominantSide.BUYERS]:
        return DominantSide.SELLERS
    return DominantSide.MIXED


def _derive_candidates_and_levels(objects: tuple[BenKimSymbolObject, ...]) -> tuple[float, float, float, float, tuple[float, ...]]:
    supports: list[float] = []
    resistances: list[float] = []
    pivots: list[float] = []

    for obj in objects:
        supports.extend(
            [
                _safe_float(obj.features.get("nearest_support"), default=0.0),
                _safe_float(obj.features.get("nearest_fib_level"), default=0.0),
            ]
        )
        resistances.append(_safe_float(obj.features.get("nearest_resistance"), default=0.0))
        pivots.append(_safe_float(obj.features.get("hv_poc"), default=0.0))

    supports = [x for x in supports if x > 0]
    resistances = [x for x in resistances if x > 0]
    pivots = [x for x in pivots if x > 0]

    if not supports and pivots:
        supports = [min(pivots)]
    if not resistances and pivots:
        resistances = [max(pivots)]

    support = min(supports) if supports else 0.0
    resistance = max(resistances) if resistances else max(support + 1.0, 1.0)
    if resistance <= support:
        resistance = support + 1.0

    if pivots:
        last_price = sorted(pivots)[len(pivots) // 2]
    else:
        last_price = round((support + resistance) / 2.0, 4)

    if last_price < support:
        last_price = support
    if last_price > resistance:
        last_price = resistance

    atr = round(max((resistance - support) / 6.0, 1e-6), 6)

    center = last_price
    span = max(atr, 1.0)
    candidates = tuple(
        round(value, 4)
        for value in sorted(
            {
                max(support, center - span),
                center,
                min(resistance, center + span),
            }
        )
    )

    if len(candidates) < 3:
        candidates = (round(support, 4), round(center, 4), round(resistance, 4))

    return round(support, 4), round(resistance, 4), round(last_price, 4), atr, candidates


def _safe_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
