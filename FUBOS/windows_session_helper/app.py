from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "sessions.json"
LOG_DIR = APP_DIR / "logs"
ACTION_LOG_PATH = LOG_DIR / "actions.jsonl"

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


class SessionEditDialog(QDialog):
    def __init__(self, profile: SessionProfile, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Session")
        self.name_edit = QLineEdit(profile.name)
        self.command_edit = QLineEdit(profile.command)
        self.notes_edit = QLineEdit(profile.notes)
        self.shell_edit = QLineEdit(profile.shell_type)
        self.auto_start_edit = QLineEdit("true" if profile.auto_start else "false")

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("Command", self.command_edit)
        form.addRow("Notes", self.notes_edit)
        form.addRow("Shell type", self.shell_edit)
        form.addRow("Auto start (true/false)", self.auto_start_edit)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btns = QHBoxLayout()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(btns)
        self.setLayout(layout)

    def to_profile(self, old: SessionProfile) -> SessionProfile:
        return SessionProfile(
            name=self.name_edit.text().strip() or old.name,
            command=self.command_edit.text().strip() or old.command,
            status=old.status,
            notes=self.notes_edit.text().strip(),
            shell_type=self.shell_edit.text().strip() or old.shell_type,
            auto_start=self.auto_start_edit.text().strip().lower() == "true",
            last_error=old.last_error,
            launch_count=old.launch_count,
            last_launch_ok=old.last_launch_ok,
            process_id=old.process_id,
            last_seen_ts=old.last_seen_ts,
            state_hint=old.state_hint,
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Boss Session Helper — Control Panel")
        self.resize(1000, 640)
        self.sessions = self.load_sessions()
        self.selected_index = 0
        self.process_handles: dict[str, subprocess.Popen] = {}
        self._dead_logged: set[str] = set()

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select)

        self.status_label = QLabel("Status: —")
        self.dashboard_label = QLabel("Dashboard: —")
        self.command_label = QLabel("Command: —")
        self.command_label.setWordWrap(True)
        self.notes_label = QLabel("Notes: —")
        self.notes_label.setWordWrap(True)
        self.meta_label = QLabel("Meta: —")
        self.meta_label.setWordWrap(True)

        self.add_btn = QPushButton("Add Session")
        self.add_btn.clicked.connect(self.add_session)
        self.import_btn = QPushButton("Import Profiles")
        self.import_btn.clicked.connect(self.import_profiles)
        self.export_btn = QPushButton("Export Profiles")
        self.export_btn.clicked.connect(self.export_profiles)
        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.clicked.connect(self.duplicate_session)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_session)
        self.reconnect_btn = QPushButton("Connect / Reconnect")
        self.reconnect_btn.clicked.connect(self.reconnect_selected)
        self.stop_btn = QPushButton("Stop Session")
        self.stop_btn.clicked.connect(self.stop_selected)
        self.mark_inactive_btn = QPushButton("Mark Inactive")
        self.mark_inactive_btn.clicked.connect(self.mark_inactive)
        self.edit_btn = QPushButton("Edit Session")
        self.edit_btn.clicked.connect(self.edit_selected)

        self.selected_label = QLabel("Selected target: —")
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("Type command here, then Send to Selected...")
        self.command_input.setFixedHeight(100)
        self.send_btn = QPushButton("Send to Selected")
        self.send_btn.clicked.connect(self.send_command)
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)

        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setPlaceholderText("Helper log / operator notes...")

        left = QVBoxLayout()
        left.addWidget(QLabel("Sessions"))
        left.addWidget(self.list_widget)

        right = QVBoxLayout()
        right.addWidget(self.selected_label)
        right.addWidget(self.dashboard_label)
        right.addWidget(self.status_label)
        right.addWidget(self.command_label)
        right.addWidget(self.notes_label)
        right.addWidget(self.meta_label)

        row = QHBoxLayout()
        row.addWidget(self.add_btn)
        row.addWidget(self.import_btn)
        row.addWidget(self.export_btn)
        row.addWidget(self.duplicate_btn)
        row.addWidget(self.delete_btn)
        row.addWidget(self.reconnect_btn)
        row.addWidget(self.stop_btn)
        row.addWidget(self.mark_inactive_btn)
        row.addWidget(self.edit_btn)
        right.addLayout(row)
        right.addSpacing(16)
        right.addWidget(QLabel("Shared command input (sent to selected target)"))
        right.addWidget(self.command_input)
        cmd_row = QHBoxLayout()
        cmd_row.addWidget(self.send_btn)
        cmd_row.addWidget(self.clear_log_btn)
        right.addLayout(cmd_row)
        right.addSpacing(16)
        right.addWidget(QLabel("Operator log"))
        right.addWidget(self.info_box)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addLayout(left, 2)
        layout.addLayout(right, 3)
        self.setCentralWidget(container)

        self.append_log("helper started")
        self.record_action("app_start", result="ok")
        self.refresh_list()
        self.list_widget.setCurrentRow(0)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_state_hints)
        self.status_timer.start(3000)
        self.run_auto_start_sessions()

    def load_sessions(self) -> list[SessionProfile]:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text())
            normalized = []
            for item in data:
                normalized.append(
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
                )
            return normalized
        self.save_sessions(DEFAULT_SESSIONS)
        return DEFAULT_SESSIONS.copy()

    def save_sessions(self, sessions: list[SessionProfile] | None = None) -> None:
        payload = [asdict(x) for x in (sessions or self.sessions)]
        CONFIG_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    def append_log(self, text: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.info_box.append(f"[{ts}] {text}")

    def clear_log(self) -> None:
        self.info_box.clear()
        self.append_log("log cleared")

    def record_action(self, action: str, session: str | None = None, result: str = "ok", error: str = "", extra: dict | None = None) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "action": action,
            "session": session,
            "result": result,
            "error": error,
        }
        if extra:
            payload.update(extra)
        with ACTION_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def get_status_color(self, session: SessionProfile) -> QColor:
        if session.status == STATUS_ACTIVE:
            return QColor("darkgreen")
        if session.status == STATUS_FAILED or session.state_hint in {STATE_LAUNCH_FAILED, STATE_AUTO_START_FAILED, STATE_SEND_FAILED, STATE_DEAD}:
            return QColor("darkred")
        return QColor("darkgoldenrod")

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for session in self.sessions:
            item = QListWidgetItem(f"{session.name} | {session.status} | {session.state_hint} | launches={session.launch_count}")
            item.setBackground(self.get_status_color(session))
            self.list_widget.addItem(item)

    def on_select(self, index: int) -> None:
        if index < 0 or index >= len(self.sessions):
            return
        self.selected_index = index
        s = self.sessions[index]
        self.selected_label.setText(f"Selected target: {s.name}")
        self.status_label.setText(f"Status: {s.status}")
        self.dashboard_label.setText(f"Dashboard: {s.name} | state={s.state_hint} | launches={s.launch_count}")
        self.command_label.setText(f"Command: {s.command}")
        self.notes_label.setText(f"Notes: {s.notes or '—'}")
        self.meta_label.setText(
            f"Meta: shell={s.shell_type} | auto_start={s.auto_start} | launches={s.launch_count} | "
            f"pid={s.process_id or '—'} | state_hint={s.state_hint} | last_seen={int(s.last_seen_ts) if s.last_seen_ts else '—'} | "
            f"last_ok={s.last_launch_ok} | last_error={s.last_error or '—'}"
        )

    def get_live_process(self, session: SessionProfile) -> subprocess.Popen | None:
        proc = self.process_handles.get(session.name)
        if proc is None:
            return None
        return proc if proc.poll() is None else None

    def stream_output(self, session_name: str, stream, stream_name: str) -> None:
        for raw_line in iter(stream.readline, ""):
            line = raw_line.rstrip()
            if not line:
                continue
            session = next((item for item in self.sessions if item.name == session_name), None)
            if session is not None:
                session.last_seen_ts = time.time()
                if session.status == STATUS_ACTIVE and session.state_hint == STATE_COMMAND_SENT:
                    session.state_hint = STATE_FRESH
            self.append_log(f"[{session_name}:{stream_name}] {line}")
        try:
            stream.close()
        except Exception:
            pass

    def attach_output_readers(self, session: SessionProfile, proc: subprocess.Popen) -> None:
        if proc.stdout is not None:
            threading.Thread(target=self.stream_output, args=(session.name, proc.stdout, "stdout"), daemon=True).start()
        if proc.stderr is not None:
            threading.Thread(target=self.stream_output, args=(session.name, proc.stderr, "stderr"), daemon=True).start()

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
        self._dead_logged.discard(session.name)
        session.status = STATUS_INACTIVE
        session.process_id = None
        session.state_hint = STATE_STOPPED
        session.last_error = ""
        session.last_seen_ts = time.time()
        self.append_log(f"[ok] stopped: {session.name} ({reason})")
        self.record_action("stop", session=session.name, result="ok", extra={"reason": reason})

    def launch_session(self, session: SessionProfile, source: str) -> None:
        live = self.get_live_process(session)
        if live is not None:
            self.append_log(f"[info] replacing live process for {session.name} before relaunch")
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
            self._dead_logged.discard(session.name)
            session.status = STATUS_ACTIVE
            session.last_error = ""
            session.launch_count += 1
            session.last_launch_ok = True
            session.process_id = getattr(proc, "pid", None)
            session.last_seen_ts = time.time()
            session.state_hint = source
            self.attach_output_readers(session, proc)
            self.append_log(f"[ok] launched: {session.name} | pid={session.process_id} | source={source}")
            self.record_action("launch", session=session.name, result="ok", extra={"pid": session.process_id, "source": source})
        except Exception as exc:
            session.status = STATUS_FAILED
            session.last_error = str(exc)
            session.launch_count += 1
            session.last_launch_ok = False
            session.process_id = None
            session.state_hint = STATE_AUTO_START_FAILED if source == STATE_AUTO_STARTED else STATE_LAUNCH_FAILED
            self.append_log(f"[err] failed to launch {session.name}: {exc}")
            self.record_action("launch", session=session.name, result="failed", error=str(exc), extra={"source": source})

    def run_auto_start_sessions(self) -> None:
        for s in self.sessions:
            if s.auto_start:
                self.launch_session(s, source=STATE_AUTO_STARTED)
        self.save_sessions()
        self.refresh_list()

    def export_profiles(self) -> None:
        export_path = APP_DIR / "sessions.export.json"
        export_path.write_text(json.dumps([asdict(x) for x in self.sessions], indent=2, ensure_ascii=False))
        self.append_log(f"[ok] exported profiles to {export_path.name}")
        self.record_action("export_profiles", result="ok", extra={"path": str(export_path)})

    def import_profiles(self) -> None:
        import_path = APP_DIR / "sessions.import.json"
        if not import_path.exists():
            self.append_log(f"[warn] import file not found: {import_path.name}")
            self.record_action("import_profiles", result="failed", error="file not found", extra={"path": str(import_path)})
            return
        try:
            data = json.loads(import_path.read_text())
            imported = []
            for item in data:
                imported.append(
                    SessionProfile(
                        name=item.get("name", "Imported Session"),
                        command=item.get("command", "powershell -NoExit"),
                        status=STATUS_INACTIVE,
                        notes=item.get("notes", ""),
                        shell_type=item.get("shell_type", "powershell"),
                        auto_start=bool(item.get("auto_start", False)),
                        last_error="",
                        launch_count=0,
                        last_launch_ok=False,
                        process_id=None,
                        last_seen_ts=0.0,
                        state_hint=STATE_IMPORTED,
                    )
                )
            self.sessions = imported
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(0)
            self.append_log(f"[ok] imported profiles from {import_path.name}")
            self.record_action("import_profiles", result="ok", extra={"count": len(imported), "path": str(import_path)})
        except Exception as exc:
            self.append_log(f"[err] import failed: {exc}")
            self.record_action("import_profiles", result="failed", error=str(exc), extra={"path": str(import_path)})

    def add_session(self) -> None:
        profile = SessionProfile(name="New Session", command="powershell -NoExit")
        dlg = SessionEditDialog(profile, self)
        if dlg.exec() == QDialog.Accepted:
            new_profile = dlg.to_profile(profile)
            self.sessions.append(new_profile)
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(len(self.sessions) - 1)
            self.append_log(f"[ok] added session: {new_profile.name}")
            self.record_action("add_session", session=new_profile.name, result="ok")

    def duplicate_session(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        clone = SessionProfile(
            name=f"{s.name} Copy",
            command=s.command,
            status=STATUS_INACTIVE,
            notes=s.notes,
            shell_type=s.shell_type,
            auto_start=False,
            last_error="",
            launch_count=0,
            last_launch_ok=False,
            process_id=None,
            last_seen_ts=0.0,
            state_hint=STATE_INACTIVE,
        )
        self.sessions.append(clone)
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(len(self.sessions) - 1)
        self.append_log(f"[ok] duplicated session: {clone.name}")
        self.record_action("duplicate_session", session=clone.name, result="ok")

    def delete_session(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        if len(self.sessions) == 1:
            QMessageBox.information(self, "Cannot delete", "At least one session profile should remain.")
            return
        if self.get_live_process(s) is not None:
            self.stop_session(s, reason="delete requested")
        del self.sessions[self.selected_index]
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(max(0, self.selected_index - 1))
        self.append_log(f"[ok] deleted session: {s.name}")
        self.record_action("delete_session", session=s.name, result="ok")

    def reconnect_selected(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        self.launch_session(s, source=STATE_LAUNCHED)
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)

    def refresh_state_hints(self) -> None:
        now = time.time()
        for s in self.sessions:
            proc = self.process_handles.get(s.name)
            if proc is not None:
                return_code = proc.poll()
                if return_code is not None:
                    self.mark_session_dead(s, return_code=return_code)
                    if s.name not in self._dead_logged:
                        self._dead_logged.add(s.name)
                        self.append_log(f"[warn] process exited: {s.name} | code={return_code}")
                        self.record_action("process_exit", session=s.name, result="failed" if return_code else "ok", extra={"code": return_code})
                    continue
            if s.status == STATUS_ACTIVE and s.last_seen_ts:
                age = now - s.last_seen_ts
                if age < 10:
                    s.state_hint = STATE_FRESH
                elif age < 60:
                    s.state_hint = STATE_IDLE
                else:
                    s.state_hint = STATE_STALE
            elif s.status == STATUS_INACTIVE and s.state_hint not in {STATE_STOPPED, STATE_IMPORTED, STATE_DEAD}:
                s.state_hint = STATE_INACTIVE
        current = self.list_widget.currentRow()
        self.save_sessions()
        self.refresh_list()
        if current >= 0:
            self.list_widget.setCurrentRow(current)

    def stop_selected(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        if self.get_live_process(s) is None:
            s.status = STATUS_INACTIVE
            s.process_id = None
            s.state_hint = STATE_STOPPED
            self.append_log(f"[info] no live process to stop for: {s.name}")
            self.record_action("stop", session=s.name, result="ok", extra={"reason": "no live process"})
        else:
            self.stop_session(s)
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)

    def mark_inactive(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        if self.get_live_process(s) is not None:
            self.stop_session(s, reason="marked inactive")
        else:
            s.status = STATUS_INACTIVE
            s.process_id = None
            s.state_hint = STATE_INACTIVE
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)
        self.append_log(f"[ok] marked inactive: {s.name}")
        self.record_action("mark_inactive", session=s.name, result="ok")

    def edit_selected(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        dlg = SessionEditDialog(s, self)
        if dlg.exec() == QDialog.Accepted:
            self.sessions[self.selected_index] = dlg.to_profile(s)
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(self.selected_index)
            self.append_log(f"[ok] updated session: {self.sessions[self.selected_index].name}")
            self.record_action("edit_session", session=self.sessions[self.selected_index].name, result="ok")

    def send_command(self) -> None:
        s = self.sessions[self.selected_index]
        command = self.command_input.toPlainText().strip()
        if not command:
            QMessageBox.information(self, "No command", "Type a command first.")
            return

        proc = self.get_live_process(s)
        if not proc or proc.stdin is None:
            self.append_log(f"[warn] session '{s.name}' is not managed yet; press Connect / Reconnect in helper first, then send command.")
            self.record_action("send", session=s.name, result="failed", error="session not managed")
            return

        try:
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
            s.last_seen_ts = time.time()
            s.state_hint = STATE_COMMAND_SENT
            s.last_error = ""
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(self.selected_index)
            self.append_log(f"[ok] sent to '{s.name}': {command}")
            self.record_action("send", session=s.name, result="ok", extra={"command": command})
            self.command_input.clear()
        except Exception as exc:
            s.last_error = str(exc)
            s.status = STATUS_FAILED
            s.state_hint = STATE_SEND_FAILED
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(self.selected_index)
            self.append_log(f"[err] failed send to '{s.name}': {exc}")
            self.record_action("send", session=s.name, result="failed", error=str(exc), extra={"command": command})


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
