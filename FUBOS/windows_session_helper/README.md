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

## Current stable behavior
- session profiles persist in `sessions.json`
- helper can launch, stop, reconnect, duplicate, import, and export profiles
- commands are sent only to helper-managed sessions
- process death is detected and reflected in UI state
- stdout/stderr are captured into the operator log when available
- structured action log is written to `logs/actions.jsonl`
- command journal is written to `logs/commands.jsonl`
- best-effort command ack markers are appended to sent commands and tracked in output

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

## Important limitation
Command dispatch is still designed for helper-launched sessions.
If you need `Send to Selected` to work reliably, first start the target session from inside the helper.
