# Runbook: recovery для `Jack / Data_collector`

## Цель
Этот runbook описывает, что делать при gap в данных, как переподнимать ingestion без потери консистентности и как `Jack` должен эскалировать инциденты `Bobby Axe`.

## Типовые симптомы инцидента
- `lag` устойчиво растёт.
- `trades/sec` резко падает или становится нулевым.
- Один или несколько символов исчезают из `symbols_online`.
- Растёт `duplicate_rate`.
- Появляются `failed_writes` в raw или curated layer.
- В `second_bar` обнаружены пропуски секунд, неожиданный `partial` или неверный `trade_count`.

## Что делать при gap в данных
Под gap понимается пропуск событий или секундного окна, из-за которого historical window больше нельзя считать complete.

### Как определить gap
Gap фиксируется, если выполняется хотя бы одно из условий:
- для символа отсутствуют raw trades в окне, где источник подтверждает активность;
- `second_count_materialized < second_count_expected` для уже закрытого окна;
- есть разрыв между `max(trade_ts)` предыдущего окна и `min(trade_ts)` следующего окна, который не объясняется отсутствием сделок на рынке;
- downstream quality check помечает окно как `AGGREGATION_GAP`.

### Немедленные действия
1. Зафиксировать `symbol`, `source`, `window_start_utc`, `window_end_utc`.
2. Остановить публикацию downstream-событий для повреждённого окна.
3. Перевести затронутый символ в статус `degraded`.
4. Проверить, находится ли проблема на стороне intake, raw storage или rebuild `second_bar`.
5. Если причина не ясна в течение 5 минут, создать escalation для `Bobby Axe`.

### Recovery-процедура по gap
1. Определить минимальное безопасное окно переигрывания:
   - начать с последнего подтверждённого корректного `second_bar` до gap;
   - закончить первым полностью здоровым окном после gap.
2. Выполнить backfill/replay raw trades для этого окна из канонического источника.
3. Записать raw trades через idempotent upsert.
4. Очистить или пометить как stale только производные curated-артефакты для конкретного окна.
5. Полностью пересобрать `second_bar`, затем `1m`, `5m`, `60m` **только из raw/second layers**, а не частичным patch-обновлением.
6. Повторно запустить quality checks:
   - полнота секунд
   - отсутствие duplicate inflation
   - детерминированность OHLC
7. Только после успешной проверки снова публиковать `second_bars_ready` и разблокировать downstream.

## Как переподнять ingestion без потери консистентности
### Принцип
Любой restart должен быть безопасным за счёт идемпотентности raw ingest и детерминированного rebuild curated-слоя.

### Безопасная последовательность restart
1. Зафиксировать текущий инцидент и затронутое окно.
2. Остановить live-consumer так, чтобы новые сообщения не коммитились частично.
3. Дождаться завершения in-flight batch либо пометить batch как aborted.
4. Сохранить checkpoint:
   - последний подтверждённый `trade_ts`
   - последний `raw_commit_ref`
   - затронутые `symbol`
5. Проверить состояние raw layer:
   - нет ли незавершённых write batches;
   - нет ли накопленных retry/dead-letter записей.
6. Перезапустить intake/consumer.
7. Считать все события после checkpoint как потенциально повторно доставленные и пропускать их через тот же dedup-key.
8. Выполнить replay короткого overlap-окна перед checkpoint, например `30-120` секунд, чтобы безопасно закрыть пограничные записи.
9. Повторно пересобрать `second_bar` для overlap-окна.
10. Подтвердить, что post-restart метрики вернулись в норму, и только после этого снять статус инцидента.

### Что нельзя делать
- Нельзя вручную дозаписывать отдельные curated-строки без пересборки окна.
- Нельзя удалять raw trades, если ещё не зафиксирован диапазон восстановления.
- Нельзя публиковать downstream `ready`, пока хотя бы один quality check остаётся красным.
- Нельзя менять allowlist universe посреди recovery без отдельного решения `Bobby Axe`.

## Проверки после восстановления
После recovery `Jack` обязан подтвердить:
- `lag` вернулся в целевой диапазон;
- `trades/sec` по затронутым символам соответствует baseline;
- `symbols_online` снова покрывает весь expected universe;
- `duplicate_rate` не вырос после replay;
- `failed_writes = 0` на устойчивом интервале наблюдения;
- gap закрыт и `second_bar`/`1m`/`5m`/`60m` детерминированны.

## Как Jack должен эскалировать проблему Bobby Axe
### Когда эскалировать немедленно
`Jack` обязан эскалировать инцидент `Bobby Axe` сразу, если:
- источник недоступен более 5 минут;
- потерян хотя бы один символ из operational universe более чем на 2 минуты;
- gap затрагивает уже опубликованное downstream окно;
- `failed_writes` указывают на возможное повреждение raw или curated storage;
- restart/replay не устранил проблему с первой попытки;
- есть риск, что downstream строится на недостоверных данных.

### Формат эскалации
```text
[Bobby Axe Escalation]
Stage: jack
Severity: <high|critical>
Source: <source_name>
Symbols: <comma-separated symbols>
Window: <window_start_utc> -> <window_end_utc>
Problem:
- <краткое описание сбоя>
Impact:
- <что заблокировано>
Actions already taken:
- <restart/replay/backfill/checks>
Requested decision:
- <restart downstream|freeze pipeline|approve extended backfill|human review>
ETA for next update:
- <timestamp_utc>
```

### Ожидаемое поведение после эскалации
- `Jack` продолжает техническое восстановление, если это безопасно.
- `Bobby Axe` решает, останавливать ли downstream pipeline, переводить ли систему в safe mode и требуется ли human escalation.
- Каждый следующий апдейт должен содержать новый статус метрик и точное окно, которое остаётся под вопросом.
