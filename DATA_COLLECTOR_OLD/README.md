# DATA_COLLECTOR_OLD

Архив старого `Data_collector` перед полным сносом и пересборкой с нуля.

## Что это
Эта папка сохраняет старую рабочую базу:
- код collector
- SQL-схемы
- runbooks
- контракты downstream-интеграции
- docs по storage / payload / downstream path

## Для кого
- **Ben_Kim** — читает feature / snapshot / analysis input contracts
- **Jusetta** — читает downstream path и analysis payload context
- **Maffi** — читает upstream contract и выход analysis layer
- **1$_Dollar_Bill** — читает upstream contract и allocation-adjacent context
- **Jack** — использует как reference для пересборки нового collector
- **Bobby Axe** — использует как historical baseline перед redesign

## Что внутри
### `collector/`
Старый код collector:
- `main.py`
- `backfill.py`
- `db.py`
- `config.py`
- `models.py`
- `features_packet.py`
- `features_rsi_macd.py`
- `features_elliott_vol.py`
- `sql/*`

### `runbooks/`
- `data_collector_start.md`
- `data_collector_recovery.md`
- `data_quality_checks.md`

### `contracts/`
- `data_collector.md`
- `ben_kim.md`
- `jusetta.md`
- `maffi.md`
- `dollar_bill.md`

### `docs/`
- `storage.md`
- `analysis_results_downstream_path.md`
- `ben_kim_payload_response_schema.md`

## Как использовать это как historical baseline
1. Не считать папку production-ready source of truth для нового collector.
2. Использовать её как reference:
   - какие данные собирались;
   - как выглядели raw / second / feature layers;
   - какие downstream ожидания уже были;
   - какие runbooks и checks существовали.
3. При восстановлении логики не переносить слепо весь код в новый collector.
4. Сначала выделять:
   - входы;
   - storage contracts;
   - transformations;
   - health / recovery / quality checks.

## Коротко: как работал старый collector
- Источник: Binance Futures USDC
- Исторические данные: backfill / replay
- Live-данные: realtime ingest
- Raw layer: сделки
- Curated layer: `second_bar`
- Старшие таймфреймы: `1m`, `5m`, `60m`
- Feature layer: packet / RSI-MACD / Elliott-vol
- Read-side: snapshot / lookup / downstream handoff

## Что коллегам читать первым
### Ben_Kim
1. `contracts/data_collector.md`
2. `contracts/ben_kim.md`
3. `docs/ben_kim_payload_response_schema.md`
4. `docs/analysis_results_downstream_path.md`

### Jusetta
1. `contracts/jusetta.md`
2. `docs/analysis_results_downstream_path.md`
3. `runbooks/data_quality_checks.md`

### Maffi
1. `contracts/maffi.md`
2. `contracts/ben_kim.md`
3. `contracts/data_collector.md`

### 1$_Dollar_Bill
1. `contracts/dollar_bill.md`
2. `contracts/maffi.md`
3. `contracts/ben_kim.md`

### Jack / Bobby Axe
1. `runbooks/data_collector_start.md`
2. `runbooks/data_collector_recovery.md`
3. `runbooks/data_quality_checks.md`
4. `contracts/data_collector.md`
5. `collector/sql/*`

## Важно
Это именно **OLD baseline**, а не место для дальнейшего развития.
Новый collector должен строиться отдельно и сознательно, а не как бессистемный patch старого контура.
