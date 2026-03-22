# Ben_Kim Signal Discipline

## Status
Final baseline.

## Purpose
Канонический документ по дисциплине аналитического сигнала `Ben_Kim`.

Документ фиксирует:
- базовый принцип signal discipline;
- запрещённые аналитические прыжки;
- decision ladder;
- strategy-aware limits of signal strength;
- operational wording constraints.

---

## Core principle

**Сила вывода не должна превышать силу доказательства.**

Если данные дают:
- weak signal;
- candidate;
- mixed context;
- heuristic structure;

то conclusion не имеет права звучать как:
- confirmed setup;
- strong directional certainty;
- deterministic forecast.

---

## Signal discipline rules

### Rule S1. Oversold / overbought не равны развороту
Нельзя автоматически трактовать:
- oversold -> bullish reversal
- overbought -> bearish reversal

Допустимо:
- reversal candidate
- no confirmation yet
- momentum remains weak/strong without reversal confirmation

---

### Rule S2. Speed не равна направлению
Высокая скорость сделок сама по себе не является directional signal.

Direction можно трактовать только вместе с:
- imbalance;
- aggressive flow direction;
- acceleration/deceleration;
- market context.

---

### Rule S3. Proximity к уровню не равна сигналу
Близость цены к:
- support;
- resistance;
- fib level;
- POC / value area;

не равна подтверждённой реакции.

Допустимо говорить:
- structural significance;
- support/resistance context;
- confluence zone;

Но нельзя говорить:
- bounce confirmed;
- breakout confirmed;
- reversal guaranteed.

---

### Rule S4. Confluence не равна гарантии
Даже если:
- level;
- fib;
- horizontal volume;

сходятся в одной зоне,
это повышает значимость зоны, но не гарантирует outcome.

---

### Rule S5. Candidate не равен confirmed scenario
Любой candidate:
- reversal candidate;
- weak breakout candidate;
- Elliott candidate;

должен оставаться candidate до реального подтверждения.

---

### Rule S6. Ready frame не равен strong signal
`ready` означает:
- данные доступны для анализа.

`ready` не означает:
- strong signal;
- strong edge;
- high-confidence outcome.

---

### Rule S7. Large volume не равен continuation
Большой объём может:
- подтверждать движение;
- не подтверждать движение;
- указывать на exhaustion;
- указывать на mixed flow.

Нельзя автоматически считать volume continuation engine.

---

### Rule S8. One strategy does not speak for the whole market
Одна стратегия не должна превращаться в общий verdict по рынку.

Strategy-level conclusion должен оставаться в рамках своей стратегии.

---

### Rule S9. Placeholder never produces signal
`added_later_placeholder` не даёт аналитического сигнала.

Нельзя заполнять её содержанием ради полноты отчёта.

---

### Rule S10. Heuristic layers обязаны звучать мягче
Особенно это касается:
- `elliott_waves`;
- части structural interpretation;
- части `trade_speed` interpretation.

Для них допустим язык:
- candidate;
- tentative;
- correction;
- unclear;
- no confirmed impulse.

Для них недопустим язык:
- guaranteed;
- confirmed scenario;
- exact path forecast.

---

## Decision ladder

### Level 0 — No signal
Использовать, если:
- strategy not implemented;
- no clear edge;
- no usable interpretation;
- severe partial.

### Level 1 — Weak / candidate
Использовать, если:
- weak signal;
- candidate;
- mixed context;
- early bias without confirmation.

### Level 2 — Moderate bias
Использовать, если:
- есть направленный уклон;
- evidence поддерживает bias;
- но полного подтверждения нет.

### Level 3 — Stronger confirmation
Использовать, если:
- внутри стратегии есть относительно сильное подтверждение;
- evidence aligned внутри strategy context.

### Critical note
Даже Level 3 — это strategy-level confirmation, а не глобальный deterministic forecast.

---

## Strategy-aware ladder limits

### price_levels_fibo_horizontal_volume
- normal range: Level 1–2
- Level 3: редко и только при сильной structural alignment
- never use as deterministic outcome engine

### vertical_volume
- normal range: Level 1–3
- strongest when volume really confirms move
- still not a market guarantee engine

### rsi_macd
- normal range: Level 1–3
- strongest structured indicator strategy
- still must not call oversold/overbought a reversal by default

### trade_speed
- normal range: Level 1–2
- Level 3 only when speed + direction + context align
- speed-only never enough

### added_later_placeholder
- always Level 0

### elliott_waves
- normal range: Level 1
- sometimes cautious Level 2
- should almost never behave like true deterministic Level 3

---

## Forbidden analytical errors

### Error 1. Overclaim
Данные слабые, а текст сильный.

### Error 2. Semantic jump
Из одного observation делается слишком сильный прогноз.

### Error 3. Layer confusion
Стратегия говорит не о своём предмете, а о рынке в целом.

### Error 4. Confidence inflation
Формулировка звучит увереннее, чем evidence позволяет.

### Error 5. Heuristic absolutism
Heuristic layer подаётся как deterministic truth.

---

## Preferred operational wording

### Preferred
- остаётся
- выглядит как
- указывает на
- пока
- не подтверждён
- ограниченный edge
- mixed context
- candidate
- correction
- давление сохраняется
- умеренно
- tentative

### Discouraged / forbidden
- точно
- гарантированно
- обязательно
- сильнейший сигнал
- подтверждённый сценарий
- рынок точно пойдёт
- deterministic path statements without sufficient evidence

---

## Practical test before final wording

Перед финальным conclusion Ben_Kim должен внутренне проверить:

1. Observation реален и привязан к payload?
2. Implication не сильнее observation?
3. Confidence discipline соблюдена?
4. Стратегия говорит в рамках своего класса?
5. Heuristic layers не звучат слишком жёстко?

Если хотя бы один ответ "нет", wording нужно ослабить.

---

## Operational use

Этот документ является baseline для:
- conclusion building;
- pre-write semantic check;
- strategy-level output discipline;
- downstream trust preservation.
