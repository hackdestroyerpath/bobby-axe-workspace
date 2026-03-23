from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

from models import (
    STATE_AUTO_START_FAILED,
    STATE_COMMAND_SENT,
    STATE_DEAD,
    STATE_FRESH,
    STATE_INACTIVE,
    STATE_LAUNCH_FAILED,
    STATE_STOPPED,
    STATUS_ACTIVE,
    STATUS_FAILED,
    STATUS_INACTIVE,
    SessionProfile,
)


class SessionRuntimeManager:
    def __init__(self, log_dir: Path, log_callback: Callable[[str], None]):
        self.log_dir = log_dir
        self.log_callback = log_callback
        self.action_log_path = log_dir / "actions.jsonl"
        self.process_handles: dict[str, subprocess.Popen] = {}
        self.dead_logged: set[str] = set()

    def record_action(self, action: str, session: str | None = None, result: str = "ok", error: str = "", extra: dict | None = None) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "action": action,
            "session": session,
            "result": result,
            "error": error,
        }
        if extra:
            payload.update(extra)
        with self.action_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def get_live_process(self, session: SessionProfile) -> subprocess.Popen | None:
        proc = self.process_handles.get(session.name)
        if proc is None:
            return None
        return proc if proc.poll() is None else None

    def stream_output(self, sessions: list[SessionProfile], session_name: str, stream, stream_name: str) -> None:
        for raw_line in iter(stream.readline, ""):
            line = raw_line.rstrip()
            if not line:
                continue
            session = next((item for item in sessions if item.name == session_name), None)
            if session is not None:
                session.last_seen_ts = time.time()
                if session.status == STATUS_ACTIVE and session.state_hint == STATE_COMMAND_SENT:
                    session.state_hint = STATE_FRESH
            self.log_callback(f"[{session_name}:{stream_name}] {line}")
        try:
            stream.close()
        except Exception:
            pass

    def attach_output_readers(self, sessions: list[SessionProfile], session: SessionProfile, proc: subprocess.Popen) -> None:
        if proc.stdout is not None:
            threading.Thread(target=self.stream_output, args=(sessions, session.name, proc.stdout, "stdout"), daemon=True).start()
        if proc.stderr is not None:
            threading.Thread(target=self.stream_output, args=(sessions, session.name, proc.stderr, "stderr"), daemon=True).start()

    def mark_session_dead(self, session: SessionProfile, return_code: int | None = None) -> None:
        session.status = STATUS_FAILED if return_code not in (0, None) else STATUS_INACTIVE
        session.last_launch_ok = False
        session.process_id = None
        session.state_hint = STATE_DEAD
        session.last_seen_ts = time.time()
        if return_code is not None:
            session.last_error = f"process exited with code {return_code}"
        self.process_handles.pop(session.name, None)

    def stop_session(self, session: SessionProfile, reason: str = "stopped by operator") -> None:
        proc = self.process_handles.get(session.name)
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        self.process_handles.pop(session.name, None)
        self.dead_logged.discard(session.name)
        session.status = STATUS_INACTIVE
        session.process_id = None
        session.state_hint = STATE_STOPPED
        session.last_error = ""
        session.last_seen_ts = time.time()
        self.log_callback(f"[ok] stopped: {session.name} ({reason})")
        self.record_action("stop", session=session.name, result="ok", extra={"reason": reason})

    def launch_session(self, sessions: list[SessionProfile], session: SessionProfile, source: str) -> None:
        live = self.get_live_process(session)
        if live is not None:
            self.log_callback(f"[info] replacing live process for {session.name} before relaunch")
            self.stop_session(session, reason="reconnect requested")
        try:
            proc = subprocess.Popen(
                session.command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self.process_handles[session.name] = proc
            self.dead_logged.discard(session.name)
            session.status = STATUS_ACTIVE
            session.last_error = ""
            session.launch_count += 1
            session.last_launch_ok = True
            session.process_id = getattr(proc, "pid", None)
            session.last_seen_ts = time.time()
            session.state_hint = source
            self.attach_output_readers(sessions, session, proc)
            self.log_callback(f"[ok] launched: {session.name} | pid={session.process_id} | source={source}")
            self.record_action("launch", session=session.name, result="ok", extra={"pid": session.process_id, "source": source})
        except Exception as exc:
            session.status = STATUS_FAILED
            session.last_error = str(exc)
            session.launch_count += 1
            session.last_launch_ok = False
            session.process_id = None
            session.state_hint = STATE_AUTO_START_FAILED if source == "auto_started" else STATE_LAUNCH_FAILED
            self.log_callback(f"[err] failed to launch {session.name}: {exc}")
            self.record_action("launch", session=session.name, result="failed", error=str(exc), extra={"source": source})

    def send_command(self, session: SessionProfile, command: str) -> tuple[bool, str | None]:
        proc = self.get_live_process(session)
        if not proc or proc.stdin is None:
            self.record_action("send", session=session.name, result="failed", error="session not managed")
            return False, "session not managed"
        try:
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
            session.last_seen_ts = time.time()
            session.state_hint = STATE_COMMAND_SENT
            session.last_error = ""
            self.record_action("send", session=session.name, result="ok", extra={"command": command})
            return True, None
        except Exception as exc:
            session.last_error = str(exc)
            session.status = STATUS_FAILED
            session.state_hint = "send_failed"
            self.record_action("send", session=session.name, result="failed", error=str(exc), extra={"command": command})
            return False, str(exc)
