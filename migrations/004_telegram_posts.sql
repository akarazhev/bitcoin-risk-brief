CREATE TABLE IF NOT EXISTS telegram_posts (
    as_of DATE PRIMARY KEY,
    posted_at TIMESTAMPTZ,
    message_id BIGINT,
    risk DOUBLE PRECISION NOT NULL,
    risk_state TEXT NOT NULL
);

ALTER TABLE telegram_posts
    ALTER COLUMN posted_at DROP NOT NULL,
    ALTER COLUMN posted_at DROP DEFAULT;
