# TO_DO_LIST.md

Ниже — полный структурированный список того, что осталось доделать по Bobby. Идея простая: ты берешь кодовую доработку на себя, а потом Bobby подтягивает изменения и доводит финальную версию уже поверх твоего апдейта.

---

# 1. Главная цель

Довести Bobby до состояния:
- paper runtime работает автономно
- стратегия сама выбирает направление сетки
- используются Binance USDS-M ограничения как source of truth
- есть корректный state/risk contract
- можно безопасно перейти к testnet/live-ready архитектуре

Важно:
- текущий фокус — **paper-first**, не live-first
- live-деньги пока не включать
- все решения должны быть совместимы с будущим Binance execution path

---

# 2. Что уже есть

Сейчас уже собрано:
- grid decision core
- paper simulator
- multi-symbol scan
- summary output
- readiness output
- heartbeat formatter
- paper cycle
- export workflow
- частичная Binance integration база (`exchangeInfo`, symbol filters)
- directional TP/SL fields
- neutral-grid removal basis

Это не нужно переписывать с нуля. Это нужно **доделать и стабилизировать**.

---

# 3. Что нужно сделать в первую очередь

## 3.1. Повторяющийся runtime loop

Нужно сделать нормальный repeating loop runner, который не зависит от ручной подачи `multi_snapshot.json`.

### Что должно быть:
1. Получение market data по символам автоматически.
2. Получение:
   - candles
   - bid/ask
   - mark price
3. Запуск цикла по интервалу.
4. Запись state после каждого цикла.
5. Запись короткого loop-status.
6. Возможность безопасно остановить loop.

### Что желательно реализовать:
- отдельный runtime mode:
  - `paper_loop.py --live`
  - или аналогичный стабильный режим
- файл статуса, например:
  - `loop_status.json`
- файл stop-сигнала, например:
  - `STOP_BOBBY`
  - либо `stop.flag`

### Что loop должен сохранять:
- last_cycle_time
- last_summary
- last_readiness
- last_error
- current_mode
- iteration_count

---

## 3.2. Реальный market-data path через Binance

Нужно, чтобы loop не жил на sample snapshot'ах.

### Сделать:
1. Нормальный market data adapter для Binance USDS-M.
2. Унифицированный сбор snapshot для каждого символа.
3. Источник данных должен включать:
   - свечи
   - bid
   - ask
   - last price
   - mark price
4. Результат должен приходить в существующий формат, совместимый с `agent.py`.

### Важно:
- не ломать текущий contract input payload
- лучше сделать adapter, который готовит данные в уже существующую структуру

---

# 4. Стратегия: что именно доработать

## 4.1. Направление — это главный edge

Алгоритм должен максимально ясно отвечать на вопрос:
- ставить `LONG_GRID`
- ставить `SHORT_GRID`
- ставить `NEUTRAL_GRID`
- не ставить ничего

### Цель:
не просто “сетка всегда”, а **правильный выбор направления**.

### Нужно проверить и усилить:
- trend detection
- pullback logic
- rejection bad structure
- edge threshold before deployment

---

## 4.2. Directional grids

Для directional grid логика должна быть такой:
- выбрал направление
- поставил grid
- поставил `TP`
- поставил `SL`
- дальше grid не надо вручную сопровождать

### Нужно проверить кодово:
1. TP действительно закрывает/снимает directional grid.
2. SL действительно закрывает/снимает directional grid.
3. После TP/SL корректно очищается:
   - active grid
   - inventory
   - runner summary
   - state
4. После завершения directional grid можно корректно re-arm на том же символе.

---

## 4.3. Neutral grids

Neutral grids использовать осторожно.

### Нужно сделать:
1. Явную политику снятия neutral grid.
2. Не позволять neutral grid жить бесконечно.
3. Удалять neutral grid:
   - по числу баров
   - по уходу цены за допустимый диапазон
   - по смене структуры рынка
4. После снятия neutral grid — чистить state.

### Критично:
neutral grid нельзя оставлять “забытой”.

---

## 4.4. Количество уровней сетки

Оператор зафиксировал логику:
- нормальный рабочий диапазон: **1–5 уровней**
- абсолютный потолок: **7**

### Нужно сделать:
1. Убедиться, что стратегия по умолчанию живет в 1–5.
2. Проверить, где код может случайно раздувать количество уровней.
3. Не строить grid, если economics makes no sense.
4. Если economics не позволяет 3–5 уровней, алгоритм должен:
   - либо уменьшить уровни
   - либо пропустить символ
   - либо явно зафиксировать blocker reason

---

# 5. Economics / Symbol policy

Это сейчас один из главных реальных узких мест.

## 5.1. Проблема

При депозите около `30 USD` некоторые символы, особенно `BTCUSDC`, могут не проходить по экономике:
- min notional
- step size
- число уровней
- доступный notional under leverage/risk limits

### Значит нужно сделать явную политику:
не “попробовали — не получилось”, а **понятное решение в коде**.

