from __future__ import annotations

from copy import deepcopy
from typing import Any

from .decision_engine import decide
from .models import MaffiOutput


def deterministic_replay(payload: dict[str, Any]) -> tuple[MaffiOutput, MaffiOutput]:
    fixed_generated_at = str(payload.get("generated_at_utc", "1970-01-01T00:00:00Z"))
    first = decide(deepcopy(payload), generated_at_override=fixed_generated_at)
    second = decide(deepcopy(payload), generated_at_override=fixed_generated_at)
    return first, second
