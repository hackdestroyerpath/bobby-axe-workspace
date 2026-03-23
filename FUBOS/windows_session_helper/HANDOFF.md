# Boss Session Helper — Usable Handoff

## What to take
Folder:
- `FUBOS/windows_session_helper/`

Main files:
- `app.py`
- `models.py`
- `store.py`
- `runtime.py`
- `requirements.txt`
- `WINDOWS_SETUP.md`
- `build_exe.bat`
- `logs/actions.jsonl` (runtime-generated)
- `logs/commands.jsonl` (runtime-generated)

---

## Fast start on Windows
### Option A — run as Python app
```powershell
pip install -r requirements.txt
python app.py
```

### Option B — build exe
```powershell
build_exe.bat
```

Expected result:
- `dist/BossSessionHelper.exe`

---

## What to test first
1. launch app
2. inspect default sessions
3. edit one session command
4. add one new session
5. press `Connect / Reconnect`
6. try `Send to Selected`
7. inspect operator log, stdout/stderr capture, and status hints
8. inspect `Recent command activity`
9. press `Stop Session`
10. confirm `logs/actions.jsonl` and `logs/commands.jsonl` are receiving events
11. export profiles to `sessions.export.json`
12. import profiles from `sessions.import.json`

---

## Current product state
This is now a stabilized prototype helper with separated UI/store/runtime layers.

It currently supports:
- session profiles
- add/edit/delete/duplicate
- reconnect/launch
- stop session
- managed command dispatch to helper-launched sessions
- process death detection
- stdout/stderr capture into operator log
- recent command activity in GUI
- action log + command journal
- best-effort ack tracking
- import/export profiles
- packaging path for exe

---

## Known limitations
- command dispatch is designed for helper-managed sessions only
- ack tracking is best-effort and relies on shell-visible `echo` markers
- status hints are still operational hints, not a full transport-health model
- operator log is visibility-focused, not a full terminal emulator
