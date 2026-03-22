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

## 4. Build exe (optional)
```powershell
build_exe.bat
```

The executable will appear under:
- `dist/BossSessionHelper.exe`

## Notes
- first launch creates `sessions.json`
- profiles can be exported/imported
- for command sending, sessions should be launched from inside the helper so they are managed by the app
