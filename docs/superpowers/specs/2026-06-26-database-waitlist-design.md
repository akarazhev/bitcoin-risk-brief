# Database Waitlist Design

## Goal

Persist waitlist leads in PostgreSQL/TimescaleDB so Bitcoin Risk Brief can measure real demand without implementing delivery or notification infrastructure yet.

## Scope

- Store waitlist contacts submitted from the frontend.
- Accept email addresses and Telegram handles.
- Normalize contacts to prevent duplicate leads.
- Store locale, source, status, and timestamps.
- Expose `POST /api/waitlist` for the frontend.
- Keep the frontend form visually consistent and backend-backed.

## Non-Goals

- No email delivery.
- No Telegram bot flow.
- No notification outbox.
- No unsubscribe flow.
- No admin dashboard.

## Data Model

Create `waitlist_leads` with `id`, `contact`, `normalized_contact`, `contact_type`, `locale`, `source`, `status`, `created_at`, and `updated_at`. `normalized_contact` is unique. Valid contact types are `email` and `telegram`; valid locales are `en` and `ru`; valid status values start with `active`.

## API Behavior

`POST /api/waitlist` accepts `{ contact, locale, source }`. The server trims and validates contact, derives `contact_type`, normalizes the value, and upserts the row. The response returns a generic success envelope with `contact_type`, `locale`, and `created` so the UI can show a useful state without exposing database internals.

## Validation

Email validation is intentionally conservative and lowercases the address. Telegram validation accepts `@` plus 5-32 characters from letters, digits, and underscores, then lowercases it. Invalid input returns HTTP 422 with a generic validation message.

## Security

All DB writes use parameterized asyncpg calls. API errors do not expose stack traces or SQL details. The endpoint does not store secrets and does not log submitted contacts.
