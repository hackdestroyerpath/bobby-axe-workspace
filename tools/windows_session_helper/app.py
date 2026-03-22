from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
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


DEFAULT_SESSIONS = [
    SessionProfile(name="Jack VPS", command="powershell -NoExit -Command ssh openclaw@YOUR_VPS_IP"),
    SessionProfile(name="Extra Server", command="powershell -NoExit -Command ssh user@YOUR_OTHER_HOST"),
    SessionProfile(name="Local PowerShell", command="powershell -NoExit"),
]


class SessionEditDialog(QDialog):
    def __init__(self, profile: SessionProfile, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Session")
        self.name_edit = QLineEdit(profile.name)
        self.command_edit = QLineEdit(profile.command)
        self.notes_edit = QLineEdit(profile.notes)

        form = QFormLayout()
        form.addRow("Name", self.name_edit)
        form.addRow("Command", self.command_edit)
        form.addRow("Notes", self.notes_edit)

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
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Boss Session Helper")
        self.resize(1000, 640)
        self.sessions = self.load_sessions()
        self.selected_index = 0

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select)

        self.status_label = QLabel("Status: —")
        self.command_label = QLabel("Command: —")
        self.command_label.setWordWrap(True)
        self.notes_label = QLabel("Notes: —")
        self.notes_label.setWordWrap(True)

        self.reconnect_btn = QPushButton("Connect / Reconnect")
        self.reconnect_btn.clicked.connect(self.reconnect_selected)
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

        row = QHBoxLayout()
        row.addWidget(self.reconnect_btn)
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

    def load_sessions(self) -> list[SessionProfile]:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text())
            return [SessionProfile(**item) for item in data]
        self.save_sessions(DEFAULT_SESSIONS)
        return DEFAULT_SESSIONS.copy()

    def save_sessions(self, sessions: list[SessionProfile] | None = None) -> None:
        payload = [asdict(x) for x in (sessions or self.sessions)]
        CONFIG_PATH.write_text(json.dumps(payload, indent=2))

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for session in self.sessions:
            item = QListWidgetItem(f"{session.name} [{session.status}]")
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

    def reconnect_selected(self) -> None:
        s = self.sessions[self.selected_index]
        try:
            subprocess.Popen(s.command, shell=True)
            s.status = "active"
            self.info_box.append(f"[ok] launched/reconnected: {s.name}")
        except Exception as exc:
            s.status = "inactive"
            self.info_box.append(f"[err] failed to launch {s.name}: {exc}")
        self.save_sessions()
        self.refresh_list()
        self.list_widget.setCurrentRow(self.selected_index)

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
        self.info_box.append(
            f"[todo] send to '{s.name}': {command}\n"
            f"This prototype currently manages sessions and launch commands; direct command injection into existing Windows terminals is the next implementation layer."
        )


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
