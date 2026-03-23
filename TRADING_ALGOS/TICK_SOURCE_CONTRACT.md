# Tick Source Contract

## Status
Этот документ — единственный source-of-truth для входных тиков для всех документов и машин в `TRADING_ALGOS`. Любые описания входа в других файлах должны ссылаться на этот контракт, а не пересказывать его своими словами.

## Canonical source
Все trading-машины читают входные тики только из таблицы `collector_v2.tick_trade`.

## Required fields
| Field | Requirement |
| --- | --- |
| `source` | Обязательное поле входного тика. |
| `symbol` | Обязательное поле входного тика. |
| `trade_id` | Обязательное поле входного тика. |
| `event_time_utc` | Обязательное поле входного тика. |
| `price` | Обязательное поле входного тика. |
| `quantity` | Обязательное поле входного тика. |
| `side` | Обязательное поле входного тика. |
| `ingested_at_utc` | Обязательное поле входного тика. |

## Hard rules
- `side` берётся напрямую из `collector_v2.tick_trade` без proxy-логики, without inference и без synthetic side reconstruction.
- Все timestamps трактуются только как UTC. Это относится как минимум к `event_time_utc` и `ingested_at_utc`, а также к любым window boundaries, derived intervals и operational checks, которые строятся поверх этих полей.

## Operational constraint: retention
Retention входных тиков определяется настройкой `RETENTION_DAYS`. Следствие: доступная глубина истории — это operational constraint, который надо проверять по фактическим данным перед расчётами, а не предполагать заранее.

## Procedure: verify available depth
Перед запуском окна расчёта нужно отдельно проверить доступную глубину данных по факту через `MIN(event_time_utc)`, `MAX(event_time_utc)` и `COUNT(*)`.

Пример проверки:

```sql
SELECT
  MIN(event_time_utc) AS min_event_time_utc,
  MAX(event_time_utc) AS max_event_time_utc,
  COUNT(*) AS tick_count
FROM collector_v2.tick_trade
WHERE symbol = :symbol;
```

## Usage rule
- `TRADING_ALGOS/README.md` и `TRADING_ALGOS/TODO.md` должны ссылаться на этот контракт как на входной source-of-truth.
- Все 12 machine templates в `TRADING_ALGOS` должны ссылаться на этот контракт в разделе входа и не дублировать его содержание локальными формулировками.
