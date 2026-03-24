from __future__ import annotations

from enum import Enum

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover - compatibility path for Python 3.10
    class StrEnum(str, Enum):
        """Minimal StrEnum-compatible fallback for Python < 3.11."""


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
