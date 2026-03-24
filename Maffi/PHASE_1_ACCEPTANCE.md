# Maffi — PHASE 1 ACCEPTANCE

Дата: 2026-03-24

Документ фиксирует числовые acceptance-пороги для Phase 1 и единый протокол верификации.

---

## 1) Deterministic replay

### Acceptance threshold
- Для одного и того же payload: **identical output + identical decision_trace в 100/100 прогонах**.
- Формула pass/fail: `identical_runs >= 100` из `total_runs = 100`.

### How to verify
**Тест-кейс DR-100**
1. Взять канонический payload из фикстуры `_base_payload()` (см. `tests/test_maffi_decision_engine.py`).
2. Выполнить 100 парных replay-запусков `deterministic_replay(copy.deepcopy(payload))`.
3. Для каждого запуска проверить:
   - `first == second`;
   - `first.decision_trace == second.decision_trace`.
4. Критерий прохождения: `100/100` запусков без расхождений.

Команда:
```bash
python - <<'PY'
import copy
from tests.test_maffi_decision_engine import _base_payload
from Maffi.runtime import deterministic_replay

payload = _base_payload()
identical = 0
for _ in range(100):
    first, second = deterministic_replay(copy.deepcopy(payload))
    if first == second and first.decision_trace == second.decision_trace:
        identical += 1

print(f"identical_runs={identical}/100")
raise SystemExit(0 if identical == 100 else 1)
PY
```

---

## 2) Validator coverage + severity distribution

### Acceptance threshold
- Покрыты все обязательные structural/semantic проверки:
  - required fields;
  - enum validity;
  - numeric ranges (`long/short/reject_score` в `0..100`, `confidence_hint` в `0..1`);
  - non-empty numeric `entry_candidates`;
  - cross-field (`support_level < resistance_level`);
  - `atr > 0`;
  - `last_price` corridor warning.
- Severity-распределение (ожидаемое):
  - `error` — используется для hard-invalid payload;
  - `warning` — используется для non-fatal quality signals;
  - для `degrade`: минимум **1 machine-readable признак деградации** в `context.degradation.reasons` при `input_quality_status=degraded`.

### How to verify
**Тест-кейс VC-01 (errors/warnings contract)**
1. Запустить unit тесты validator/decision:
   - missing required field;
   - bad input hard reject;
   - reject score high.
2. Проверить, что invalid payload даёт `is_valid=False` и `errors[*].severity == "error"`.
3. Проверить, что предупреждения приходят как `warnings[*].severity == "warning"`.

Команда:
```bash
pytest -q tests/test_maffi_decision_engine.py
```

**Тест-кейс VC-02 (degrade trace присутствует)**
1. Построить payload через builder со сценарием деградации.
2. Проверить:
   - `input_quality_status == "degraded"`;
   - `context.degradation.reasons` существует и содержит минимум 1 причину.

Команда:
```bash
pytest -q tests/test_maffi_payload_builder.py::MaffiPayloadBuilderIntegrationTests::test_degraded_but_usable_input
```

---

## 3) Decision quality (confidence + efficiency)

### Acceptance threshold
- Для non-reject решений (`decision in {long, short}`):
  - **confidence >= 0.55** на `input_quality_status=ok`;
  - **confidence >= 0.45** на `input_quality_status=degraded`.
- Для candidate geometry quality:
  - **efficiency_score >= 0.60** для выбранного grid-кандидата (когда поле доступно в output/trace).

> Примечание: порог по `efficiency_score` обязателен для Phase 1 acceptance и должен валидироваться на этапе candidate selection.

### How to verify
**Тест-кейс DQ-01 (confidence floor, OK)**
1. Прогнать healthy long + healthy short.
2. Убедиться, что решения не reject и `confidence >= 0.55`.

Команда:
```bash
pytest -q tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_good_long_scenario \
          tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_good_short_scenario
```

**Тест-кейс DQ-02 (confidence floor, degraded)**
1. Прогнать degraded but usable.
2. Убедиться, что `decision != reject` и `confidence >= 0.45`.

Команда:
```bash
pytest -q tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_degraded_input_remains_usable_with_penalty
```

**Тест-кейс DQ-03 (efficiency floor)**
1. Подать канонический payload `Maffi/payload_example_ok.json`.
2. Проверить в trace/output выбранный `efficiency_score`.
3. Критерий: `efficiency_score >= 0.60`.

Команда (проверка контракта поля):
```bash
python - <<'PY'
import json
from Maffi.runtime import decide

with open('Maffi/payload_example_ok.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

out = decide(payload)
trace = out.decision_trace or {}
candidate = (trace.get('selection') or {})
eff = candidate.get('efficiency_score')

if eff is None:
    raise SystemExit('efficiency_score is missing in decision_trace.selection')
if float(eff) < 0.60:
    raise SystemExit(f'efficiency_score too low: {eff}')
print(f'efficiency_score={eff}')
PY
```

---

## 4) Reject policy on negative scenarios

### Acceptance threshold
- На негативном наборе сценариев доля корректных reject: **>= 95%**.
- Негативный набор (минимум 20 кейсов) обязан включать:
  - hard bad quality;
  - high reject score (`>=60`);
  - malformed payload (missing required / invalid range / bad enum).
- Корректный reject = `decision=reject` и `reject_reason` совпадает с ожидаемой категорией.

### How to verify
**Тест-кейс RP-20**
1. Сформировать batch из 20+ негативных payload.
2. Для каждого payload сравнить фактические `decision/reject_reason` с expected.
3. Посчитать `correct_reject_ratio = correct_rejects / total_negative`.
4. Критерий: `correct_reject_ratio >= 0.95`.

Базовая команда (smoke на ключевых негативных сценариях):
```bash
pytest -q tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_bad_data_hard_reject \
          tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_chaotic_high_reject_score_rejects \
          tests/test_maffi_decision_engine.py::MaffiDecisionEngineTests::test_validator_rejects_missing_required_field
```

---

## 5) E2E bridge (canonical payload, no manual fixes)

### Acceptance threshold
- Канонический bridge flow проходит end-to-end без ручных фиксов данных.
- Минимальный порог: **1/1 успешный прогон** канонического payload pipeline.
- Условия pass:
  - payload собран bridge-ом и валиден;
  - runtime возвращает решение (`long|short|reject`) без ручной правки payload;
  - mapping contract соблюдён.

### How to verify
**Тест-кейс E2E-BRIDGE-01**
1. Запустить `machine_response -> symbol_object -> payload -> decide`.
2. Проверить schema/symbol/quality и корректный runtime output.
3. Убедиться, что `BRIDGE_MAPPING_CONTRACT` не нарушен.

Команда:
```bash
pytest -q tests/test_maffi_orchestration_bridge.py
```

---

## Phase 1 Acceptance Decision Rule

Phase 1 считается принятой только если одновременно выполняются все условия:
1. DR-100: `100/100` deterministic identical replay.
2. Validator coverage + severity distribution подтверждены.
3. Decision quality пороги (`confidence`, `efficiency_score`) выдержаны.
4. Reject policy на негативном наборе `>=95%` корректных reject.
5. E2E bridge канонический прогон успешен без ручных фиксов.
