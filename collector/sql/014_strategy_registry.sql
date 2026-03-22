CREATE TABLE IF NOT EXISTS collector.strategy_registry (
    agent TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 100,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (agent, strategy_id),
    UNIQUE (agent, strategy_name)
);

INSERT INTO collector.strategy_registry (
    agent, strategy_id, strategy_name, enabled, sort_order, metadata_json
)
VALUES
    ('Ben_Kim', 'price_levels_fibo_horizontal_volume', 'Price Levels + Fibo + Horizontal Volume', TRUE, 10, '{"source":"ben_kim_seed"}'::jsonb),
    ('Ben_Kim', 'vertical_volume', 'Vertical Volume', TRUE, 20, '{"source":"ben_kim_seed"}'::jsonb),
    ('Ben_Kim', 'rsi_macd', 'RSI + MACD', TRUE, 30, '{"source":"ben_kim_seed"}'::jsonb),
    ('Ben_Kim', 'trade_speed', 'Trade Speed', TRUE, 40, '{"source":"ben_kim_seed"}'::jsonb),
    ('Ben_Kim', 'added_later_placeholder', 'Added Later Placeholder', TRUE, 50, '{"source":"ben_kim_seed"}'::jsonb),
    ('Ben_Kim', 'elliott_waves', 'Elliott Waves', TRUE, 60, '{"source":"ben_kim_seed"}'::jsonb)
ON CONFLICT (agent, strategy_id) DO UPDATE SET
    strategy_name = EXCLUDED.strategy_name,
    enabled = EXCLUDED.enabled,
    sort_order = EXCLUDED.sort_order,
    metadata_json = EXCLUDED.metadata_json,
    updated_at_utc = now();
