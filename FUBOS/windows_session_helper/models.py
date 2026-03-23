from __future__ import annotations

from dataclasses import dataclass

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_FAILED = "failed"

STATE_LAUNCHED = "launched"
STATE_AUTO_STARTED = "auto_started"
STATE_IDLE = "idle"
STATE_STALE = "stale"
STATE_FRESH = "fresh"
STATE_DEAD = "dead"
STATE_LAUNCH_FAILED = "launch_failed"
STATE_AUTO_START_FAILED = "auto_start_failed"
STATE_SEND_FAILED = "send_failed"
STATE_STOPPED = "stopped"
STATE_IMPORTED = "imported"
STATE_INACTIVE = "inactive"
STATE_COMMAND_SENT = "command_sent"


@dataclass
class SessionProfile:
    name: str
    command: str
    status: str = STATUS_INACTIVE
    notes: str = ""
    shell_type: str = "powershell"
    auto_start: bool = False
    last_error: str = ""
    launch_count: int = 0
    last_launch_ok: bool = False
    process_id: int | None = None
    last_seen_ts: float = 0.0
    state_hint: str = STATE_INACTIVE


DEFAULT_SESSIONS = [
    SessionProfile(name="Jack VPS", command="powershell -NoExit -Command ssh openclaw@YOUR_VPS_IP", shell_type="ssh", auto_start=True),
    SessionProfile(name="Extra Server", command="powershell -NoExit -Command ssh user@YOUR_OTHER_HOST", shell_type="ssh", auto_start=False),
    SessionProfile(name="Local PowerShell", command="powershell -NoExit", shell_type="powershell", auto_start=False),
]
