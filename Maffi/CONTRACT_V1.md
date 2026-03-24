# Maffi Contract v1

Статус: canonical for orchestration parsing.

## Parsing stability rules

Для стабильного orchestration parsing применяются правила:
- ключи фиксированы и не переименовываются между patch/minor релизами `schema_version=1.x`;
- неизвестные ключи допускаются только как optional additions и не ломают required-контур;
- порядок шагов в `decision_trace.steps` обязателен и интерпретируется как execution order.

---

## `validation_summary` schema

Назначение: агрегировать итог валидации входа и деградаций качества.

### Stable keys
- `counts`
- `errors`
- `warnings`
- `degrade`
- `top_reasons`

### Required fields
- `counts` (object)
  - `total_checks` (integer, >= 0)
  - `passed` (integer, >= 0)
  - `failed` (integer, >= 0)
  - `warnings` (integer, >= 0)
- `errors` (array of string, может быть пустым)
- `warnings` (array of string, может быть пустым)
- `degrade` (object)
  - `is_degraded` (boolean)
  - `degrade_score` (number, 0..1)
- `top_reasons` (array of object, может быть пустым)
  - `code` (string)
  - `count` (integer, >= 1)

### Optional fields
- `counts.skipped` (integer, >= 0)
- `degrade.sources` (array of string)
- `degrade.policy` (string)
- `top_reasons[].severity` (`error | warning | info`)

---

## `decision_summary` schema

Назначение: короткий digest принятого решения и логики TP/SL.

### Stable keys
- `direction`
- `selected_candidate_id`
- `tp_sl_logic_digest`

### Required fields
- `direction` (`long | short | reject`)
- `selected_candidate_id` (string; для `reject` допускается `"none"`)
- `tp_sl_logic_digest` (object)
  - `mode` (`atr_buffered | structure_based | mixed | none`)
  - `tp_basis` (string)
  - `sl_basis` (string)
  - `rr_estimate` (number, > 0 для `long/short`, `0` для `reject`)

### Optional fields
- `tp_sl_logic_digest.constraints` (array of string)
- `tp_sl_logic_digest.rejected_by` (string)
- `tp_sl_logic_digest.notes` (array of string)

---

## `decision_trace` schema

Назначение: детерминированный ordered trace по ключевым шагам.

### Stable keys
- `steps`

### Required fields
- `steps` (array length = 6; порядок фиксирован):
  1. `gate`
  2. `direction`
  3. `range`
  4. `grid_count`
  5. `tp_sl`
  6. `confidence`

Каждый элемент `steps[]` обязан иметь:
- `name` (string, одно из фиксированных значений выше)
- `status` (`pass | fail | skip`)
- `reason` (string, non-empty)

### Optional fields for each step
- `inputs` (object)
- `outputs` (object)
- `metrics` (object)
- `warnings` (array of string)

### Determinism constraints
- `steps[i].name` должен совпадать с фиксированным названием позиции `i`.
- При `status=skip` поле `reason` остается обязательным.
- `inputs/outputs/metrics` должны быть JSON-serializable без enum/object ссылок.

---

## Minimal canonical example

```json
{
  "validation_summary": {
    "counts": {
      "total_checks": 12,
      "passed": 10,
      "failed": 0,
      "warnings": 2
    },
    "errors": [],
    "warnings": [
      "low_liquidity_window"
    ],
    "degrade": {
      "is_degraded": true,
      "degrade_score": 0.15,
      "sources": [
        "spread_widened"
      ]
    },
    "top_reasons": [
      {
        "code": "spread_widened",
        "count": 2,
        "severity": "warning"
      }
    ]
  },
  "decision_summary": {
    "direction": "long",
    "selected_candidate_id": "grid_2",
    "tp_sl_logic_digest": {
      "mode": "mixed",
      "tp_basis": "resistance_plus_atr_buffer",
      "sl_basis": "support_minus_atr_buffer",
      "rr_estimate": 1.9,
      "constraints": [
        "min_tp_distance_ok",
        "min_sl_distance_ok"
      ]
    }
  },
  "decision_trace": {
    "steps": [
      {"name": "gate", "status": "pass", "reason": "input accepted"},
      {"name": "direction", "status": "pass", "reason": "long_score dominates"},
      {"name": "range", "status": "pass", "reason": "range geometry valid"},
      {"name": "grid_count", "status": "pass", "reason": "best grid_count=5"},
      {"name": "tp_sl", "status": "pass", "reason": "tp/sl constraints satisfied"},
      {"name": "confidence", "status": "pass", "reason": "confidence >= threshold"}
    ]
  }
}
```
