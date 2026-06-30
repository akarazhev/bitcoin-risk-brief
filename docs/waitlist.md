# Waitlist

The waitlist is intentionally small and production-pilot focused. It stores interest signals without sending notifications yet.

## Frontend Behavior

The frontend form accepts one value:

- email address;
- Telegram handle.

On successful submission, the UI shows a saved state. The contact is not persisted in browser storage.

## API Endpoint

```http
POST /api/waitlist
Content-Type: application/json
```

Payload:

```json
{
  "contact": "user@example.com",
  "locale": "en",
  "source": "landing"
}
```

## Validation Rules

Contacts are validated server-side.

| Field | Rule |
| --- | --- |
| email | Must match a simple email pattern with no whitespace. |
| Telegram | Must match `@[A-Za-z0-9_]{5,32}`. |
| locale | Only `en` and `ru` are accepted; invalid values fall back to `en`. |
| source | Must match `[A-Za-z0-9_.:-]{1,64}`; invalid values fall back to `landing`. |

## Storage

Leads are stored in `waitlist_leads`.

Important columns:

- `contact`
- `normalized_contact`
- `contact_type`
- `locale`
- `source`
- `status`
- `created_at`
- `updated_at`

`normalized_contact` is unique. Re-submitting the same normalized contact updates metadata instead of creating a duplicate.

## Rate Limiting

`POST /api/waitlist` uses an in-memory fixed-window per-client limit. The default is:

```text
WAITLIST_RATE_LIMIT_PER_HOUR=20
```

For public production, complement this with the repo-managed Cloudflare edge rule from
`scripts/cloudflare_edge_rules.py`, which limits `POST /api/waitlist` to 5 requests per minute per IP and bypasses cache
for waitlist submissions.

## Current Scope

The waitlist stores leads only. It does not send emails, Telegram messages, or daily alerts yet.
