CREATE TABLE IF NOT EXISTS collector.agent_signature_ledger (
    signature_id UUID PRIMARY KEY,
    signature_code TEXT NOT NULL,
    producer TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    object_scope_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    object_hash TEXT,
    status TEXT NOT NULL DEFAULT 'registered',
    notes TEXT,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_at_utc TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_signature_ledger_producer
    ON collector.agent_signature_ledger (producer);

CREATE INDEX IF NOT EXISTS idx_agent_signature_ledger_object_type
    ON collector.agent_signature_ledger (object_type);

CREATE INDEX IF NOT EXISTS idx_agent_signature_ledger_object_id
    ON collector.agent_signature_ledger (object_id);

CREATE INDEX IF NOT EXISTS idx_agent_signature_ledger_signature_code
    ON collector.agent_signature_ledger (signature_code);