---

## 5.2. Что нужно реализовать

### Для каждого символа алгоритм должен уметь определить:
1. Можно ли строить сетку вообще.
2. Сколько уровней реально допустимо.
3. Какой минимальный notional нужен на уровень.
4. Что является blocker:
   - exchange filters
   - account economics
   - risk constraints
   - regime mismatch

### Если символ не проходит:
алгоритм должен выбрать одно из действий:
- `skip_symbol`
- `reduce_levels`
- `reduce_allocation`
- `prefer_other_symbol`

### Особо по BTCUSDC:
нужно явно решить в коде:
- когда BTCUSDC торгуется
- когда пропускается
- когда он доступен только при особой экономике

---

## 5.3. ExchangeInfo final binding

Нужно окончательно закрепить использование Binance `exchangeInfo`.

### Проверить и довести:
- `tickSize`
- `stepSize`
- `minNotional`
- `orderTypes`
- `timeInForce`
- актуальные symbol filters

### Важно:
- не использовать hardcoded `pricePrecision` как `tickSize`
- не использовать hardcoded `quantityPrecision` как `stepSize`
- использовать live symbol filters как source of truth

---

# 6. Risk / state contract

Это обязательно надо дочистить, иначе runtime будет врать.

## 6.1. Что должно быть гарантировано

После каждого из событий состояние должно быть строго корректным:
- invalidation
- TP exit
- SL exit
- neutral removal
- risk lock
- re-arm after full exit

## 6.2. Что нужно проверить

### После invalidation:
- active grid cleared
- inventory cleaned if required
- runner summary updated
- readiness updated

### После TP:
- state consistent
- grid removed
- inventory consistent
- realized pnl updated

### После SL:
- state consistent
- loss streak updated
- lock logic re-evaluated

### После neutral removal:
- neutral grid not left in active state
- no stale active_grids record
- no stale summary

### После lock:
- runner summary must reflect lock
- no stale deployment recommendation

---

## 6.3. Тесты

Нужно добавить/расширить тесты минимум на:
1. invalidation -> clear state
2. TP -> clear state
3. SL -> clear state
4. neutral removal -> clear state
5. lock -> summary + state contract
6. same-symbol re-arm after prior full close

---

# 7. Paper runtime stabilization

Когда loop будет собран, нужно не просто один раз запустить, а проверить серией прогонов.

## Что проверить:
1. state drift
2. stale grids
3. wrong inventory carry
4. wrong symbol carry
5. false locks
6. wrong readiness
7. summary consistency
8. repeated-cycle stability

### Практически:
сделать серию repeated runs и логировать:
- cycle result
- summary
- readiness
- state changes
- detected blockers

---

# 8. Что можно сделать архитектурно аккуратно

Если хочешь ускорить и не ломать код:

## Рекомендуемая структура
- `binance_exchange.py` — live exchange info + market data helpers
- `market_data.py` — normalized snapshot structures
- `agent.py` — evaluation orchestration
- `risk.py` — sizing / filters / economics
- `grid_strategy.py` — regime + deployment decision
- `simulator.py` — fill simulation / tp / sl / neutral removal
- `runner.py` — scan + summary + readiness
- `paper_cycle.py` — one-shot paper cycle
- `paper_loop.py` — repeating runtime loop

### Смысл:
не смешивать everything in one file

---

# 9. Что не нужно делать сейчас

Пока НЕ надо:
- сразу включать реальные деньги
- сразу включать production execution
- прыгать в сложный live order management
- делать full bot orchestration beyond paper runtime

Сейчас сначала надо сделать:
- стабильный paper runtime
- стабильный economics policy
- стабильный state contract

---

# 10. После твоих правок

Когда ты допишешь:
1. Bobby подтягивает обновления из GitHub.
2. Сверяет diff.
3. Обновляет memory/status/tasks.
4. Делает final stabilization.
5. Дальше уже можно переходить к:
   - Binance testnet execution path
   - live-ready connector architecture
   - потом только реальные деньги

---

# 11. Самый короткий practical order of execution

Если делать вообще по порядку, то вот так:

1. Доделать `paper_loop.py`
2. Подключить живой Binance market-data path
3. Сделать loop-status + stop flag
4. Дочистить TP/SL/neutral removal state cleanup
5. Дочистить risk/state contract
6. Доделать economics policy under 30 USD
7. Сделать явную policy по BTCUSDC
8. Прогнать repeated paper cycles
9. Проверить summary/readiness consistency
10. Вернуть Bobby на final integration pass

---

# 12. Итог

Если по-простому:

Тебе нужно доделать не “всю стратегию с нуля”, а вот эти хвосты:
- автономный runtime loop
- реальный market-data path
- economics policy
- финальный state/risk contract
- стабильность repeated paper runtime

После этого Bobby уже сможет быстро добить финальный слой и двигаться к testnet/live-ready архитектуре.
