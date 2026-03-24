# MAFFI_STORAGE_INSTRUCTION

## Purpose
Инструкция для `Maffi`: как класть свои финальные objects в Jack-controlled SQL storage.

Формат Maffi object может быть уточнён отдельно, но storage contour, auth model и audit discipline уже фиксируются сейчас.

---

## 1. Core storage rule
`Maffi` не пишет напрямую в SQL.

`Maffi` пишет только через sanctioned storage write path.

Правило хранения:
- `1 Maffi final decision = 1 storage object`
- если появится batch model для Maffi, он должен быть таким же контролируемым, как у Ben_Kim

---

## 2. Canonical storage API
Storage API runtime:
- base URL: `http://127.0.0.1:8792`

Minimal write path:
- `POST /analysis/object`

Если у Maffi появится batch write model:
- `POST /analysis/batch`

Minimal read path:
- `GET /analysis/object/:object_id`
- `GET /analysis/latest`

---

## 3. Auth rule
Для записи в storage Maffi должен использовать отдельный storage writer key.

Нельзя:
- использовать collector machine keys как storage writer keys
- использовать master/admin key как обычный runtime writer key

### Canonical principle
- отдельный producer key
- отдельный `key_id`
- отдельный `client_id`
- audit must identify Maffi independently

---

## 4. What Maffi must preserve in object
Даже до финального object schema, Maffi обязан не терять:
- `object_id`
- `symbol`
- `agent_id`
- `request_id`
- `generated_at`
- `status`
- `client_id`
- `api_key_id`
- payload body
- quality/readiness markers
- storage traceability ids after write

---

## 5. Success criteria
### Success for object write
Storage returns:
- `status = stored`
- `object_id`
- `storage_status = stored`
- `storage_request_id`

После этого Maffi должен сохранить refs:
- `object_id`
- `storage_request_id`

---

## 6. Read-back rule
Maffi может использовать limited read-back для verification:
- object by `object_id`
- latest object by symbol if such view is allowed

Но не должен обходить sanctioned API direct SQL reads into runtime logic.

---

## 7. Audit rule
Каждая write/read операция Maffi должна быть отслеживаема через:
- `key_id`
- `client_id`
- `request_id`
- `symbol`
- `object_id`
- `result_status`

Это нужно для owner dashboard и usage tracking.

---

## 8. Hard prohibitions
Maffi не должен:
- писать напрямую в SQL
- печатать raw secrets
- использовать collector key как storage writer key
- терять traceability ids
- подменять финальный storage write локальным “кажется записал” состоянием

---

## 9. Important note
Когда будет утверждён окончательный Maffi object format,
этот документ должен быть дополнен отдельным Maffi object contract.

Но уже сейчас storage contour для Maffi фиксируется как:
- key-controlled
- auditable
- Jack-managed
- readable back only through sanctioned storage API
