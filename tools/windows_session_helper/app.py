from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
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


@dataclass
class SessionProfile:
    name: str
    command: str
    status: str = "inactive"
    notes: str = ""
    shell_type: str = "powershell"
    auto_start: bool = False
    last_error: str = ""
    launch_count: int = 0
    last_launch_ok: bool = False
    process_id: int | None = None
    last_seen_ts: float = 0.0
    state_hint: str = "unknown"


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
        self.auto_start_edit = QLineEdit('true' if profile.auto_start else 'false')

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
            auto_start=self.auto_start_edit.text().strip().lower() == 'true',
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
        self.setWindowTitle("Boss Session Helper")
        self.resize(1000, 640)
        self.sessions = self.load_sessions()
        self.selected_index = 0
        self.process_handles: dict[str, subprocess.Popen] = {}

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select)

        self.status_label = QLabel("Status: —")
        self.command_label = QLabel("Command: —")
        self.command_label.setWordWrap(True)
        self.notes_label = QLabel("Notes: —")
        self.notes_label.setWordWrap(True)
        self.meta_label = QLabel("Meta: —")
        self.meta_label.setWordWrap(True)

        self.reconnect_btn = QPushButton("Connect / Reconnect")
        self.reconnect_btn.clicked.connect(self.reconnect_selected)
        self.mark_inactive_btn = QPushButton("Mark Inactive")
        self.mark_inactive_btn.clicked.connect(self.mark_inactive)
        self.edit_btn = QPushButton("Edit Session")
        self.edit_btn.clicked.connect(self.edit_selected)

        self.selected_label = QLabel("Selected session: —")
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("Type command to send to selected session...")
        self.command_input.setFixedHeight(100)
        self.send_btn = QPushButton("Send to Selected")
        self.send_btn.clicked.connect(self.send_command)

        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setPlaceholderText("Helper log / operator notes...")

        left = QVBoxLayout()
        left.addWidget(QLabel("Sessions"))
        left.addWidget(self.list_widget)

        right = QVBoxLayout()
        right.addWidget(self.selected_label)
        right.addWidget(self.status_label)
        right.addWidget(self.command_label)
        right.addWidget(self.notes_label)
        right.addWidget(self.meta_label)

        row = QHBoxLayout()
        row.addWidget(self.reconnect_btn)
        row.addWidget(self.mark_inactive_btn)
        row.addWidget(self.edit_btn)
        right.addLayout(row)
        right.addSpacing(16)
        right.addWidget(QLabel("Shared command input"))
        right.addWidget(self.command_input)
        right.addWidget(self.send_btn)
        right.addSpacing(16)
        right.addWidget(QLabel("Operator log"))
        right.addWidget(self.info_box)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addLayout(left, 2)
        layout.addLayout(right, 3)
        self.setCentralWidget(container)

        self.refresh_list()
        self.list_widget.setCurrentRow(0)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_state_hints)
        self.status_timer.start(3000)

    def load_sessions(self) -> list[SessionProfile]:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text())
            normalized = []
            for item in data:
                normalized.append(SessionProfile(
                    name=item.get('name', 'Unnamed'),
                    command=item.get('command', 'powershell -NoExit'),
                    status=item.get('status', 'inactive'),
                    notes=item.get('notes', ''),
                    shell_type=item.get('shell_type', 'powershell'),
                    auto_start=bool(item.get('auto_start', False)),
                    last_error=item.get('last_error', ''),
                    launch_count=int(item.get('launch_count', 0)),
                    last_launch_ok=bool(item.get('last_launch_ok', False)),
                    process_id=item.get('process_id'),
                    last_seen_ts=float(item.get('last_seen_ts', 0.0)),
                    state_hint=item.get('state_hint', 'unknown'),
                ))
            return normalized
        self.save_sessions(DEFAULT_SESSIONS)
        return DEFAULT_SESSIONS.copy()

    def save_sessions(self, sessions: list[SessionProfile] | None = None) -> None:
        payload = [asdict(x) for x in (sessions or self.sessions)]
        CONFIG_PATH.write_text(json.dumps(payload, indent=2))

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for session in self.sessions:
            item = QListWidgetItem(f"{session.name} [{session.status} | {session.state_hint}]")
            self.list_widget.addItem(item)

    def on_select(self, index: int) -> None:
        if index < 0 or index >= len(self.sessions):
            return
        self.selected_index = index
        s = self.sessions[index]
        self.selected_label.setText(f"Selected session: {s.name}")
        self.status_label.setText(f"Status: {s.status}")
        self.command_label.setText(f"Command: {s.command}")
        self.notes_label.setText(f"Notes: {s.notes or '—'}")
        self.meta_label.setText(f"Meta: shell={s.shell_type} | auto_start={s.auto_start} | launches={s.launch_count} | pid={s.process_id or '—'} | state_hint={s.state_hint} | last_seen={int(s.last_seen_ts) if s.last_seen_ts else '—'} | last_ok={s.last_launch_ok} | last_error={s.last_error or '—'}")

    def reconnect_selected(self) -> None:
        s = self.sessions[self.selected_index]
        try:
            proc = subprocess.Popen(s.command, shell=True, stdin=subprocess.PIPE, text=True)
            self.process_handles[s.name] = proc
            s.status = "active"
            s.last_error = ""
            s.launch_count += 1
            s.last_launch_ok = True
            s.process_id = getattr(proc, 'pid', None)
            s.last_seen_ts = time.time()
            s.state_hint = 'launched'
            self.info_box.append(f"[ok] launched/reconnected: {s.name} | pid={s.process_id}")
        except Exception as exc:
            s.status = "inactive"
            s.last_error = str(exc)
            s.launch_count += 1
            s.last_launch_ok = False
            s.process_id = None
            s.state_hint = 'launch_failed'
            self.info_box.append(f"[err] failed to launch {s.name}: {exc}")
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)

    def refresh_state_hints(self) -> None:
        now = time.time()
        for s in self.sessions:
            if s.status == 'active' and s.last_seen_ts:
                age = now - s.last_seen_ts
                if age < 10:
                    s.state_hint = 'fresh'
                elif age < 60:
                    s.state_hint = 'idle'
                else:
                    s.state_hint = 'stale'
            elif s.status == 'inactive' and s.state_hint == 'unknown':
                s.state_hint = 'inactive'
        current = self.list_widget.currentRow()
        self.save_sessions()
        self.refresh_list()
        if current >= 0:
            self.list_widget.setCurrentRow(current)

    def mark_inactive(self) -> None:
        s = self.sessions[self.selected_index]
        s.status = "inactive"
        s.process_id = None
        s.state_hint = 'manually_inactive'
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)
        self.info_box.append(f"[ok] marked inactive: {s.name}")

    def edit_selected(self) -> None:
        s = self.sessions[self.selected_index]
        dlg = SessionEditDialog(s, self)
        if dlg.exec() == QDialog.Accepted:
            self.sessions[self.selected_index] = dlg.to_profile(s)
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(self.selected_index)
            self.info_box.append(f"[ok] updated session: {self.sessions[self.selected_index].name}")

    def send_command(self) -> None:
        s = self.sessions[self.selected_index]
        command = self.command_input.toPlainText().strip()
        if not command:
            QMessageBox.information(self, "No command", "Type a command first.")
            return

        proc = self.process_handles.get(s.name)
        if not proc or proc.stdin is None:
            self.info_box.append(f"[warn] session '{s.name}' is not managed yet; launch/reconnect it from helper first.")
            return

        try:
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
            s.last_seen_ts = time.time()
            s.state_hint = 'command_sent'
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(self.selected_index)
            self.info_box.append(f"[ok] sent to '{s.name}': {command}")
        except Exception as exc:
            s.last_error = str(exc)
            s.state_hint = 'send_failed'
            self.save_sessions()
            self.refresh_list()
            self.list_widget.setCurrentRow(self.selected_index)
            self.info_box.append(f"[err] failed send to '{s.name}': {exc}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
