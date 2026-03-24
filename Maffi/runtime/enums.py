from __future__ import annotations

from enum import Enum


class Decision(str, Enum):
    LONG = "long"
    SHORT = "short"
    REJECT = "reject"


class QualityStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    BAD = "bad"
