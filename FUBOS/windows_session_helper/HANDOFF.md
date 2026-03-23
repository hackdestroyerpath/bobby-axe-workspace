# Boss Session Helper — First Usable Handoff

## What to take
Folder:
- `FUBOS/windows_session_helper/`

Main files:
- `app.py`
- `requirements.txt`
- `WINDOWS_SETUP.md`
- `build_exe.bat`
- `logs/actions.jsonl` (runtime-generated)

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
8. press `Stop Session`
9. confirm `logs/actions.jsonl` is receiving events

---

## Current product state
This is the first usable prototype with basic lifecycle stabilization.

It currently supports:
- session profiles
- add/edit/delete/duplicate
- reconnect/launch
- stop session
- managed command dispatch to helper-launched sessions
- process death detection
- stdout/stderr capture into operator log
- status hints
- import/export profiles
- packaging path for exe
- structured action log

---

## Current known limitation
The current command dispatch is designed for helper-managed sessions.

Meaning:
- for command sending to work reliably, launch/reconnect the session from inside the helper first.
- status hints are operational hints, not a full transport-health model.
- stdout/stderr capture is best-effort and meant for operator visibility, not terminal emulation.
