from __future__ import annotations

import sys
import time
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

from models import (
    STATE_AUTO_START_FAILED,
    STATE_ACCEPTED,
    STATE_AUTO_STARTED,
    STATE_DEAD,
    STATE_FRESH,
    STATE_IDLE,
    STATE_IMPORTED,
    STATE_INACTIVE,
    STATE_LAUNCH_FAILED,
    STATE_LAUNCHED,
    STATE_SEND_FAILED,
    STATE_STALE,
    STATE_STOPPED,
    STATUS_ACTIVE,
    STATUS_FAILED,
    STATUS_INACTIVE,
    SessionProfile,
)
from runtime import SessionRuntimeManager
from store import SessionStore

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "sessions.json"
LOG_DIR = APP_DIR / "logs"


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
        self.store = SessionStore(CONFIG_PATH)
        self.sessions = self.store.load()
        self.selected_index = 0

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

        self.history_box = QTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setPlaceholderText("Recent command activity for selected session...")
        self.history_box.setFixedHeight(140)

        self.runtime = SessionRuntimeManager(LOG_DIR, self.append_log)

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
        right.addWidget(QLabel("Recent command activity"))
        right.addWidget(self.history_box)
        right.addSpacing(12)
        right.addWidget(QLabel("Operator log"))
        right.addWidget(self.info_box)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addLayout(left, 2)
        layout.addLayout(right, 3)
        self.setCentralWidget(container)

        self.append_log("helper started")
        self.runtime.record_action("app_start", result="ok")
        self.refresh_list()
        self.list_widget.setCurrentRow(0)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_state_hints)
        self.status_timer.start(3000)
        self.run_auto_start_sessions()

    def persist(self) -> None:
        self.store.save(self.sessions)

    def append_log(self, text: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.info_box.append(f"[{ts}] {text}")

    def clear_log(self) -> None:
        self.info_box.clear()
        self.append_log("log cleared")

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

    def render_session_details(self, s: SessionProfile) -> None:
        self.selected_label.setText(f"Selected target: {s.name}")
        self.status_label.setText(f"Status: {s.status}")
        self.dashboard_label.setText(f"Dashboard: {s.name} | state={s.state_hint} | launches={s.launch_count}")
        self.command_label.setText(f"Command: {s.command}")
        self.notes_label.setText(f"Notes: {s.notes or '—'}")
        recent_events = self.runtime.get_recent_command_events(s.name, limit=6)
        recent_summary = " ; ".join(
            f"{item.get('stage')}:{item.get('command_id', '')[:8]}" for item in recent_events[:3]
        ) or "—"
        self.meta_label.setText(
            f"Meta: shell={s.shell_type} | auto_start={s.auto_start} | launches={s.launch_count} | "
            f"pid={s.process_id or '—'} | state_hint={s.state_hint} | last_seen={int(s.last_seen_ts) if s.last_seen_ts else '—'} | "
            f"last_ok={s.last_launch_ok} | last_error={s.last_error or '—'} | recent_cmds={recent_summary}"
        )
        if recent_events:
            lines = []
            for item in recent_events:
                lines.append(
                    f"{item.get('ts', '')} | {item.get('stage', '')} | {item.get('command_id', '')[:8]} | {item.get('command', '')}"
                )
            self.history_box.setPlainText("\n".join(lines))
        else:
            self.history_box.setPlainText("No command activity yet.")

    def on_select(self, index: int) -> None:
        if index < 0 or index >= len(self.sessions):
            return
        self.selected_index = index
        s = self.sessions[index]
        self.render_session_details(s)

    def run_auto_start_sessions(self) -> None:
        for s in self.sessions:
            if s.auto_start:
                self.runtime.launch_session(self.sessions, s, source=STATE_AUTO_STARTED)
        self.persist()
        self.refresh_list()

    def export_profiles(self) -> None:
        export_path = APP_DIR / "sessions.export.json"
        export_path.write_text(CONFIG_PATH.read_text() if CONFIG_PATH.exists() else "[]")
        self.append_log(f"[ok] exported profiles to {export_path.name}")
        self.runtime.record_action("export_profiles", result="ok", extra={"path": str(export_path)})

    def import_profiles(self) -> None:
        import_path = APP_DIR / "sessions.import.json"
        if not import_path.exists():
            self.append_log(f"[warn] import file not found: {import_path.name}")
            self.runtime.record_action("import_profiles", result="failed", error="file not found", extra={"path": str(import_path)})
            return
        import_store = SessionStore(import_path)
        self.sessions = import_store.load()
        for s in self.sessions:
            s.status = STATUS_INACTIVE
            s.state_hint = STATE_IMPORTED
            s.process_id = None
            s.last_error = ""
        self.persist()
        self.refresh_list()
        self.list_widget.setCurrentRow(0)
        self.append_log(f"[ok] imported profiles from {import_path.name}")
        self.runtime.record_action("import_profiles", result="ok", extra={"count": len(self.sessions), "path": str(import_path)})

    def add_session(self) -> None:
        profile = SessionProfile(name="New Session", command="powershell -NoExit")
        dlg = SessionEditDialog(profile, self)
        if dlg.exec() == QDialog.Accepted:
            new_profile = dlg.to_profile(profile)
            self.sessions.append(new_profile)
            self.persist()
            self.refresh_list()
            self.list_widget.setCurrentRow(len(self.sessions) - 1)
            self.append_log(f"[ok] added session: {new_profile.name}")
            self.runtime.record_action("add_session", session=new_profile.name, result="ok")

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
        )
        self.sessions.append(clone)
        self.persist()
        self.refresh_list()
        self.list_widget.setCurrentRow(len(self.sessions) - 1)
        self.append_log(f"[ok] duplicated session: {clone.name}")
        self.runtime.record_action("duplicate_session", session=clone.name, result="ok")

    def delete_session(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        if len(self.sessions) == 1:
            QMessageBox.information(self, "Cannot delete", "At least one session profile should remain.")
            return
        if self.runtime.get_live_process(s) is not None:
            self.runtime.stop_session(s, reason="delete requested")
        del self.sessions[self.selected_index]
        self.persist()
        self.refresh_list()
        self.list_widget.setCurrentRow(max(0, self.selected_index - 1))
        self.append_log(f"[ok] deleted session: {s.name}")
        self.runtime.record_action("delete_session", session=s.name, result="ok")

    def reconnect_selected(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        self.runtime.launch_session(self.sessions, s, source=STATE_LAUNCHED)
        self.persist()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)

    def refresh_state_hints(self) -> None:
        now = time.time()
        for s in self.sessions:
            proc = self.runtime.process_handles.get(s.name)
            if proc is not None:
                return_code = proc.poll()
                if return_code is not None:
                    self.runtime.mark_session_dead(s, return_code=return_code)
                    if s.name not in self.runtime.dead_logged:
                        self.runtime.dead_logged.add(s.name)
                        self.append_log(f"[warn] process exited: {s.name} | code={return_code}")
                        self.runtime.record_action("process_exit", session=s.name, result="failed" if return_code else "ok", extra={"code": return_code})
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
        self.persist()
        self.refresh_list()
        if current >= 0:
            self.list_widget.setCurrentRow(current)
            self.render_session_details(self.sessions[current])

    def stop_selected(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        if self.runtime.get_live_process(s) is None:
            s.status = STATUS_INACTIVE
            s.process_id = None
            s.state_hint = STATE_STOPPED
            self.append_log(f"[info] no live process to stop for: {s.name}")
            self.runtime.record_action("stop", session=s.name, result="ok", extra={"reason": "no live process"})
        else:
            self.runtime.stop_session(s)
        self.persist()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)

    def mark_inactive(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        if self.runtime.get_live_process(s) is not None:
            self.runtime.stop_session(s, reason="marked inactive")
        else:
            s.status = STATUS_INACTIVE
            s.process_id = None
            s.state_hint = STATE_INACTIVE
        self.persist()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)
        self.append_log(f"[ok] marked inactive: {s.name}")
        self.runtime.record_action("mark_inactive", session=s.name, result="ok")

    def edit_selected(self) -> None:
        if not self.sessions:
            return
        s = self.sessions[self.selected_index]
        dlg = SessionEditDialog(s, self)
        if dlg.exec() == QDialog.Accepted:
            self.sessions[self.selected_index] = dlg.to_profile(s)
            self.persist()
            self.refresh_list()
            self.list_widget.setCurrentRow(self.selected_index)
            self.append_log(f"[ok] updated session: {self.sessions[self.selected_index].name}")
            self.runtime.record_action("edit_session", session=self.sessions[self.selected_index].name, result="ok")

    def send_command(self) -> None:
        s = self.sessions[self.selected_index]
        command = self.command_input.toPlainText().strip()
        if not command:
            QMessageBox.information(self, "No command", "Type a command first.")
            return
        ok, error, command_id = self.runtime.send_command(s, command)
        self.persist()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)
        if ok:
            self.append_log(f"[ok] sent to '{s.name}': {command} | command_id={command_id}")
            self.command_input.clear()
        else:
            if error == "session not managed":
                self.append_log(f"[warn] session '{s.name}' is not managed yet; press Connect / Reconnect in helper first, then send command. | command_id={command_id}")
            else:
                self.append_log(f"[err] failed send to '{s.name}': {error} | command_id={command_id}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
