# Windows Session Helper

Prototype Windows GUI helper for managing several session windows from one control app.

## Run

```bash
python app.py
```

## Requirements
- Python 3.11+
- PySide6

```bash
pip install -r requirements.txt
```

## File layout
- `app.py` — Qt UI and wiring
- `models.py` — session model + status/state constants
- `store.py` — profile persistence for `sessions.json` / import/export files
- `runtime.py` — process lifecycle, output capture, action log, command journal, ack flow
- `sessions.json` — active profile store
- `logs/actions.jsonl` — structured helper actions
- `logs/commands.jsonl` — command lifecycle journal

## Current stable behavior
- session profiles persist in `sessions.json`
- helper can launch, stop, reconnect, duplicate, import, and export profiles
- commands are sent only to helper-managed sessions
- process death is detected and reflected in UI state
- stdout/stderr are captured into the operator log when available
- structured action log is written to `logs/actions.jsonl`
- command journal is written to `logs/commands.jsonl`
- best-effort command ack markers are appended to sent commands and tracked in output
- recent command activity is shown for the selected session in GUI

## Import / export behavior
- Export writes the current session set into `sessions.export.json`
- Import reads `sessions.import.json`
- Import stops helper-managed live sessions before replacing the in-memory profile set
- Imported sessions are normalized to inactive/imported state before first use

## Status model

### `status`
- `inactive`
- `active`
- `failed`

### `state_hint`
- `launched`
- `auto_started`
- `fresh`
- `idle`
- `stale`
- `dead`
- `launch_failed`
- `auto_start_failed`
- `send_failed`
- `stopped`
- `imported`
- `inactive`
- `command_sent`
- `accepted`
- `acked`

## Important limitations
Command dispatch is still designed for helper-launched sessions.
If you need `Send to Selected` to work reliably, first start the target session from inside the helper.

Ack behavior is best-effort:
- helper appends an `echo <ack-marker>` after the sent command
- this works best for PowerShell/cmd-like shells
- complex interactive programs or non-echoing runtimes may not produce `acked`, even if the write succeeded
