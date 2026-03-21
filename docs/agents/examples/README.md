# Ben_Kim Examples

Эта директория хранит reference-примеры для интеграции `Jack -> Ben_Kim -> storage`.

## Files

- `ben_kim_btcusdc_batch_example.json`
  - канонический пример batch-ответа `Ben_Kim`
  - 1 тикер (`BTCUSDC`)
  - 3 таймфрейма (`1m`, `5m`, `60m`)
  - 6 стратегий
  - всего `18` отдельных `analysis_result`

## Purpose

Использовать как reference для:
- интеграции writeback в storage;
- валидации expected count;
- тестов ingestion/output pipeline;
- сверки формата `analysis_result`.
