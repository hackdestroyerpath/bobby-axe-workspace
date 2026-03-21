# Agent Guide: 1$_Dollar_Bill

`1$_Dollar_Bill` распределяет капитал между тикерами на основании `grid_proposal` от `Maffi`, входной аналитики и ограничений из `docs/risk-framework.md`.

## Назначение

- принимать набор актуальных `grid_proposal`;
- рассчитывать долю капитала по каждому тикеру;
- проверять лимиты по тикеру и коррелированным группам;
- публиковать валидные объекты `capital_allocation` только при корректной сумме батча.

## Объект `capital_allocation`

```json
{
  "event_type": "capital_allocation",
  "allocation_id": "alloc_BTCUSDC_20260321T121000Z",
  "symbol": "BTCUSDC",
  "proposal_id": "grid_BTCUSDC_20260321T120000Z",
  "allocation_pct": 25.0,
  "risk_bucket": "medium",
  "rationale": "Аллокация ограничена потолком на тикер и подтверждена 5m/60m сигналами.",
  "approved_at": "2026-03-21T12:10:00Z",
  "status": "ready",
  "supporting_analysis_ids": [
    "an_BTCUSDC_rsi_macd_20260321T120000Z_5m",
    "an_BTCUSDC_volume_profile_20260321T120000Z_60m"
  ]
}
```

## Обязательная валидация суммы

`1$_Dollar_Bill` должен валидировать не только каждый объект `capital_allocation`, но и весь батч аллокаций.

### Правила

- Сумма всех `allocation_pct` в батче после округления обязана быть **ровно 100.0**.
- Проверка выполняется только по объектам со статусом `ready`.
- Если сумма больше или меньше `100.0`, весь батч должен быть отклонён с причиной `ALLOCATION_SUM_MISMATCH`.
- Перед финальной публикацией агент обязан применить правила округления из `docs/risk-framework.md`.
- Ни один отдельный объект не может превышать лимит на тикер из risk framework.
- Сумма по коррелированной группе не может превышать групповой лимит из risk framework.

### Рекомендуемая структура батча для проверки

```json
{
  "capital_allocation_batch": [
    {
      "symbol": "BTCUSDC",
      "allocation_pct": 25.0,
      "status": "ready"
    },
    {
      "symbol": "ETHUSDC",
      "allocation_pct": 20.0,
      "status": "ready"
    },
    {
      "symbol": "SOLUSDC",
      "allocation_pct": 15.0,
      "status": "ready"
    },
    {
      "symbol": "XRPUSDC",
      "allocation_pct": 10.0,
      "status": "ready"
    },
    {
      "symbol": "ADAUSDC",
      "allocation_pct": 30.0,
      "status": "ready"
    }
  ],
  "validation": {
    "sum_ready_allocation_pct": 100.0,
    "is_valid": true,
    "error_code": null
  }
}
```

## Правила публикации

- `proposal_id` должен ссылаться на существующий актуальный `grid_proposal`.
- `allocation_pct` должен быть числом от `0` до `100`.
- `risk_bucket` должен быть одним из: `low`, `medium`, `high`.
- `approved_at` должен быть указан в UTC в формате RFC 3339.
- `rationale` должен объяснять, почему тикер получил именно такую долю после применения риск-лимитов.
- Если `Data_collector` недоступен и активирован emergency stop, новые `capital_allocation` публиковать нельзя.
