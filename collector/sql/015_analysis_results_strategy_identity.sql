ALTER TABLE collector.analysis_results
    ADD COLUMN IF NOT EXISTS strategy_id TEXT,
    ADD COLUMN IF NOT EXISTS strategy_name TEXT;

UPDATE collector.analysis_results
SET strategy_id = COALESCE(strategy_id, strategy),
    strategy_name = COALESCE(
        strategy_name,
        (
            SELECT sr.strategy_name
            FROM collector.strategy_registry sr
            WHERE sr.agent = 'Ben_Kim'
              AND sr.strategy_id = collector.analysis_results.strategy
            LIMIT 1
        ),
        strategy
    )
WHERE strategy_id IS NULL OR strategy_name IS NULL;

CREATE INDEX IF NOT EXISTS idx_analysis_results_strategy_id
    ON collector.analysis_results (strategy_id);
