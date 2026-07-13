CREATE TABLE IF NOT EXISTS risk_level_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    as_of TIMESTAMPTZ NOT NULL,
    snapshot_version TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (as_of, snapshot_version)
);

CREATE INDEX IF NOT EXISTS idx_risk_level_snapshots_as_of_desc
    ON risk_level_snapshots (as_of DESC);
