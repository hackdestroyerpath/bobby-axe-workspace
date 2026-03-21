# Runbook: Ben_Kim Request Flow

## Status
Accepted.

## Purpose
Операционный runbook для выполнения одного запроса `Ben_Kim` в live/snapshot-режиме.

Используется, когда:
- приходит пользовательский запрос на анализ;
- `Jack` передаёт feature-пакеты;
- нужно гарантированно получить полный набор `analysis_result` и вернуть его обратно в storage.

---

## 1. Trigger

Запрос на анализ считается начатым, когда существует:
- `correlation_id`
- список тикеров
- фиксированный набор таймфреймов `1m/5m/60m`
- список активных стратегий
- согласованное окно данных

---

## 2. Inputs required before analysis starts

Перед стартом `Ben_Kim` должен иметь:
- `symbol` или список `symbols`
- `observed_at`
- `source_window.from`
- `source_window.to`
- feature-пакеты от `Jack` по каждому `symbol × frame`
- runtime-конфиг активных стратегий

Если хотя бы одного обязательного входа нет — анализ не должен маскироваться под готовый.

---

## 3. Step-by-step execution

### Step 1. Validate request scope
Проверить:
- тикеры валидны;
- таймфреймы только `1m`, `5m`, `60m`;
- есть `correlation_id`;
- окно данных задано в UTC.

### Step 2. Validate input packets
Для каждого `symbol × frame` проверить наличие feature-пакета.

### Step 3. Load active strategies
Загрузить runtime-список стратегий из:
- `config/ben_kim_runtime_strategies.yaml`

### Step 4. Compute expected count
Посчитать:
- `expected_per_ticker = active_strategies × 3`
- `expected_total = tickers × active_strategies × 3`

### Step 5. Build results
Для каждого тикера:
- пройти `1m -> 5m -> 60m`
- внутри каждого таймфрейма пройти по всем стратегиям
- сформировать отдельный `analysis_result`

### Step 6. Validate results
Проверить:
- нет пропущенных комбинаций;
- `status/result_code` согласованы;
- заполнены обязательные поля;
- conclusion короткий и конкретный.

### Step 7. Persist batch
Передать batch `Jack` и/или записать его в storage.

### Step 8. Confirm completion
Запрос считается завершённым только после подтверждения записи batch в storage.

---

## 4. Failure handling

### Case A. Missing feature group
Действие:
- вернуть `partial`
- `result_code=insufficient_data`
- явно указать, какого блока признаков не хватает.

### Case B. Strategy not implemented yet
Действие:
- вернуть `partial`
- `result_code=skipped`
- указать, что стратегия зарезервирована и пока не реализована.

### Case C. Storage write failed
Действие:
- не считать запрос завершённым;
- зафиксировать ошибку записи;
- повторить writeback идемпотентно.

### Case D. Invalid timeframe
Действие:
- отклонить конкретный элемент;
- не создавать неканонический таймфрейм.

---

## 5. Completion criteria

Запрос `Ben_Kim` выполнен корректно, если:
1. по каждому тикеру сформированы результаты для `1m`, `5m`, `60m`;
2. по каждой активной стратегии есть отдельный результат;
3. общее число результатов совпадает с expected count;
4. batch записан в storage;
5. `Jack` может прочитать результаты обратно.

---

## 6. Minimal operator checklist

Перед завершением проверить:
- [ ] feature-пакеты по всем тикерам получены
- [ ] runtime-стратегии загружены
- [ ] expected count посчитан
- [ ] все комбинации `ticker × frame × strategy` покрыты
- [ ] partial/rejected элементы оформлены формально
- [ ] batch записан в storage
- [ ] результат доступен `Jack`
