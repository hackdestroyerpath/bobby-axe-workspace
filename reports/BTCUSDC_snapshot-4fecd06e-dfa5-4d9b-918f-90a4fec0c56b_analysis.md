# BTCUSDC Analysis Report

- **Snapshot ID:** `snapshot-4fecd06e-dfa5-4d9b-918f-90a4fec0c56b`
- **Correlation ID:** `4fecd06e-dfa5-4d9b-918f-90a4fec0c56b`
- **As of UTC:** `2026-03-22T01:28:23Z`
- **Source:** `Ben_Kim analysis_result_batch`

## Executive Summary

- **Overall signal:** `weak_long_bias`
- **Overall confidence:** `0.54`
- **Final comment:** Тестовый analysis-only mock-analysis сформирован и привязан к `snapshot_id` / `correlation_id`.

**Короткий вывод:**
По BTCUSDC наблюдается слабый перевес в long-сценарий, но без сильного подтверждения. Наиболее рабочим выглядит trend-following на `5m`, при этом breakout требует подтверждения объёмом, а mean reversion остаётся слабым и локальным сценарием.

---

## Strategy Overview

| Strategy | 1m | 5m | 60m | Avg confidence |
|---|---|---|---|---:|
| trend_following | weak_long | long_bias | neutral_to_long | 0.56 |
| mean_reversion | scalp_revert | weak_revert | no_clear_edge | 0.48 |
| breakout | watch_breakout | conditional_breakout_long | neutral | 0.49 |

---

## 1. Trend Following

### 1m
- **Signal:** `weak_long`
- **Confidence:** `0.54`
- **Conclusion:** краткосрочный импульс умеренно положительный, но шум высокий

### 5m
- **Signal:** `long_bias`
- **Confidence:** `0.58`
- **Conclusion:** локальный тренд сохраняет слабый восходящий уклон

### 60m
- **Signal:** `neutral_to_long`
- **Confidence:** `0.55`
- **Conclusion:** старший контекст нейтрально-позитивный без сильного подтверждения

**Итог по стратегии:**
Trend-following сейчас выглядит сильнее остальных сценариев, но сигнал остаётся умеренным. Это не агрессивный long, а скорее осторожный перевес в пользу восходящего движения.

---

## 2. Mean Reversion

### 1m
- **Signal:** `scalp_revert`
- **Confidence:** `0.51`
- **Conclusion:** вероятен краткий откат после локального импульса

### 5m
- **Signal:** `weak_revert`
- **Confidence:** `0.49`
- **Conclusion:** возврат к среднему возможен, но edge ограничен

### 60m
- **Signal:** `no_clear_edge`
- **Confidence:** `0.44`
- **Conclusion:** на старшем таймфрейме выраженного reversion-сигнала нет

**Итог по стратегии:**
Откатный сценарий допустим только локально и не даёт сильного преимущества. Использовать его можно лишь как дополнительную тактическую гипотезу, а не как основной сценарий.

---

## 3. Breakout

### 1m
- **Signal:** `watch_breakout`
- **Confidence:** `0.47`
- **Conclusion:** риск ложного пробоя высокий, нужен фильтр подтверждения

### 5m
- **Signal:** `conditional_breakout_long`
- **Confidence:** `0.54`
- **Conclusion:** пробойный сценарий допустим только при подтверждении объёмом

### 60m
- **Signal:** `neutral`
- **Confidence:** `0.46`
- **Conclusion:** подтверждения для старшего breakout-сценария недостаточно

**Итог по стратегии:**
Breakout остаётся наблюдаемым сценарием, но не подтверждённым. Его можно рассматривать только при наличии дополнительного подтверждения, в первую очередь по объёму.

---

## Final Editorial Conclusion

Ben_Kim по BTCUSDC даёт **слабый long bias** без сильной уверенности. Наиболее качественно выглядит **trend-following**, особенно на `5m`, где сохраняется слабый восходящий уклон. **Mean reversion** выглядит ограниченно и локально, а **breakout** допустим только при подтверждении объёмом. Общая интерпретация — рынок скорее склоняется вверх, но пока не даёт основания для сильного направленного вывода.

---

## Data/Visualization Note

В текущем snapshot был доступен `analysis_result`, но не было полноценного свечного/таймсерийного массива от Jack. Поэтому этот отчёт собран в Markdown как аналитический breakdown по стратегиям.

Когда Jack передаст массив свечей / тиков, в Markdown-отчёт можно будет добавлять:
- графики цены
- графики объёма
- свечные секции
- визуальные summary-блоки
- ссылки на связанные артефакты
