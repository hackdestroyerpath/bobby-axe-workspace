# Archived Legacy Data Source Specs

Документы в этой папке сохранены только как исторический след ранней декомпозиции по отдельным аналитическим источникам.

Они **не являются** актуальным контрактом для текущей архитектуры. Любые упоминания частоты, окон анализа или таймфреймов в этих файлах должны интерпретироваться только как внутренние rolling calculations внутри секундного live decision loop, а не как независимый график обновления.

Актуальные stage-based документы находятся в `agents/analysis/`:
- `feature_extraction_agent.md`
- `probability_engine_agent.md`
- `grid_synthesis_agent.md`
- `neutral_lifecycle_agent.md`
