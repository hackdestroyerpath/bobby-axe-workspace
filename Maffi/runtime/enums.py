from __future__ import annotations

from enum import StrEnum


class Decision(StrEnum):
    REJECT = "reject"
    LONG = "long"
    SHORT = "short"


class QualityStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    BAD = "bad"


class MarketRegime(StrEnum):
    TREND = "trend"
    RANGE = "range"
    CHAOTIC = "chaotic"


class DominantSide(StrEnum):
    BUYERS = "buyers"
    SELLERS = "sellers"
    MIXED = "mixed"


class VolatilityRegime(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
