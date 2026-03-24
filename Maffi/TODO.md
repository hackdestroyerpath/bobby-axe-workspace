# MAFFI — PROJECT ANALYSIS + TODO (на утверждение)

Дата анализа: **2026-03-24**  
Режим: **статический обзор репозитория (без запуска кода)**

---

## 1) Как я изучал проект (план ревью)

1. Проверил структуру репозитория и ключевые контуры (`TRADING_ALGOS`, `new_collector`, `tests`, корневые документы).
2. Сверил архитектурные документы и текущий operational-план по Phase 2/3.
3. Просмотрел runtime-реализацию машин (`machine_registry.py`, `runtime_contract.py`, `machines.py`, `strategy_cores.py`).
4. Проверил интеграционный и контрактный тестовый слой (`tests/test_phase3_integration.py` и смежные тесты).
5. Проверил packaging/storage handoff слой (`ben_kim_packaging.py`).
6. Зафиксировал факты: что уже готово, что частично готово, что отсутствует в контуре `Maffi`.
7. Сформировал:
   - основной (базовый) to-do list;
   - модифицированный to-do list (с приоритизацией и checkpoint-логикой).

---

## 2) Что подтверждено по проекту (факты)

### 2.1. Что уже есть в репозитории
- Сильный contract-first контур для `TRADING_ALGOS`:
  - единый runtime pipeline;
  - frozen registry на 12 машин;
  - унифицированные status semantics (`ready/partial/error`);
  - shared normalizer + feature engine;
  - strategy family cores;
  - integration/unit test-слой;
  - начат/реализован packaging layer для symbol-scoped objects (`Ben_Kim`).

### 2.2. Что важно для `Maffi`
- Папка `Maffi/` содержит только этот TODO-документ.
- Отдельного runtime/validator/scoring/candidate/TP-SL кода для `Maffi` в репозитории пока нет.
- Значит `Maffi` нужно строить как новый контур, но на уже существующих дисциплинах проекта:
  - contract-first;
  - traceability;
  - deterministic behavior;
  - честные `Reject/Partial/Error` причины.

### 2.3. Основной риск
- Если начать с «логики Long/Short» без схемы входа, валидации и воспроизводимого payload, получится хрупкая эвристика.
- Правильная последовательность: **schema → validator → payload builder → decision/scoring → selection/TP-SL → trace/tests**.

---

## 3) Основной TO-DO list (базовый)

## A. Contract & модели
1. Зафиксировать `MaffiInputPayload` и `MaffiOutput` (typed, versioned).
2. Ввести enum-слой (`Decision`, `QualityStatus`, `MarketRegime`, `DominantSide`, `VolatilityRegime`).
3. Добавить совместимый формат traceability (`schema_version`, `generated_at_utc`, `input_quality_status`, `reject_reason`).

## B. Валидация
4. Реализовать structural validation обязательных блоков payload.
5. Реализовать semantic validation диапазонов и инвариантов (`confidence 0..1`, score 0..100, price relations).
6. Реализовать cross-field validation (consistency между quality/order-flow/candidates/market snapshot).
7. Ввести `ValidationResult` с `is_valid`, `errors`, `warnings`, `severity`.

## C. Preprocessing layer
8. Спроектировать модуль очистки тиков (`duplicates`, `bad ticks`, gap metrics).
9. Реализовать агрегации (1m/5m/15m OHLC + volume stats + local range).
10. Реализовать volatility features.
11. Реализовать order-flow features.
12. Реализовать trend-structure features.
13. Реализовать market regime classifier (explainable, score-based).
14. Реализовать support/resistance block.
15. Реализовать grid candidates generator (1..N candidates + quality metrics).
16. Реализовать payload builder с поддержкой `ok/degraded/bad` входа.

## D. Decision layer
17. Зафиксировать reject policy до выбора направления.
18. Реализовать composite scoring (`long_score`, `short_score`, `reject_score`).
19. Реализовать confidence policy с штрафами за качество данных/нестабильность.
20. Реализовать candidate selector (не выбирать «из воздуха», только из входного списка).
21. Реализовать TP/SL policy (направление + волатильность + уровни).
22. Собрать итоговый `decision_engine`.

## E. Explainability, replay, tests
23. Добавить rationale generator.
24. Добавить machine-readable decision trace.
25. Добавить deterministic replay (одинаковый payload => одинаковый output).
26. Добавить unit tests: validator/scoring/candidate/tp_sl.
27. Добавить e2e tests: good long, good short, bad data reject, chaotic reject, degraded usable.

---

## 4) Модифицированный TO-DO list (рекомендованный к исполнению сейчас)

Ниже — тот же список, но адаптированный под текущую зрелость репозитория и управление риском.

## Sprint 0 — Decision Gate (1 короткий цикл)
1. Утвердить минимальный входной контракт `Maffi v0.1` (не весь production payload).
2. Утвердить формулу `Reject`-критериев (hard fail vs soft degrade).
3. Утвердить список обязательных полей для первого боевого запуска.

**Artifact:** `Maffi/CONTRACT_V0_1.md` + `Maffi/payload_example_ok.json` + `Maffi/payload_example_reject.json`.

## Sprint 1 — Skeleton MVP (высший приоритет)
4. Создать каркас модулей `maffi/` (enums/models/validator/decision_engine/formatter).
5. Реализовать validator + минимальный `decision_engine` (`Reject | Long | Short`) без сложной математики.
6. Реализовать базовый candidate selection и TP/SL с детерминированными правилами.

**Artifact:** первый end-to-end проход на фиксированном payload fixture.

## Sprint 2 — Feature depth (средний приоритет)
7. Довести preprocessing-модули: volatility/order_flow/trend/regime/support-resistance/grid candidates.
8. Включить composite scoring и confidence adjustments.
9. Подключить decision trace и explainability-блок.

**Artifact:** `Maffi/PHASE_2_REPORT.md` с матрицей quality и примерами решений.

## Sprint 3 — Hardening (обязательный перед production)
10. Добавить deterministic replay и regression fixtures.
11. Закрыть unit+e2e тесты по минимальному набору сценариев.
12. Ввести readiness-статусы для релиза: `ready`, `partial`, `blocked`.

**Artifact:** `Maffi/READINESS_MATRIX.md` + стабильный test suite.

---

## 5) Приоритеты (что делать прямо сейчас)

**P0 (сразу):** пункты 1–6 из модифицированного списка.  
**P1 (следом):** пункты 7–9.  
**P2 (перед релизом):** пункты 10–12.

---

## 6) Сигнал готовности на утверждение

Этот документ подготовлен как обновлённый `to-do list` после детального анализа текущего состояния проекта.

Если утверждаете, следующий шаг для исполнителя:
- взять **модифицированный TO-DO list** как канонический;
- открыть Sprint 0 и зафиксировать артефакты контракта `v0.1`.
