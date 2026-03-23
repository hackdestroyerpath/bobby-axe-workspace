# Windows Setup

## 1. Install Python
Use Python 3.11+ on Windows.

## 2. Install dependencies
```powershell
pip install -r requirements.txt
```

## 3. Run helper
```powershell
python app.py
```

## 4. How to use
1. Open the app.
2. Select or edit a session profile.
3. Press **Connect / Reconnect** to launch the session from inside the helper.
4. Type a command in **Shared command input**.
5. Press **Send to Selected**.
6. Watch:
   - **Recent command activity** for command stages
   - **Operator log** for stdout/stderr and lifecycle events
7. Use **Stop Session** to stop a managed session.
8. Use **Export Profiles** / **Import Profiles** for profile transfer.

## 5. Build exe
```powershell
build_exe.bat
```

The executable will appear under:
- `dist/BossSessionHelper.exe`

## Notes
- first launch creates `sessions.json`
- logs are written to `logs/actions.jsonl` and `logs/commands.jsonl`
- import stops helper-managed live sessions before replacing the profile set
- command guardrails show a warning for risky shell patterns before send
- best-effort ack works best for PowerShell/cmd-like shells
