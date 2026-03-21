# Ben_Kim Output Batch Spec

## Status
Accepted for implementation alignment with Jack/storage.

## Purpose
Документ фиксирует, как `Ben_Kim` должен собирать и возвращать batch результатов анализа по одному запросу.

Цель:
- чтобы `Jack` мог без двусмысленности принимать batch в storage;
- чтобы каждая комбинация `ticker × frame × strategy` превращалась в отдельный `analysis_result`;
- чтобы batch можно было проверять по expected-count до записи в БД.

---

## 1. Batch boundaries

Один batch `Ben_Kim` соответствует одному пользовательскому запросу / одному `correlation_id` и содержит результаты по одному или нескольким тикерам.

Batch не является новым типом бизнес-артефакта вместо `analysis_result`.
Он является только транспортной оболочкой, внутри которой лежат канонические отдельные объекты `analysis_result`.

---

## 2. Expected count rule

Для каждого тикера:

`expected_results_per_ticker = active_strategy_count × 3`

Где `3` — это фиксированный набор таймфреймов:
- `1m`
- `5m`
- `60m`

Для всего batch:

`expected_results_total = tickers_count × active_strategy_count × 3`

Batch считается полным только если фактическое число элементов равно ожидаемому числу, либо по отсутствующим элементам явно сформированы `partial/rejected` результаты.

---

## 3. Batch envelope

Рекомендуемая транспортная оболочка batch:

```json
{
  "event_type": "analysis_result_batch",
  "correlation_id": "corr_20260321_btc_snapshot_001",
  "requested_at": "2026-03-21T21:00:00Z",
  "producer": "Ben_Kim",
  "tickers": ["BTCUSDC"],
  "timeframes": ["1m", "5m", "60m"],
  "strategies": [
    "price_levels_fibo_horizontal_volume",
    "vertical_volume",
    "rsi_macd",
    "trade_speed",
    "added_later_placeholder",
    "elliott_waves"
  ],
  "expected_results": 18,
  "results": []
}
```

---

## 4. Result item rule

Каждый элемент массива `results` обязан быть валидным `analysis_result` по канонической схеме.

То есть внутри batch каждый item содержит:
- `event_type = analysis_result`
- `analysis_id`
- `symbol`
- `strategy`
- `frame`
- `signal`
- `conclusion`
- `confidence`
- `observed_at`
- `source_window`
- `status`
- `result_code`

---

## 5. Canonical storage mapping

`Jack` должен сохранять не только сам batch, но и каждый item как отдельную запись в `analysis_results`.

Batch-уровень полезен для:
- transport;
- валидации expected count;
- операторского логирования;
- подтверждения completeness.

Но канонический storage-unit — это отдельный `analysis_result`.

---

## 6. Recommended writeback workflow

### Step 1. Receive batch
`Jack` принимает batch от `Ben_Kim`.

### Step 2. Validate envelope
Проверяет:
- `correlation_id`
- список `tickers`
- список `strategies`
- `expected_results`
- непротиворечивость времени

### Step 3. Validate items
Проверяет каждый item по `analysis_result` schema.

### Step 4. Count check
Проверяет:
- `results.length == expected_results`
- либо отсутствующие комбинации представлены как формализованные `partial/rejected` элементы

### Step 5. Idempotent write
Пишет каждый result отдельно в `analysis_results` через upsert.

### Step 6. Confirm writeback
Возвращает `Ben_Kim` или orchestration layer подтверждение, что batch сохранён.

---

## 7. Canonical ordering inside results

Для удобства аудита и сравнения рекомендуется фиксировать порядок элементов в batch:

1. по `symbol` ASC
2. по `frame` в порядке:
   - `1m`
   - `5m`
   - `60m`
3. по `strategy` в порядке runtime-конфига

Это не меняет бизнес-смысл, но упрощает проверку полноты.

---

## 8. Example batch for BTCUSDC

Ниже сокращённый пример batch-объекта для одного тикера и шести стратегий.

```json
{
  "event_type": "analysis_result_batch",
  "correlation_id": "corr_btc_snapshot_20260321T210000Z",
  "requested_at": "2026-03-21T21:00:00Z",
  "producer": "Ben_Kim",
  "tickers": ["BTCUSDC"],
  "timeframes": ["1m", "5m", "60m"],
  "strategies": [
    "price_levels_fibo_horizontal_volume",
    "vertical_volume",
    "rsi_macd",
    "trade_speed",
    "added_later_placeholder",
    "elliott_waves"
  ],
  "expected_results": 18,
  "results": [
    {
      "event_type": "analysis_result",
      "analysis_id": "an_BTCUSDC_price_levels_fibo_horizontal_volume_20260321T210000Z_1m",
      "symbol": "BTCUSDC",
      "strategy": "price_levels_fibo_horizontal_volume",
      "frame": "1m",
      "signal": "neutral",
      "conclusion": "Цена находится внутри локальной объёмной зоны; явного преимущества поддержки или сопротивления в текущую минуту нет.",
      "confidence": 0.58,
      "observed_at": "2026-03-21T21:00:00Z",
      "source_window": {
        "from": "2026-03-21T18:00:00Z",
        "to": "2026-03-21T21:00:00Z"
      },
      "status": "ready",
      "result_code": "ok"
    },
    {
      "event_type": "analysis_result",
      "analysis_id": "an_BTCUSDC_vertical_volume_20260321T210000Z_1m",
      "symbol": "BTCUSDC",
      "strategy": "vertical_volume",
      "frame": "1m",
      "signal": "bullish",
      "conclusion": "Вертикальный объём усилился на росте, что поддерживает краткосрочное продолжение вверх.",
      "confidence": 0.71,
      "observed_at": "2026-03-21T21:00:00Z",
      "source_window": {
        "from": "2026-03-21T18:00:00Z",
        "to": "2026-03-21T21:00:00Z"
      },
      "status": "ready",
      "result_code": "ok"
    }
  ]
}
```

---

## 9. Acceptance rule

Batch считается готовым к записи, если:
- envelope валиден;
- expected count сходится;
- каждый result валиден по `analysis_result` schema;
- нет недоописанных комбинаций `ticker × frame × strategy`;
- все timestamps указаны в UTC.
