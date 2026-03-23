# COMMON_TICK_READ_SPEC

## Назначение

Этот документ фиксирует единые правила чтения тиков для всех потребителей, которые работают с историей сделок.

## Нормализованный вход

Любой тик-рид должен принимать и явно фиксировать следующие входы:

- `symbol`
- `timeframe_target`
- `from`
- `to`
- `source`

### Семантика входов

- `symbol` — инструмент, для которого читаются сделки.
- `timeframe_target` — целевой таймфрейм downstream-расчёта; сам запрос тиков не агрегирует данные, но этот параметр должен быть зафиксирован на уровне вызывающего контура.
- `from` — левая граница окна чтения в UTC.
- `to` — правая граница окна чтения в UTC.
- `source` — источник тиков.

## Источник данных

Чтение делается **только** из таблицы `collector_v2.tick_trade`.

Другие таблицы, materialized views, локальные кеши или производные наборы не считаются каноническим источником для tick-read.

## Обязательные фильтры

Канонический read-path обязан включать:

- `symbol = :symbol`
- `source = :source`
- `event_time_utc >= :from`
- `event_time_utc <= :to`

Границы окна являются **inclusive** с обеих сторон.

Это означает:

- сделка с `event_time_utc == from` должна входить в результат;
- сделка с `event_time_utc == to` должна входить в результат.

## Канонический порядок для расчётов

Для любых расчётов, ресемплинга, дедупликации, candle-build, feature engineering и downstream-аналитики канонический порядок строк такой:

```sql
ORDER BY event_time_utc ASC, trade_id ASC
```

Правило обязательно даже тогда, когда сервер или промежуточный API отдают страницы в другом порядке ради pagination.

## Pagination rules для `/ticks`

Эндпоинт `/ticks` может отдавать данные страницами, если окно больше `limit`.

### Серверный порядок страницы

Чтобы pagination была стабильной, серверная страница должна строиться в порядке:

```sql
ORDER BY event_time_utc DESC, trade_id DESC
```

Причина: так можно последовательно читать «назад по времени» и получать детерминированный cursor boundary даже когда у нескольких сделок одинаковый `event_time_utc`.

### Stable tie-break

Если у нескольких строк одинаковый `event_time_utc`, вторичным ключом сортировки всегда служит `trade_id`.

Без `trade_id` pagination по окнам не считается стабильной.

### Cursor rule

Для чтения следующей страницы сервер должен использовать последний элемент предыдущей страницы как cursor и применять строгий фильтр:

```sql
AND (event_time_utc, trade_id) < (:cursor_event_time_utc, :cursor_trade_id)
```

Это правило:

- не меняет исходные inclusive window boundaries;
- не дублирует уже отданную запись на следующей странице;
- сохраняет детерминированный проход по окну.

### Inclusive window boundaries и pagination

Inclusive-границы окна (`>= from`, `<= to`) применяются одинаково для **первой** и **всех последующих** страниц.

Pagination не должна ослаблять или ужесточать базовое окно.
Дополнительный cursor-фильтр работает только как отсечение уже прочитанного хвоста внутри того же окна.

### Клиентская нормализация

После получения всех страниц клиент обязан нормализовать итоговую последовательность в canonical ascending order:

```sql
ORDER BY event_time_utc ASC, trade_id ASC
```

Именно этот порядок считается правильным для расчётов и любых downstream-процедур.

## Canonical SQL template

```sql
SELECT
    source,
    symbol,
    trade_id,
    event_time_utc,
    price,
    quantity,
    side,
    ingested_at_utc
FROM collector_v2.tick_trade
WHERE symbol = :symbol
  AND source = :source
  AND event_time_utc >= :from
  AND event_time_utc <= :to
ORDER BY event_time_utc ASC, trade_id ASC;
```

## Canonical SQL template для server-side pagination `/ticks`

Первая страница:

```sql
SELECT
    source,
    symbol,
    trade_id,
    event_time_utc,
    price,
    quantity,
    side,
    ingested_at_utc
FROM collector_v2.tick_trade
WHERE symbol = :symbol
  AND source = :source
  AND event_time_utc >= :from
  AND event_time_utc <= :to
ORDER BY event_time_utc DESC, trade_id DESC
LIMIT :limit;
```

Следующая страница:

```sql
SELECT
    source,
    symbol,
    trade_id,
    event_time_utc,
    price,
    quantity,
    side,
    ingested_at_utc
FROM collector_v2.tick_trade
WHERE symbol = :symbol
  AND source = :source
  AND event_time_utc >= :from
  AND event_time_utc <= :to
  AND (event_time_utc, trade_id) < (:cursor_event_time_utc, :cursor_trade_id)
ORDER BY event_time_utc DESC, trade_id DESC
LIMIT :limit;
```

## Summary rule

Если есть расхождение между удобством API и корректностью расчёта, приоритет такой:

1. окно всегда inclusive: `>= from`, `<= to`;
2. pagination всегда стабильна через `(event_time_utc, trade_id)`;
3. финальный расчёт всегда идёт по `ORDER BY event_time_utc ASC, trade_id ASC`.
