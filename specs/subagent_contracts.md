# Subagent Contracts

## Цель
Зафиксировать единый контракт сигналов для разрешённых аналитических субагентов и правила их передачи в decision layer.

## Разрешённые аналитические субагенты
Только следующие источники могут поставлять аналитические сигналы в модуль-агрегатор:
- `vertical_volume_agent`
- `horizontal_volume_agent`
- `fibonacci_agent`
- `ticks_agent`
- `trade_activity_agent`
- `global_context_agent`
- `elliott_wave_agent`

Любой иной аналитический источник считается нерелевантным для decision layer и не должен участвовать в расчёте торгового решения.

## Единый JSON-like контракт сигнала
Каждый разрешённый аналитический субагент обязан публиковать сигнал в нормализованном JSON-like формате:

```json
{
  "agent_id": "vertical_volume_agent",
  "symbol": "BTCUSDC",
  "timestamp": "2026-03-21T12:34:56Z",
  "timeframe": "1m",
  "direction_candidate": "LONG | SHORT | NEUTRAL",
  "confidence": {
    "score": 0.0,
    "scale": "0.0-1.0",
    "label": "low | medium | high"
  },
  "supporting_features": [
    {
      "name": "relative_volume_ratio",
      "value": 2.4,
      "unit": "x",
      "interpretation": "Объём выше базового режима"
    }
  ],
  "invalidators": [
    "Импульс объёма исчез в следующих 3 барах",
    "Цена вернулась ниже POC"
  ],
  "recommended_grid_bounds": {
    "lower": 101250.0,
    "upper": 102100.0,
    "basis": "value_area_low/value_area_high"
  },
  "suggested_tp": {
    "price": 102450.0,
    "basis": "next_volume_node"
  },
  "suggested_sl": {
    "price": 100980.0,
    "basis": "acceptance_below_value_area_low"
  },
  "data_freshness_sec": 15,
  "source_snapshot_ref": "artifacts/vertical_volume/BTCUSDC/2026-03-21T12-34-56Z.json"
}
```

## Обязательные поля
- `agent_id` — идентификатор субагента, строго из списка разрешённых источников.
- `symbol` — торговый инструмент.
- `timestamp` — UTC-время расчёта сигнала в ISO 8601.
- `timeframe` — рабочий таймфрейм анализа.
- `direction_candidate` — кандидат направления: `LONG`, `SHORT` или `NEUTRAL`.
- `confidence` — нормализованный confidence score.
- `supporting_features` — список признаков, объясняющих сигнал.
- `invalidators` — список условий, при которых сигнал должен быть ослаблен или снят.
- `recommended_grid_bounds` — предложенные границы рабочей grid-зоны.
- `suggested_tp` — предлагаемая цель фиксации прибыли.
- `suggested_sl` — предлагаемый защитный уровень.
- `data_freshness_sec` — возраст данных в секундах на момент публикации.
- `source_snapshot_ref` — путь к артефакту/снимку, на базе которого получен сигнал.

## Требования к confidence
Все субагенты обязаны использовать единый формат confidence:
- `confidence.score` — число от `0.0` до `1.0`.
- `confidence.scale` — строка `0.0-1.0` для явной фиксации шкалы.
- `confidence.label`:
  - `low` для `0.00-0.39`
  - `medium` для `0.40-0.69`
  - `high` для `0.70-1.00`

## Требования к supporting_features
Каждый элемент `supporting_features` должен содержать:
- `name` — имя метрики/признака;
- `value` — числовое или категориальное значение;
- `unit` — единица измерения или `none`;
- `interpretation` — краткое объяснение вклада признака в направление.

## Требования к invalidators
`invalidators` должны:
- быть проверяемыми на реальных данных;
- описывать условия отмены, ослабления или перевода сигнала в `NEUTRAL`;
- не содержать ссылок на нерелевантные источники или ручные субъективные решения.

## Правила совместимости
- Контракт обязателен для всех разрешённых аналитических субагентов.
- Расширение полей допускается только с обратной совместимостью.
- Изменение смысла обязательных полей требует синхронного обновления `specs/system_architecture.md` и спецификаций конкретных субагентов.
- Decision layer не должен принимать сигнал без всех обязательных полей, кроме случаев явной деградации в `NEUTRAL` по policy fail-safe.
