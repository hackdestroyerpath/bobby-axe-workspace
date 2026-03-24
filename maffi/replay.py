from __future__ import annotations

from copy import deepcopy
from typing import Any

from .decision_engine import decide
from .models import MaffiOutput


def deterministic_replay(payload: dict[str, Any]) -> tuple[MaffiOutput, MaffiOutput]:
    first = decide(deepcopy(payload))
    second = decide(deepcopy(payload))
    return first, second
