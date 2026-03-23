from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from models import DEFAULT_SESSIONS, STATE_INACTIVE, STATUS_INACTIVE, SessionProfile


class SessionStore:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load(self) -> list[SessionProfile]:
        if self.config_path.exists():
            data = json.loads(self.config_path.read_text())
            return [
                SessionProfile(
                    name=item.get("name", "Unnamed"),
                    command=item.get("command", "powershell -NoExit"),
                    status=item.get("status", STATUS_INACTIVE),
                    notes=item.get("notes", ""),
                    shell_type=item.get("shell_type", "powershell"),
                    auto_start=bool(item.get("auto_start", False)),
                    last_error=item.get("last_error", ""),
                    launch_count=int(item.get("launch_count", 0)),
                    last_launch_ok=bool(item.get("last_launch_ok", False)),
                    process_id=item.get("process_id"),
                    last_seen_ts=float(item.get("last_seen_ts", 0.0)),
                    state_hint=item.get("state_hint", STATE_INACTIVE),
                )
                for item in data
            ]
        self.save(DEFAULT_SESSIONS)
        return DEFAULT_SESSIONS.copy()

    def save(self, sessions: list[SessionProfile]) -> None:
        payload = [asdict(x) for x in sessions]
        self.config_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
