from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Mapping

from TRADING_ALGOS.ben_kim_packaging import BenKimBatch, BenKimSymbolObject

from .enums import QualityStatus
from .models import MaffiPayload

BRIDGE_MAPPING_CONTRACT = ("scores", "quality_status", "candidates")


def payload_dict_from_symbol_object(symbol_object: BenKimSymbolObject) -> dict[str, Any]:
    return _payload_from_objects((symbol_object,))


def payload_dict_from_batch(batch: BenKimBatch) -> dict[str, Any]:
    return _payload_from_objects(batch.objects)


def batch_to_maffi_payload(batch: BenKimBatch) -> MaffiPayload:
    payload = payload_dict_from_batch(batch)
    payload["input_quality_status"] = QualityStatus(payload["input_quality_status"])
    return MaffiPayload(**payload)


def _payload_from_objects(objects: tuple[BenKimSymbolObject, ...] | list[BenKimSymbolObject]) -> dict[str, Any]:
    first = objects[0]
    bullish = 0.0
    bearish = 0.0
    partial_count = 0
    supports: list[float] = []
    resistances: list[float] = []

    for obj in objects:
        state = str(obj.summary.get("state", "")).lower()
        strength = str(obj.summary.get("strength", "medium")).lower()
        mult = {"weak": 0.8, "medium": 1.0, "strong": 1.2}.get(strength, 1.0)
        if state in {"bullish", "buyers", "up"}:
            bullish += 10 * mult
        elif state in {"bearish", "sellers", "down"}:
            bearish += 10 * mult

        if obj.status == "partial":
            partial_count += 1

        features = obj.features
        if "nearest_support" in features:
            supports.append(float(features["nearest_support"]))
        if "nearest_resistance" in features:
            resistances.append(float(features["nearest_resistance"]))

    quality = QualityStatus.OK if partial_count == 0 else QualityStatus.DEGRADED
    reject_score = 15.0 + min(partial_count * 5.0, 30.0)

    support = mean(supports) if supports else 0.0
    resistance = mean(resistances) if resistances else 0.0
    last_price = (support + resistance) / 2 if support and resistance else support or resistance
    atr = max((resistance - support) / 5, 1.0) if support and resistance else 100.0

    payload = {
        "schema_version": "maffi-v1",
        "symbol": first.symbol,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": first.source,
        "input_quality_status": quality.value,
        "market_regime": "trend",
        "volatility_regime": "normal",
        "dominant_side": "buyers" if bullish >= bearish else "sellers",
        "long_score": 50.0 + bullish,
        "short_score": 30.0 + bearish,
        "reject_score": reject_score,
        "confidence_hint": 0.75 if quality == QualityStatus.OK else 0.62,
        "entry_candidates": [
            support + (resistance - support) * 0.3,
            support + (resistance - support) * 0.5,
            support + (resistance - support) * 0.7,
        ],
        "support_level": support,
        "resistance_level": resistance,
        "last_price": last_price,
        "atr": atr,
        "context": {
            "bridge": {
                "objects": [asdict(o) for o in objects],
                "partial_count": partial_count,
            }
        },
    }
    return payload
