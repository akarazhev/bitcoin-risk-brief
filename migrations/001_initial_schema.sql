CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS btc_ohlcv_daily (
    timestamp TIMESTAMPTZ NOT NULL,
    open_usd DOUBLE PRECISION NOT NULL,
    high_usd DOUBLE PRECISION NOT NULL,
    low_usd DOUBLE PRECISION NOT NULL,
    close_usd DOUBLE PRECISION NOT NULL,
    volume_usd DOUBLE PRECISION NOT NULL,
    market_cap_usd DOUBLE PRECISION NOT NULL,
    circulating_supply DOUBLE PRECISION NOT NULL,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (timestamp)
);
SELECT create_hypertable('btc_ohlcv_daily', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_btc_ohlcv_daily_timestamp_desc ON btc_ohlcv_daily (timestamp DESC);

CREATE TABLE IF NOT EXISTS btc_risk_daily (
    timestamp TIMESTAMPTZ NOT NULL,
    price_hlc3 DOUBLE PRECISION NOT NULL,
    risk DOUBLE PRECISION NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    trend_dev DOUBLE PRECISION NOT NULL,
    vol_regime DOUBLE PRECISION NOT NULL,
    turnover DOUBLE PRECISION,
    z_trend_dev DOUBLE PRECISION NOT NULL,
    z_vol_regime DOUBLE PRECISION NOT NULL,
    z_turnover DOUBLE PRECISION,
    turnover_enabled BOOLEAN NOT NULL,
    risk_state TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT btc_risk_daily_risk_check CHECK (risk >= 0 AND risk <= 1),
    CONSTRAINT btc_risk_daily_state_check CHECK (risk_state IN ('low', 'neutral', 'high')),
    UNIQUE (timestamp)
);
SELECT create_hypertable('btc_risk_daily', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_btc_risk_daily_timestamp_desc ON btc_risk_daily (timestamp DESC);

CREATE TABLE IF NOT EXISTS btc_risk_validation (
    validation_key TEXT PRIMARY KEY,
    computed_at TIMESTAMPTZ NOT NULL,
    covered_start TIMESTAMPTZ NOT NULL,
    covered_end TIMESTAMPTZ NOT NULL,
    row_count INTEGER NOT NULL,
    risk_range_ok BOOLEAN NOT NULL,
    validation_summary TEXT NOT NULL,
    validation_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS brief_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    as_of TIMESTAMPTZ NOT NULL,
    snapshot_version TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (as_of, snapshot_version)
);
CREATE INDEX IF NOT EXISTS idx_brief_snapshots_as_of_desc ON brief_snapshots (as_of DESC);
