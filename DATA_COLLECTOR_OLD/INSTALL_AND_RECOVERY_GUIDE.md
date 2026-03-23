# INSTALL_AND_RECOVERY_GUIDE

Краткая инструкция для коллег, которые будут сами поднимать или восстанавливать старый collector-контур как reference.

## 1. Что нужно для старого контура
- Linux VPS
- Python 3.12+
- PostgreSQL
- доступ к Binance Futures endpoints
- `.env` на базе `collector/.env.example`

## 2. Базовый порядок старта
```bash
cd collector
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 3. Поднять БД-схему
```bash
psql "$DATABASE_URL" -f sql/001_init.sql
psql "$DATABASE_URL" -f sql/003_feature_rsi_macd.sql
psql "$DATABASE_URL" -f sql/007_feature_elliott_vol.sql
psql "$DATABASE_URL" -f sql/013_analysis_results.sql
psql "$DATABASE_URL" -f sql/014_strategy_registry.sql
psql "$DATABASE_URL" -f sql/015_analysis_results_strategy_identity.sql
psql "$DATABASE_URL" -f sql/016_agent_signature_ledger.sql
```

## 4. Что было в старом runtime-контуре
- historical backfill
- live ingest
- aggregation in `second_bar`
- feature generation
- snapshot / downstream handoff

## 5. Что читать для старта
### Jack / infra
- `runbooks/data_collector_start.md`
- `runbooks/data_collector_recovery.md`
- `runbooks/data_quality_checks.md`

### Ben_Kim
- `contracts/data_collector.md`
- `contracts/ben_kim.md`
- `docs/ben_kim_payload_response_schema.md`

### Jusetta
- `contracts/jusetta.md`
- `docs/analysis_results_downstream_path.md`

## 6. Что проверять после старта
- есть ли свежие `raw_trades`
- есть ли свежие `second_bar`
- считается ли feature layer
- нет ли gap / lag / failed writes

## 7. Как использовать это при восстановлении
Этот old-контур нужен не для слепого копирования, а для восстановления знаний:
- какие таблицы были
- какие входы использовались
- какие transformation layers существовали
- какие downstream агенты зависели от collector

## 8. Что не переносить слепо
- старые временные workaround-и
- старые loop-скрипты без переоценки
- старые operational assumptions без новой валидации

## 9. Цель
Использовать `DATA_COLLECTOR_OLD` как reference baseline, а не как новый canonical collector.
