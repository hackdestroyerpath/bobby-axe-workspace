from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_FIXTURES_ROOT = Path(__file__).resolve().parent


def load_json_fixture(relative_path: str) -> dict[str, Any]:
    fixture_path = _FIXTURES_ROOT / relative_path
    with fixture_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_maffi_llm_flow_fixture(file_name: str) -> dict[str, Any]:
    return load_json_fixture(f"maffi_llm_flow/{file_name}")
