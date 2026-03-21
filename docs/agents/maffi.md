# Agent Guide: Maffi

`Maffi` генерирует торговую сетку на основании `analysis_result` и обязан соблюдать ограничения из `docs/risk-framework.md`.

## Назначение

- принять батч аналитики по одному `symbol`;
- проверить полноту и качество входных данных;
- сформировать `grid_proposal` или вернуть отказ с понятной причиной.

## Правила принятия решения

- Поддерживаются только входные данные для одного `symbol`.
- Обязательны валидные `analysis_result` для `1m`, `5m`, `60m`.
- Если сигналы конфликтуют по правилам risk framework, ответ должен быть `rejected`.
- Если confidence ниже `0.55`, ответ должен быть `rejected`.
- Все ценовые уровни должны удовлетворять логике направления:
  - для `long`: `grid_top > grid_bottom`, `stop_loss < grid_bottom`, `take_profit > grid_top`;
  - для `short`: `grid_top > grid_bottom`, `stop_loss > grid_top`, `take_profit < grid_bottom`.

## Шаблон объекта `grid_proposal`

Ниже приведён рабочий шаблон объекта, который агент должен формировать. Поля подобраны для удобства агента; при публикации во внешние контракты допускается маппинг в поля схемы `contracts/schemas/grid_proposal.schema.json`.

```json
{
  "event_type": "grid_proposal",
  "proposal_id": "grid_BTCUSDC_20260321T120000Z",
  "symbol": "BTCUSDC",
  "frame": "5m",
  "direction": "long",
  "grid_top": 64520.0,
  "grid_bottom": 64080.0,
  "grid_levels": 8,
  "stop_loss": 63940.0,
  "take_profit": 64780.0,
  "rationale": "5m и 60m подтверждают long-сценарий, 1m используется только для уточнения входа.",
  "confidence": 0.72,
  "based_on": {
    "analysis_ids": [
      "an_BTCUSDC_rsi_macd_20260321T120000Z_5m",
      "an_BTCUSDC_volume_profile_20260321T120000Z_60m"
    ],
    "signal_summary": {
      "bullish": 5,
      "bearish": 1,
      "neutral": 2,
      "ignore": 0
    }
  },
  "status": "ready"
}
```

## Обязательные поля `grid_proposal`

- `direction`
- `grid_top`
- `grid_bottom`
- `grid_levels`
- `stop_loss`
- `take_profit`
- `rationale`
- `confidence`

## Валидация перед публикацией

- `direction` должен быть одним из: `long`, `short`.
- `grid_top`, `grid_bottom`, `stop_loss`, `take_profit` должны быть положительными числами.
- `grid_levels` должен быть целым числом больше либо равным `2`.
- `confidence` должен находиться в диапазоне от `0` до `1`.
- `rationale` должен кратко объяснять, какие сигналы были использованы и почему сетка не нарушает risk framework.
- При `status = ready` объект обязан содержать все обязательные поля и валидный `based_on.analysis_ids`.
- При `status = rejected` агент обязан сохранить `rationale` с причиной отказа.

## Маппинг в контрактную схему

Если объект нужно привести к `contracts/schemas/grid_proposal.schema.json`, используется следующее соответствие:

- `grid_top` → `grid_upper_price`
- `grid_bottom` → `grid_lower_price`
- `grid_levels` → `grid_count`
- `stop_loss` → `sl`
- `take_profit` → `tp`

Поле `confidence` является внутренним обязательным полем агента и должно использоваться в риск-логике, даже если внешняя схема хранит его отдельно или не принимает напрямую.
