CREATE TABLE IF NOT EXISTS telegram_posts (
    as_of DATE PRIMARY KEY,
    posted_at TIMESTAMPTZ,
    message_id BIGINT,
    risk DOUBLE PRECISION NOT NULL,
    risk_state TEXT NOT NULL
);
