# Decision Engine Contracts

## Цель
Зафиксировать единый контракт артефактов, которые `probabilistic_decision_engine` публикует для downstream-модулей вместо directional-сигналов от отдельных аналитических субагентов.

## Публикуемые артефакты
Центральный движок публикует три связанных артефакта:
- `state snapshot` — формализованное описание актуального состояния рынка и внутренне вычисленных признаков;
- `probability snapshot` — вероятностная оценка `LONG`, `SHORT`, `NEUTRAL` с объясняющими факторами;
- `grid proposal` — исполнимое предложение по параметрам сетки и защитным уровням.

Эти артефакты могут публиковаться как единый пакет на один символ/цикл расчёта или как три согласованных сообщения с общим `decision_id`.

## Единый JSON-like контракт decision snapshot
```json
{
  "decision_id": "BTCUSDC-2026-03-21T12:34:56Z",
  "symbol": "BTCUSDC",
  "timestamp": "2026-03-21T12:34:56Z",
  "engine_id": "probabilistic_decision_engine",
  "state_snapshot": {
    "market_regime": "trend_up",
    "feature_freshness_sec": 3,
    "feature_window": "last_300_ticks",
    "derived_features": [
      {
        "name": "microstructure_imbalance",
        "value": 0.62,
        "unit": "ratio",
        "interpretation": "Покупательская агрессия доминирует"
      }
    ],
    "data_quality": {
      "status": "ok | degraded | stale",
      "gaps_detected": 0,
      "notes": []
    },
    "source_snapshot_refs": [
      "artifacts/ingestion/BTCUSDC/2026-03-21T12-34-56Z.json"
    ]
  },
  "probability_snapshot": {
    "long": 0.58,
    "short": 0.17,
    "neutral": 0.25,
    "confidence": {
      "score": 0.58,
      "scale": "0.0-1.0",
      "label": "medium"
    },
    "dominant_outcome": "LONG",
    "reason_codes": [
      "trend_continuation",
      "positive_flow_imbalance"
    ],
    "degradation_flags": []
  },
  "grid_proposal": {
    "status": "tradable | neutral_only | blocked",
    "direction": "LONG",
    "recommended_grid_bounds": {
      "lower": 101250.0,
      "upper": 102100.0,
      "basis": "engine_expected_value_zone"
    },
    "suggested_tp": {
      "price": 102450.0,
      "basis": "projected_upside_target"
    },
    "suggested_sl": {
      "price": 100980.0,
      "basis": "risk_invalidation_level"
    },
    "execution_constraints": {
      "max_leverage": 3,
      "margin_mode": "isolated"
    }
  },
  "audit": {
    "calculation_trace_ref": "artifacts/decision_engine/BTCUSDC/2026-03-21T12-34-56Z.json",
    "neutral_fallback_reason": null
  }
}
```

## Обязательные поля верхнего уровня
- `decision_id` — уникальный идентификатор расчётного цикла или decision package.
- `symbol` — торговый инструмент.
- `timestamp` — UTC-время публикации в ISO 8601.
- `engine_id` — идентификатор движка, публикующего решение.
- `state_snapshot` — описание состояния рынка, derived features и качества данных.
- `probability_snapshot` — нормализованное распределение вероятностей и объяснение исхода.
- `grid_proposal` — параметры исполнения или явный безопасный отказ.
- `audit` — ссылки на trace-артефакты и причины деградации.

## Требования к `state_snapshot`
`state_snapshot` обязан содержать:
- описание текущего market regime или эквивалентного состояния;
- актуальность данных и/или окно расчёта признаков;
- список `derived_features`, достаточный для объяснения решения;
- статус качества данных и обнаруженные деградации;
- ссылки на входные snapshot-артефакты, из которых получено состояние.

Каждый элемент `derived_features` должен содержать:
- `name` — имя признака;
- `value` — числовое или категориальное значение;
- `unit` — единица измерения или `none`;
- `interpretation` — краткое объяснение влияния на решение.

## Требования к `probability_snapshot`
`probability_snapshot` обязан содержать:
- `long`, `short`, `neutral` — значения от `0.0` до `1.0`;
- нормализацию, при которой сумма трёх вероятностей равна `1.0` с допустимой технической погрешностью;
- `confidence.score` — агрегированную уверенность в итоговом состоянии;
- `dominant_outcome` — `LONG`, `SHORT` или `NEUTRAL`;
- `reason_codes` — формализованные причины выбора;
- `degradation_flags` — список флагов, объясняющих снижение уверенности или перевод в fail-safe.

### Требования к confidence
- `confidence.score` — число от `0.0` до `1.0`.
- `confidence.scale` — строка `0.0-1.0`.
- `confidence.label`:
  - `low` для `0.00-0.39`;
  - `medium` для `0.40-0.69`;
  - `high` для `0.70-1.00`.

## Требования к `grid_proposal`
`grid_proposal` обязан содержать:
- `status` — `tradable`, `neutral_only` или `blocked`;
- `direction` — `LONG`, `SHORT` или `NEUTRAL` в соответствии с итоговым сценарием;
- `recommended_grid_bounds` — рекомендуемые границы сетки, если размещение допускается;
- `suggested_tp` и `suggested_sl` — целевой и защитный уровни либо явное указание, что они не применяются в `blocked`/`neutral_only` сценарии;
- `execution_constraints` — ключевые ограничения, которые execution/risk layer обязаны дополнительно проверить.

## Правила деградации и совместимости
- Если качество данных недостаточно для directional-решения, движок обязан публиковать валидный `probability_snapshot` с повышенной вероятностью `NEUTRAL` и соответствующими `degradation_flags`.
- Если grid-параметры не могут быть рассчитаны безопасно, `grid_proposal.status` должен быть `neutral_only` или `blocked`.
- Расширение контракта допускается только с обратной совместимостью.
- Изменение смысла обязательных полей требует синхронного обновления `specs/system_architecture.md` и downstream-спецификаций.
- Execution и risk layer не должны принимать решение без обязательных полей, кроме случаев явного безопасного отказа, описанного в контракте.
