# FUBOS — инструкция по запуску и передаче

## Что это
`FUBOS/windows_session_helper` — Windows GUI helper для управления несколькими terminal/session окнами из одного приложения.

## Что скачать
Скачай весь раздел:
- `FUBOS/`

Если передаёшь другому человеку, лучше передавать именно архив всей папки `FUBOS`, а не отдельные файлы.

## Состав
Главное внутри:
- `FUBOS/README.md`
- `FUBOS/JETBRAINS_WINDOWS_GUIDE.md`
- `FUBOS/windows_session_helper/app.py`
- `FUBOS/windows_session_helper/requirements.txt`
- `FUBOS/windows_session_helper/WINDOWS_SETUP.md`
- `FUBOS/windows_session_helper/build_exe.bat`
- `FUBOS/windows_session_helper/HANDOFF.md`
- `FUBOS/windows_session_helper/DISPATCH.md`

## Вариант 1 — запуск как Python приложения
Требования:
- Windows
- Python 3.11+
- установлен `pip`

Шаги:
1. Распаковать архив.
2. Открыть папку:
   - `FUBOS/windows_session_helper/`
3. Открыть терминал в этой папке.
4. Установить зависимости:
```powershell
pip install -r requirements.txt
```
5. Запустить приложение:
```powershell
python app.py
```

## Вариант 2 — запуск через JetBrains
1. Открыть в PyCharm или другой JetBrains IDE папку:
   - `FUBOS/windows_session_helper/`
2. Убедиться, что выбран Python 3.11+ interpreter.
3. Встроенным терминалом выполнить:
```powershell
pip install -r requirements.txt
python app.py
```

## Вариант 3 — собрать `.exe`
Из папки `FUBOS/windows_session_helper/` выполнить:
```powershell
build_exe.bat
```
Ожидаемый результат:
- `dist/BossSessionHelper.exe`

## Первый запуск
На первом запуске приложение создаёт:
- `sessions.json`

Это файл профилей сессий. Его можно потом:
- редактировать через GUI,
- экспортировать,
- импортировать.

## Как пользоваться правильно
Рабочая модель сейчас такая:
1. Запустить helper.
2. Проверить default sessions.
3. Нажать `Edit Session` у нужного профиля.
4. Подставить реальную команду запуска (`ssh`, `powershell`, другое).
5. Нажать `Connect / Reconnect`.
6. После этого вводить команду в общее поле.
7. Нажимать `Send to Selected`.

Ключевое правило:
- сначала `Connect / Reconnect`,
- потом `Send to Selected`.

## Что уже умеет
Текущий helper поддерживает:
- несколько session profiles,
- add / edit / duplicate / delete,
- import / export profiles,
- launch / reconnect managed sessions,
- shared command dispatch в выбранную сессию,
- status hints,
- operator log.

## Ограничение текущей версии
Командная отправка рассчитана в первую очередь на helper-managed sessions.

То есть надёжный сценарий такой:
- helper сам запускает или переподключает сессию,
- потом helper отправляет в неё команду.

## Что передавать Боссу
Для передачи лучше использовать архив всей папки:
- `FUBOS.zip`

Внутри уже должны быть:
- исходники helper,
- инструкции,
- setup-файлы,
- bat для сборки exe.

## Быстрая проверка после запуска
Минимальный smoke test:
1. Запустить helper.
2. Открыть список сессий.
3. Отредактировать одну сессию.
4. Выполнить `Connect / Reconnect`.
5. Отправить тестовую команду через `Send to Selected`.
6. Проверить статус и operator log.
