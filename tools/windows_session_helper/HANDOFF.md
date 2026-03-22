# Boss Session Helper — First Usable Handoff

## What to take
Folder:
- `tools/windows_session_helper/`

Main files:
- `app.py`
- `requirements.txt`
- `WINDOWS_SETUP.md`
- `build_exe.bat`

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
7. inspect operator log and status hints

---

## Current product state
This is the first usable prototype.

It already supports:
- session profiles
- add/edit/delete/duplicate
- reconnect/launch
- managed command dispatch to helper-launched sessions
- status hints
- import/export profiles
- packaging path for exe

---

## Current known limitation
The current command dispatch is designed for helper-managed sessions.

Meaning:
- for command sending to work reliably, launch/reconnect the session from inside the helper first.

This is the intended first practical model.
