from __future__ import annotations

from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
FILES = [
    "STATUS.md",
    "PROJECTS.md",
    "TASKS.md",
    "PROCESSES.md",
    "ACTION_LOG.md",
    "NAGANYAY.md",
]


def read_text(name: str) -> str:
    path = ROOT / name
    return path.read_text() if path.exists() else ""


def latest_action_lines(text: str, limit: int = 6) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return lines[-limit:]


def extract_status_section(text: str, title: str) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    capture = False
    for line in lines:
        if line.strip() == title:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip():
            out.append(line.strip())
    return out


def has_meaningful_progress(action_log: str) -> bool:
    return "- Time:" in action_log and "- Done:" in action_log


def build_heartbeat() -> str:
    status = read_text("STATUS.md")
    action_log = read_text("ACTION_LOG.md")
    naganyay = read_text("NAGANYAY.md")

    if not has_meaningful_progress(action_log):
        return "HEARTBEAT_OK"

    done_lines = [line for line in extract_status_section(status, "## Что сделано") if line.startswith("-")]
    left_lines = [line for line in extract_status_section(status, "## Что осталось сделать") if line.startswith("-")]
    class_lines = [line for line in extract_status_section(status, "## Классификация") if line.startswith("-")]
    nag_lines = [line for line in extract_status_section(status, "## Нагоняй от MAXIMUS") if line.startswith("-")]

    done_lines = done_lines[-3:] if done_lines else ["- Нет нового зафиксированного прогресса."]
    left_lines = left_lines[:3] if left_lines else ["- Существенных хвостов не зафиксировано."]
    class_lines = class_lines[:3] if class_lines else ["- [PROCESS] PROC-BBY-001"]
    nag_text = nag_lines[0] if nag_lines else "- нет"
    if nag_text.lower() == "- нет активного нового нагоняя.":
        nag_text = "- нет"

    sections = [
        "1) Что было сделано за последние 5 минут",
        *done_lines,
        "",
        "2) Что осталось сделать",
        *left_lines,
        "",
        "3) К чему относится",
        *class_lines,
        "",
        "4) Был ли нагоняй от MAXIMUS",
        nag_text,
    ]
    return "\n".join(sections)


if __name__ == "__main__":
    print(build_heartbeat())
