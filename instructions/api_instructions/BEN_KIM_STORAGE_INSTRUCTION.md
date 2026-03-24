# BEN_KIM_STORAGE_INSTRUCTION

## Purpose
Инструкция для `Ben_Kim`: как класть финальные analysis objects в Jack-controlled SQL storage.

---

## 1. Core storage rule
- `1 machine response = 1 storage object`
- `1 symbol-run = 1 batch`
- normal batch target = `12` отдельных object rows

Ben не пишет напрямую в SQL.
Ben пишет только через sanctioned storage write path.

---

## 2. Canonical storage API
Storage API runtime:
- base URL: `http://127.0.0.1:8792`

Write endpoints:
- `POST /analysis/object`
- `POST /analysis/batch`

Read endpoints:
- `GET /analysis/object/:object_id`
- `GET /analysis/batch/:batch_id`
- `GET /analysis/latest`

---

## 3. Auth rule
Для storage write использовать только отдельный Ben storage writer key.

Нельзя:
- использовать collector machine keys как writer keys
- использовать master/admin key как обычный write key

Canonical writer identity:
- `key_id = ben-storage-writer-001`
- `client_id = ben_kim_storage_writer`
- `scope = analysis.write`

---

## 4. What Ben must write
Ben должен сформировать:
1. `objects[]` — storage objects по object contract
2. `batch` — batch envelope по batch contract

Основной путь:
- `POST /analysis/batch`

---

## 5. Minimal object fields to preserve
Ben не должен терять:
- `object_id`
- `batch_id`
- `symbol`
- `strategy`
- `timeframe`
- `machine_id`
- `agent_id`
- `request_id`
- `requested_at`
- `generated_at`
- `source`
- `status`
- `object_readiness`
- `summary_json`
- `meta_json`
- `features_json`
- `errors_json`
- `packaging_issues_json`
- `client_id`
- `api_key_id`

---

## 6. Minimal batch checklist
Перед `POST /analysis/batch` Ben должен проверить:
- один `symbol` на весь batch
- один `batch_id` на все objects
- `actual_object_count` совпадает с `objects.length`
- `object_ids_json` согласован
- missing branches surfaced honestly
- raw secrets не попали в payload

---

## 7. Success criteria
### Success for batch write
Storage returns:
- `status = stored`
- `batch_id`
- `storage_status = stored`
- `stored_object_count`
- `storage_request_id`

После этого Ben должен сохранить refs:
- `batch_id`
- `storage_request_id`
- `stored_object_count`

---

## 8. Read-back rule
Ben может использовать limited read-back для проверки:
- `GET /analysis/batch/:batch_id`
- `GET /analysis/latest?symbol=...`

Но storage read не должен превращаться в direct SQL habits.

---

## 9. Hard prohibitions
Ben не должен:
- слать один merged blob вместо 12 objects
- писать напрямую в SQL
- использовать collector key как storage writer key
- печатать raw secrets
- терять `machine_id / client_id / api_key_id`
- скрывать `partial/error` внутри fake-ready payload

---

## 10. Minimal success report upward
После storage write Ben должен уметь коротко сообщить:
- `symbol`
- `batch_id`
- `stored_object_count`
- `batch_status`
- `batch_readiness`
- `storage_request_id`
- blockers, if any
