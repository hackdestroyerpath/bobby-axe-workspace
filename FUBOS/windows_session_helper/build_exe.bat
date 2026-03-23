@echo off
setlocal
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name BossSessionHelper --distpath "%~dp0" --workpath "%~dp0build" --specpath "%~dp0" app.py
endlocal
