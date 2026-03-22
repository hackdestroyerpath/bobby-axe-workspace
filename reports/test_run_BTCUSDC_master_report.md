# BTCUSDC — Test Master Report

- **Format:** test master report
- **Symbol:** `BTCUSDC`
- **Snapshot ID:** `snapshot-4fecd06e-dfa5-4d9b-918f-90a4fec0c56b`
- **Correlation ID:** `4fecd06e-dfa5-4d9b-918f-90a4fec0c56b`
- **As of UTC:** `2026-03-22T01:28:23Z`
- **Source:** `Ben_Kim analysis_result_batch`

---

## 1. Executive Summary

По BTCUSDC в текущем snapshot просматривается **слабый long bias** без сильного подтверждения. Общая картина остаётся умеренно-позитивной, но не агрессивной: рынок скорее склоняется в сторону продолжения роста, чем разворота, однако сигнал пока недостаточно сильный, чтобы трактовать его как уверенный направленный импульс.

---

## 2. Summary Table

| Field | Value |
|---|---|
| Symbol | `BTCUSDC` |
| Overall signal | `weak_long_bias` |
| Overall confidence | `0.54` |
| Producer | `Ben_Kim` |

---

## 3. Strategy Matrix

| Strategy | 1m Signal | 1m Conf | 5m Signal | 5m Conf | 60m Signal | 60m Conf |
|---|---|---:|---|---:|---|---:|
| trend_following | `weak_long` | 0.54 | `long_bias` | 0.58 | `neutral_to_long` | 0.55 |
| mean_reversion | `scalp_revert` | 0.51 | `weak_revert` | 0.49 | `no_clear_edge` | 0.44 |
| breakout | `watch_breakout` | 0.47 | `conditional_breakout_long` | 0.54 | `neutral` | 0.46 |

---

## 4. Strategy Commentary

### Trend Following
Trend-following выглядит сильнее остальных сценариев. На `5m` сохраняется слабый восходящий уклон, а на `60m` старший контекст остаётся нейтрально-позитивным. Это делает трендовую стратегию базовым рабочим сценарием для текущего snapshot.

### Mean Reversion
Mean reversion не показывает выраженного преимущества. На младших таймфреймах возможен краткий откат после локального импульса, однако на более широком контексте сигнал на возврат к среднему остаётся слабым.

### Breakout
Breakout-сценарий допустим, но только условно. На `1m` сохраняется риск ложного пробоя, а на `5m` для подтверждения требуется объём. Без дополнительного подтверждения этот сценарий стоит считать наблюдаемым, а не основным.

---

## 5. Ranking by Average Confidence

| Rank | Strategy | Avg confidence |
|---:|---|---:|
| 1 | trend_following | 0.56 |
| 2 | breakout | 0.49 |
| 3 | mean_reversion | 0.48 |

---

## 6. Final Editorial Conclusion

Ben_Kim по BTCUSDC даёт **умеренно-позитивный, но слабый long bias**. Наиболее качественно выглядит сценарий **trend-following**, особенно в зоне `5m`, где тренд сохраняет восходящий уклон. **Mean reversion** уместен лишь как локальная тактическая гипотеза, а **breakout** требует внешнего подтверждения объёмом. В целом рынок выглядит скорее склонным вверх, чем нейтральным вниз, но текущая сила сигнала остаётся ограниченной.

---

## 7. Export Notes

- **Primary delivery format:** Markdown
- **Export subagent target:** PDF on demand
- **Current limitation:** в snapshot нет полноценного свечного / tick-массива от Jack, поэтому этот тест собран как текстово-табличный analytical report.
