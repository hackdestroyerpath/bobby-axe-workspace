# Maffi — ТЗ по шагам для завершения алгоритма

Статус: рабочее ТЗ на завершение Maffi после объединения документации и runtime-кода в директорию `Maffi/`.

---

# Общая цель

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

При этом поведение должно быть:
- deterministic
- contract-first
- traceable
- пригодным для orchestration handoff

---

# PHASE 1 — Finish Core Runtime and Decision Quality

## 1. Цель фазы

Завершить ядро Maffi так, чтобы оно не просто принимало валидный payload, а действительно строило торгуемое решение по сетке с прозрачной логикой выбора направления, диапазона, количества сеток, TP и SL.

Сейчас каркас уже есть:
- validator
- preprocessing
- payload builder
- decision engine
- bridge
- formatter
- replay

Но Phase 1 должна довести это до уровня **рабочего core-algorithm**.

---

## 2. Что именно должно быть готово по завершении Phase 1

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

## 3. Подзадачи Phase 1

## 3.1. Жёстко зафиксировать runtime contract v1

### Нужно сделать
- Утвердить единый runtime input schema.
- Убрать разночтения между `Maffi/TODO.md`, `Maffi/CONTRACT_V0_1.md` и реальными dataclass/model полями.
- Выделить поля на:
  - required
  - optional
  - derived
  - trace-only

### Результат
Один канонический контракт, от которого зависят validator, bridge и formatter.

### Артефакт
- `Maffi/CONTRACT_V1.md`
- при необходимости `Maffi/contract_v1.json`

---

## 3.2. Довести validator до production-порогов

### Нужно сделать
Validator должен проверять не только наличие полей, но и смысл:
- диапазоны чисел;
- корректность enum-значений;
- `support_level < resistance_level`;
- `entry_candidates` не пустой и отсортированный;
- `confidence_hint` в пределах `0..1`;
- `long_score / short_score / reject_score` в рамках `0..100`;
- `atr > 0`;
- `last_price > 0`;
- cross-field consistency между режимом, доминирующей стороной и score.

### Нужно добавить
- severity model (`error`, `warning`, `degrade`)
- machine-readable validation trace
- отдельный validation summary block

### Результат
Validator перестаёт быть просто gatekeeper и становится нормальным semantic quality filter.

---

## 3.3. Усилить preprocessing / feature extraction

### Нужно сделать
Слой preprocessing должен стабильно извлекать базовые market-structure признаки из тиков:
- OHLCV aggregation для `1m`, `5m`, `15m`
- realized volatility
- price range
- buy/sell volume split
- imbalance
- trend structure
- support/resistance
- market regime candidates
- volatility regime
- entry candidates

### Нужно улучшить
- устойчивость к sparse input
- устойчивость к noisy input
- явную обработку gaps
- degradation trace для плохих окон

### Результат
На вход payload builder приходит уже clean, explainable feature set.

---

## 3.4. Пересобрать decision engine вокруг grid-логики

### Проблема сейчас
Текущий decision engine в основном выбирает `LONG/SHORT` по `long_score/short_score` и потом подбирает entry + TP/SL. Это хороший skeleton, но он ещё не полностью выражает логику самой сетки.

### Нужно сделать
Decision engine должен отдельно решать:
1. пригоден ли рынок для сетки вообще;
2. какой directional bias доминирует;
3. какой диапазон сетки использовать;
4. сколько уровней сетки оптимально;
5. где заканчивается идея (`tp`);
6. где ломается идея (`sl`).

### Для этого нужны внутренние шаги
- reject gate
- direction resolver
- range resolver
- grid count resolver
- tp/sl resolver
- confidence adjuster
- rationale synthesizer

### Результат
Полноценное decision core, а не только routing между Long/Short.

---

## 3.5. Добавить grid candidate scoring

### Нужно сделать
Ввести механизм сравнения нескольких кандидатов сетки.

Каждый кандидат должен иметь:
- `grid_lower_price`
- `grid_upper_price`
- `grid_width`
- `grid_count`
- `grid_step`
- `efficiency_score`
- `candidate_notes`

### Минимальные подскоринги
- range utilization
- oscillation quality
- step quality
- stability
- boundary respect

### Результат
Maffi выбирает сетку не из одной подсказки, а из реально ранжированного набора.

---

## 3.6. Формализовать TP/SL policy

### Нужно сделать
Нужно отделить TP/SL логику от случайной arithmetic-эвристики.

Для Long:
- `tp` должен лежать в зоне логичного завершения движения / сопротивления;
- `sl` — за support / структурным сломом.

Для Short:
- `tp` — в зоне поддержки / нижней цели;
- `sl` — за resistance / структурным сломом.

### Нужно описать
- базовые формулы
- ATR-based buffers
- ограничения против слишком близкого TP/SL
- reject при бессмысленной геометрии

### Результат
TP/SL становятся воспроизводимыми и проверяемыми.

---

## 3.7. Усилить formatter и traceability

### Нужно сделать
Выходной формат должен быть стабилен и удобен для downstream систем.

Добавить:
- `grid_upper_price`
- `grid_lower_price`
- `grid_count`
- `grid_step`
- `efficiency_score`
- `selected_candidate_id`
- `validation_summary`
- `decision_summary`

### Результат
Downstream системы и Bobby Axe получают не только ответ, но и понятный разбор, как он получился.

---

## 3.8. Довести тесты до реального acceptance coverage

### Нужно сделать
Нужны тесты минимум на сценарии:
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

### Результат
Есть регрессионная страховка от поломок при развитии алгоритма.

---

## 4. Deliverables Phase 1

К концу фазы должны существовать:
- `Maffi/CONTRACT_V1.md`
- runtime implementation inside `Maffi/runtime/`
- updated tests
- payload examples: ok / degraded / reject
- decision trace examples
- short `PHASE_1_ACCEPTANCE.md`

---

## 5. Acceptance criteria Phase 1

Фаза считается завершённой, если:
1. один канонический контракт утверждён;
2. validator проверяет и структуру, и семантику;
3. preprocessing стабильно даёт usable features;
4. decision engine выбирает не только сторону, но и геометрию сетки;
5. TP/SL воспроизводимы;
6. grid candidate scoring работает;
7. formatter стабилен;
8. есть regression tests;
9. orchestration bridge может отдать payload в runtime без ручного вмешательства.

---

# PHASE 2 — Orchestration / Live Bridge / Runtime Wiring

## Заголовки задач
- Canonical live entrypoint for Maffi
- Ben_Kim -> Maffi symbol-object mapping finalization
- Orchestration bridge hardening
- Live payload transport contract
- Error propagation and retry policy
- Runtime status model: ready / partial / blocked
- E2E integration tests with orchestration layer
- Release checkpoint for controlled live-run

---

# PHASE 3 — Hardening / Replay / Production Readiness

## Заголовки задач
- Deterministic replay pack
- Historical regression suite
- Threshold calibration by ticker class
- Confidence calibration and reject policy tuning
- Observability / metrics / audit trail
- Release checklist and go-live criteria
- Maintenance cadence and post-release governance
