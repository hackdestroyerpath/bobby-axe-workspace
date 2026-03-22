# PowerShell Guide — Snapshot Lookup UI

## Для чего это
Этот гайд показывает, как с твоего компьютера через PowerShell подключиться к snapshot lookup панели на VPS, открыть её в браузере и понять, где что смотреть.

---

## 1. Что уже должно быть запущено на VPS
На VPS должен быть запущен snapshot lookup UI.

Команда на VPS:

```bash
cd /home/openclaw/.openclaw/workspace-jack
./tools/run_snapshot_lookup_ui.sh
```

После запуска сервис слушает локально:

```text
127.0.0.1:8787
```

---

## 2. Как подключиться с PowerShell
На своём компьютере открой **PowerShell** и выполни:

```powershell
ssh -L 8787:127.0.0.1:8787 openclaw@vds2933049.my-ihor.ru
```

Что это делает:
- пробрасывает локальный порт `8787`
- на удалённый `127.0.0.1:8787` на VPS
- после этого твой браузер на компьютере сможет открыть панель как локальный сайт

Важно:
- это окно PowerShell нужно **держать открытым**, пока пользуешься панелью
- если закроешь SSH-сессию, туннель исчезнет

---

## 3. Что открыть в браузере
После того как SSH-туннель поднят, открой в браузере:

```text
http://127.0.0.1:8787/
```

Если всё хорошо, увидишь страницу **Snapshot Lookup**.

---

## 4. Что вводить в панели
В верхнем блоке есть поля:

### Поле 1 — Snapshot ID
Сюда вставляешь:
- `snapshot_id`
- или `bundle_id`
- или `correlation_id`

Для первого теста можно использовать, например:

```text
snapshot_20260321T235503Z_c0a7cb5a
```

или

```text
snapshot_20260321T234848Z_1851b6be
```

### Поле 2 — optional symbol
Обычно можно оставить пустым.

Нужно только если snapshot multi-symbol и ты хочешь выбрать конкретный symbol, например:

```text
BTCUSDC
```

---

## 5. Какие кнопки за что отвечают
### Lookup
Основной запрос.
После нажатия панель подтягивает все данные по snapshot.

### Refresh
Повторно перечитывает текущий snapshot.

### Auto-refresh every 7s
Автоматически обновляет snapshot каждые 7 секунд.

### Download JSON
Скачивает текущий lookup-result как JSON.

### Save to Project
Сохраняет текущий lookup-result внутрь проекта на VPS.

---

## 6. Где что смотреть в панели
## Верхний блок
Это управление:
- вводишь `snapshot_id`
- нажимаешь `Lookup`

## Operator Summary
Это самый важный быстрый блок.
Смотри там:
- `lookup`
- `symbol`
- `as_of_utc`
- `production`
- `Ben_Kim`
- `Jusetta`
- `Frame coverage`

Если тут всё зелёное — snapshot в хорошем состоянии.

## Snapshot Meta
Это паспорт snapshot:
- `snapshot_id`
- `bundle_id`
- `correlation_id`
- `symbol`
- `symbols`
- `as_of_utc`

## Readiness
Здесь смотри по фреймам:
- `1m`
- `5m`
- `60m`

Если все `ready`, значит snapshot пригоден для нормальной downstream-работы.

## Downstream
Здесь смотри:
- usable for `Ben_Kim`
- usable for `Jusetta`
- blocking reasons

## Artifacts
Тут лежат refs на JSON/export/source tables.

## Access Stats
Это важный блок контроля.
Тут видно:
- сколько раз вообще открывали snapshot
- сколько пользователей его трогало
- кто именно обращался
- сколько запросов у каждого

Если выдашь ключ Ben или Jusetta, тут будет видно их активность.

## Errors / Notes
Смотри сюда, если что-то не так:
- snapshot не найден
- frame не готов
- symbol ambiguous
- есть техническая заметка

---

## 7. Куда вводить ключ
### В самой панели ключ сейчас не вводится в отдельное поле
Текущий режим такой:
- UI открываешь ты как оператор через туннель
- ключи в первую очередь нужны для API-вызовов агентам (`Ben_Kim`, `Jusetta` и т.д.)

То есть:
- **для панели** ты просто открываешь её по туннелю
- **для агентов** ключ передаётся в HTTP header:

```text
X-API-Key: <KEY>
```

Если потом захотим, можно будет добавить и поле для ключа прямо в UI, но сейчас этого поля нет.

---

## 8. Как агенту пользоваться ключом
Пример запроса через ключ:

```bash
curl -H "X-API-Key: <KEY>" "http://127.0.0.1:8787/lookup?snapshot_id=snapshot_20260321T235503Z_c0a7cb5a"
```

Пример с symbol:

```bash
curl -H "X-API-Key: <KEY>" "http://127.0.0.1:8787/lookup?snapshot_id=snapshot_20260321T235503Z_c0a7cb5a&symbol=BTCUSDC"
```

---

## 9. Как проверить, что всё работает
### На VPS
Можно проверить health:

```bash
curl http://127.0.0.1:8787/health
```

Ожидаемо:

```json
{
  "status": "ok",
  "auth_optional": false,
  "auth_mode": "mandatory"
}
```

### На твоём компьютере
Если туннель поднят, просто открой:

```text
http://127.0.0.1:8787/
```

---

## 10. Если панель не открывается
Проверь по порядку:

### 1. Сервис запущен ли на VPS
```bash
cd /home/openclaw/.openclaw/workspace-jack
./tools/run_snapshot_lookup_ui.sh
```

### 2. Туннель поднят ли
```powershell
ssh -L 8787:127.0.0.1:8787 openclaw@vds2933049.my-ihor.ru
```

### 3. Не закрыт ли PowerShell с туннелем
Если окно закрыто — туннеля нет.

### 4. Не занят ли локальный порт 8787
Если занят, можно потом перенести на другой порт.

---

## 11. Где лежит этот проект
Основные файлы:
- `tools/snapshot_lookup_backend.py`
- `tools/snapshot_lookup_server.py`
- `tools/run_snapshot_lookup_ui.sh`
- `tools/test_snapshot_lookup_ui.sh`
- `runbooks/snapshot_lookup_ui_runbook.md`
- `runbooks/snapshot_lookup_locked_access_runbook.md`

---

## 12. Короткий порядок действий
1. На VPS запусти UI:
   ```bash
   cd /home/openclaw/.openclaw/workspace-jack
   ./tools/run_snapshot_lookup_ui.sh
   ```
2. На своём компьютере в PowerShell подними туннель:
   ```powershell
   ssh -L 8787:127.0.0.1:8787 openclaw@vds2933049.my-ihor.ru
   ```
3. В браузере открой:
   ```text
   http://127.0.0.1:8787/
   ```
4. Вставь `snapshot_id`
5. Нажми `Lookup`
6. Смотри `Operator Summary`, `Readiness`, `Access Stats`

---

## Итог
Для тебя сейчас рабочий режим такой:
- доступ к панели — через SSH-туннель
- доступ агентов — через API keys
- учёт запросов — централизованно в этой панели
