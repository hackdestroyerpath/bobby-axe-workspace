# Runbook: quality checks для рыночных данных

## Цель
Этот runbook фиксирует минимальный набор проверок качества данных, которые `Jack` обязан выполнять перед тем, как считать окно пригодным для downstream-пайплайна.

## Когда выполнять проверки
Quality checks обязательны:
- при первичном запуске `Data_collector`;
- после подключения нового источника данных;
- после любого recovery/replay/backfill;
- перед публикацией `second_bars_ready` для ранее проблемного окна;
- при любом алерте по lag, duplicates или failed writes.

## Check 1. Разрешённый universe и symbol hygiene
### Цель
Убедиться, что в pipeline попадают только разрешённые тикеры.

### Проверка
- Каждый `trade_tick.symbol` должен входить в operational universe:
  - `BTCUSDC`
  - `ETHUSDC`
  - `SOLUSDC`
  - `XRPUSDC`
  - `ADAUSDC`
- Любой тикер вне списка должен быть отклонён с ошибкой `SYMBOL_NOT_ALLOWED`.
- Символ должен быть нормализован в uppercase canonical form.

### Fail criteria
- в raw layer появилась запись по неразрешённому символу;
- символ не приводится к канонической форме;
- allowlist отличается между intake и quality checker.

## Check 2. Schema validation входных сделок
### Цель
Проверить соответствие `trade_tick` контракту.

### Проверка
Каждая запись обязана содержать:
- `event_type`
- `source`
- `symbol`
- `trade_id`
- `price`
- `quantity`
- `side`
- `trade_ts`
- `ingested_at`

### Fail criteria
- отсутствует обязательное поле;
- `trade_ts` или `ingested_at` невалидны как UTC timestamp;
- `price <= 0` или `quantity <= 0`;
- `side` не равен `buy` или `sell`.

## Check 3. Health live trades потока
### Цель
Формально определить, что live trades поток здоров.

### Метрики и пороги
- `lag`: `P95 <= 3s`, критично при `> 10s` более 60 секунд.
- `trades/sec`: не ниже 20% от 15-минутного baseline по активному символу.
- `symbols_online`: должны быть online все символы из allowlist в течение последних 30 секунд.
- `duplicate_rate`: норма `< 0.5%`, warning `0.5% - 2%`, critical `>= 2%`.
- `failed_writes`: норма `0`; любое устойчивое ненулевое значение — инцидент.

### Решение
Поток live trades считается `healthy`, только если **все** перечисленные метрики находятся в зелёной зоне.

## Check 4. Deduplication integrity
### Цель
Подтвердить, что replay/restart не приводит к дублированию.

### Проверка
- Для raw trades uniqueness должна обеспечиваться по `source + symbol + trade_id`.
- При отсутствии надёжного `trade_id` используется fallback-ключ.
- Повторная поставка того же окна не должна увеличивать число уникальных сделок сверх ожидаемого.

### Fail criteria
- одинаковый trade проходит как два уникальных raw-события;
- после replay вырос `trade_count`, хотя business window не изменился;
- duplicate rate растёт скачком после restart.

## Check 5. Completeness of `second_bar`
### Цель
Подтвердить, что секундный слой полон и детерминирован.

### Проверка
Для каждого закрытого окна и символа:
- `second_count_materialized == second_count_expected`;
- нет исторических секунд со статусом `partial`;
- `open/high/low/close/volume/trade_count` воспроизводимы при повторной пересборке;
- `1m`, `5m`, `60m` пересчитываются только из `second_bar`.

### Fail criteria
- есть необъяснимый пропуск секунды;
- повторная сборка даёт другой OHLC;
- старший таймфрейм не совпадает с секундным источником истины.

## Check 6. Gap detection и recovery readiness
### Цель
Быстро определить, что окно должно быть отправлено в recovery.

### Trigger conditions
- закрытое окно имеет меньше секунд, чем ожидается;
- между raw и curated count есть необъяснимое расхождение;
- символ был offline, но рынок оставался активным;
- backlog retries или failed writes совпадает по времени с дырой в данных.

### Действие
- Пометить окно как `AGGREGATION_GAP`.
- Заблокировать downstream-публикацию по этому окну.
- Передать инцидент в recovery runbook.

## Check 7. Storage write reliability
### Цель
Убедиться, что ни raw, ни curated слой не теряют данные на записи.

### Проверка
Мониторить отдельно:
- `failed_writes_raw`
- `failed_writes_curated`
- размер retry queue
- размер dead-letter queue

### Fail criteria
- `failed_writes_raw > 0` более 30 секунд;
- `failed_writes_curated > 0` более 30 секунд;
- retry queue растёт и не дренируется;
- есть неподтверждённые batch после restart.

## Итоговый quality gate
Окно считается пригодным для downstream только если:
1. символ входит в allowlist;
2. schema validation проходит;
3. live health metrics зелёные;
4. duplicate rate под контролем;
5. `second_bar` complete и детерминирован;
6. `failed_writes = 0`;
7. активных gap по окну нет.

## Рекомендуемый статус-репорт
```text
[Data Quality Check]
Source: <source_name>
Symbol: <symbol>
Window: <window_start_utc> -> <window_end_utc>
Result: <pass|fail>
Metrics:
- lag_p95: <value>
- trades_per_sec: <value>
- symbols_online: <value>
- duplicate_rate: <value>
- failed_writes: <value>
Checks:
- symbol_allowlist: <pass/fail>
- schema_validation: <pass/fail>
- deduplication: <pass/fail>
- second_bar_completeness: <pass/fail>
- recovery_needed: <yes/no>
```
