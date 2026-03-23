@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "LOGFILE=%~dp0build_exe.log"
echo ==== BossSessionHelper build started ==== > "%LOGFILE%"
echo Working dir: %CD% >> "%LOGFILE%"

echo [1/4] Upgrade pip
python -m pip install --upgrade pip >> "%LOGFILE%" 2>&1
if errorlevel 1 goto :fail

echo [2/4] Install requirements and pyinstaller
python -m pip install -r requirements.txt pyinstaller >> "%LOGFILE%" 2>&1
if errorlevel 1 goto :fail

echo [3/4] Build exe
python -m PyInstaller --noconfirm --onefile --windowed --name BossSessionHelper --distpath "%~dp0" --workpath "%~dp0build" --specpath "%~dp0" app.py >> "%LOGFILE%" 2>&1
if errorlevel 1 goto :fail

echo [4/4] Done
if exist "%~dp0BossSessionHelper.exe" (
  echo SUCCESS: "%~dp0BossSessionHelper.exe"
  echo SUCCESS: "%~dp0BossSessionHelper.exe" >> "%LOGFILE%"
  echo.
  echo Build complete. EXE created in this folder.
  pause
  goto :eof
)

echo ERROR: Build command finished but BossSessionHelper.exe was not found. >> "%LOGFILE%"
echo.
echo Build finished but EXE was not found.
echo See log: "%LOGFILE%"
pause
goto :eof

:fail
echo.
echo Build failed. See log: "%LOGFILE%"
echo Last 40 log lines:
powershell -NoProfile -Command "Get-Content -Path '%LOGFILE%' -Tail 40"
pause
exit /b 1
