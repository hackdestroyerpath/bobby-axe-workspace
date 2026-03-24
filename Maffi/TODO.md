# MAFFI APPROVED INSTRUCTION

Статус: утвержденная инструкция по завершению алгоритма Maffi.
Дата: 2026-03-24

---

# Цель

Довести Maffi до состояния, в котором агент по одному тикеру и подготовленному payload стабильно возвращает:
- `direction` (`Long` / `Short` / `Reject`)
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `tp`
- `sl`
- `confidence`
- `rationale`
- `decision_trace`

Требования к поведению:
- deterministic
- contract-first
- traceable
- пригодное для orchestration handoff

---

# PHASE 1 — Finish Core Runtime and Decision Quality

## Цель Phase 1

Завершить ядро Maffi так, чтобы оно не просто принимало валидный payload, а действительно строило торгуемое решение по сетке с прозрачной логикой выбора направления, диапазона, количества сеток, TP и SL.

Текущий каркас уже включает:
- validator
- preprocessing
- payload builder
- decision engine
- bridge
- formatter
- replay

Phase 1 должна довести это до уровня полноценного рабочего core-algorithm.

---

## Что должно быть готово по завершении Phase 1

По одному тикеру система должна уметь:
1. принять входной payload;
2. проверить hard/soft data quality;
3. классифицировать режим рынка;
4. определить directional bias;
5. построить кандидаты сетки;
6. выбрать лучший кандидат;
7. вычислить `tp/sl`;
8. вернуть решение в стабильном формате;
9. объяснить решение через rationale и trace.

---

## Подзадачи Phase 1

### 1. Зафиксировать единый runtime contract v1
- убрать расхождения между `TODO`, `CONTRACT_V0_1` и runtime-моделями;
- разделить поля на required / optional / derived / trace-only.
- Depends on: `[]`
- Priority: `P0`
- Owner: `Maffi`
- Completion artifact: `Maffi/CONTRACT_V1.md` (+ `Maffi/contract_v1.json`, если добавляется)

Артефакты:
- `CONTRACT_V1.md`
- при необходимости `contract_v1.json`

### 2. Довести validator до production-порогов
Validator должен проверять:
- диапазоны чисел;
- корректность enum-значений;
- `support_level < resistance_level`;
- непустой `entry_candidates`;
- `confidence_hint` в диапазоне `0..1`;
- `long_score / short_score / reject_score` в диапазоне `0..100`;
- `atr > 0`;
- `last_price > 0`;
- cross-field consistency.

Также добавить:
- severity model (`error`, `warning`, `degrade`)
- machine-readable validation trace
- validation summary block
- Depends on: `[1]`
- Priority: `P0`
- Owner: `Maffi`
- Completion artifact: `tests/`-кейс(ы) validator + пример `validation_trace` в `Maffi/examples/validator_trace.json`

### 3. Усилить preprocessing / feature extraction
Должны стабильно извлекаться:
- OHLCV для `1m`, `5m`, `15m`
- realized volatility
- price range
- buy/sell volume split
- imbalance
- trend structure
- support/resistance
- market regime candidates
- volatility regime
- entry candidates

Улучшить:
- устойчивость к sparse input
- устойчивость к noisy input
- явную обработку gaps
- degradation trace
- Depends on: `[2]`
- Priority: `P0`
- Owner: `Maffi`
- Completion artifact: пример `Maffi/examples/preprocessing_features.json` + тест(ы) preprocessing

### 4. Пересобрать decision engine вокруг grid-логики
Decision engine должен решать:
1. пригоден ли рынок для сетки;
2. какой directional bias доминирует;
3. какой диапазон сетки использовать;
4. сколько уровней сетки оптимально;
5. где заканчивается идея (`tp`);
6. где ломается идея (`sl`).

Внутренние блоки:
- reject gate
- direction resolver
- range resolver
- grid count resolver
- tp/sl resolver
- confidence adjuster
- rationale synthesizer
- Depends on: `[3]`
- Priority: `P0`
- Owner: `Maffi`
- Completion artifact: тест(ы) decision engine + пример `Maffi/examples/decision_trace_core.json`

### 5. Добавить grid candidate scoring
Для каждого кандидата должны быть:
- `grid_lower_price`
- `grid_upper_price`
- `grid_width`
- `grid_count`
- `grid_step`
- `efficiency_score`
- `candidate_notes`

Подскоринги:
- range utilization
- oscillation quality
- step quality
- stability
- boundary respect
- Depends on: `[4]`
- Priority: `P1`
- Owner: `Maffi`
- Completion artifact: `Maffi/examples/grid_candidates_scored.json` + тест(ы) scoring

### 6. Формализовать TP/SL policy
Для Long:
- `tp` в зоне логичного завершения движения / сопротивления;
- `sl` за support / структурным сломом.

Для Short:
- `tp` в зоне поддержки / нижней цели;
- `sl` за resistance / структурным сломом.

Описать:
- базовые формулы
- ATR-based buffers
- ограничения против слишком близкого TP/SL
- reject при бессмысленной геометрии
- Depends on: `[4]`
- Priority: `P1`
- Owner: `Maffi`
- Completion artifact: `Maffi/TP_SL_POLICY.md` + тест(ы) `tp/sl` резолвера

### 7. Усилить formatter и traceability
Добавить в финальный output:
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `grid_step`
- `efficiency_score`
- `selected_candidate_id`
- `validation_summary`
- `decision_summary`
- Depends on: `[5, 6]`
- Priority: `P1`
- Owner: `Maffi`
- Completion artifact: snapshot/fixture финального ответа в `Maffi/examples/final_output_v1.json`

### 8. Довести тесты до acceptance coverage
Сценарии:
- healthy long trend
- healthy short trend
- balanced range
- chaotic reject
- degraded but usable
- bad input hard reject
- conflicting signal set
- weak confidence reject
- malformed payload
- bridge e2e
- Depends on: `[7]`
- Priority: `P0`
- Owner: `Maffi`
- Completion artifact: `Maffi/PHASE_1_ACCEPTANCE.md` + green test run (пример вывода `pytest`)

---

## Deliverables Phase 1
- `CONTRACT_V1.md`
- runtime implementation
- updated tests
- payload examples: ok / degraded / reject
- decision trace examples
- `PHASE_1_ACCEPTANCE.md`

## Acceptance criteria Phase 1
Phase 1 завершена, если:
1. один канонический контракт утвержден;
2. validator проверяет структуру и семантику;
3. preprocessing стабильно дает usable features;
4. decision engine выбирает сторону и геометрию сетки;
5. TP/SL воспроизводимы;
6. grid candidate scoring работает;
7. formatter стабилен;
8. есть regression tests;
9. orchestration bridge может отдать payload в runtime без ручного вмешательства.

---

# PHASE 2 — Заголовки
- Canonical live entrypoint for Maffi
- Ben_Kim -> Maffi mapping finalization
- Orchestration bridge hardening
- Live payload transport contract
- Error propagation and retry policy
- Runtime statuses: ready / partial / blocked
- E2E orchestration integration

---

# PHASE 3 — Заголовки
- Deterministic replay pack
- Historical regression suite
- Threshold calibration by ticker class
- Confidence / reject tuning
- Observability and audit trail
- Release checklist and go-live criteria
- Maintenance cadence
