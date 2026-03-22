# JetBrains / Windows Guide for Boss Session Helper

## Что открыть
Открой папку:
- `FUBOS/windows_session_helper/`

в своей JetBrains IDE (PyCharm или другой IDE с Python support).

---

## Вариант 1 — запуск как Python app
### 1. Убедись, что Python установлен
Лучше Python 3.11+

### 2. Открой встроенный терминал IDE
В папке `FUBOS/windows_session_helper/`

### 3. Поставь зависимости
```powershell
pip install -r requirements.txt
```

### 4. Запусти приложение
```powershell
python app.py
```

---

## Вариант 2 — собрать exe
В той же папке:
```powershell
build_exe.bat
```

После сборки ожидается:
- `dist/BossSessionHelper.exe`

---

## Что тестировать первым
1. Запусти helper
2. Посмотри default sessions
3. Нажми `Edit Session` у `Jack VPS`
4. Подставь свой реальный SSH/PowerShell launch command
5. Нажми `Connect / Reconnect`
6. Введи команду в поле команды
7. Нажми `Send to Selected`

---

## Важно
Текущая версия лучше всего работает с managed sessions:
- сначала helper сам запускает сессию
- потом helper шлёт команду в эту сессию

То есть сначала `Connect / Reconnect`, потом `Send to Selected`.

---

## Что делать, если захочешь править под себя
В helper уже можно:
- `Add Session`
- `Edit Session`
- `Duplicate`
- `Delete`
- `Import Profiles`
- `Export Profiles`

То есть базовую настройку можно делать прямо из GUI.
