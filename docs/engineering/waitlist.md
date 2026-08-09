# Waitlist

The waitlist is intentionally small and production-pilot focused. It stores interest signals without sending notifications yet.

## Frontend Behavior

The frontend form accepts one value:

- email address;
- Telegram handle.

On successful submission, the UI shows a saved state. The contact is not persisted in browser storage.

Before a submission can be sent, the browser renders Cloudflare Turnstile and contacts
`challenges.cloudflare.com` to obtain a single-use token. The frontend sends that token with the waitlist payload and
resets the widget after each same-page attempt. The backend verifies the token server-side before it can write a lead.

The public CTA positions the first test cohort for free BTC risk-alert access plus the two-year risk history and
risk-level views during the pilot. In the current implementation, the submission still stores only a lead for manual
founder/operator follow-up; automated email or Telegram delivery is not implemented yet.

The frontend also shows a compact privacy/terms/disclaimer note near the waitlist. The note is local UI copy only; it
does not add notification delivery, accounts, deletion handling, unsubscribe handling, or a public support channel.

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
  "source": "landing",
  "turnstile_token": "single-use-client-token"
}
```

## Validation Rules

Contacts are validated server-side.

| Field | Rule |
| --- | --- |
| email | Must match a simple email pattern with no whitespace. |
| Telegram | Must match `@[A-Za-z0-9_]{5,32}`. |
| locale | `en`, `ru`, `zh`, `de`, `fr`, `es`, and `ar` are accepted; invalid values fall back to `en`. |
| source | Must match `[A-Za-z0-9_.:-]{1,64}`; invalid values fall back to `landing`. |
| turnstile_token | Required single-use token (1-2048 characters). It must pass server-side Siteverify for the `waitlist` action and an allowed hostname. |

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
No failed, expired, replayed, wrong-action, wrong-hostname, or unavailable Turnstile verification writes a lead.

The public note summarizes this storage behavior: the app stores the submitted contact value, a normalized copy, contact
type, locale, source, status, and timestamps. Backend access logs may include method, path, status, client key,
Cloudflare ray ID, cache status, and duration, but they do not intentionally log submitted contact values.

## Local Review And Export

Operators can review waitlist leads from the local or deployed project checkout with:

```bash
./scripts/export_waitlist.sh
```

The default report prints aggregate counts and recent leads with masked contacts. It is safe for quick operational
review, but still should not be copied into Git if it contains private operational context.

For manual founder/operator follow-up, export full contacts only to an operator-controlled path:

```bash
./scripts/export_waitlist.sh --include-contacts --output /secure/path/waitlist.csv
```

The full CSV contains raw waitlist contacts and is PII. Store it outside the project checkout, dependency caches, browser
profiles, and Git history. The script writes the file with owner-only permissions and refuses to overwrite an existing
file.

## Rate Limiting

`POST /api/waitlist` uses an in-memory fixed-window per-client limit. The default is:

```text
WAITLIST_RATE_LIMIT_PER_HOUR=20
```

For public production, complement this with the repo-managed Cloudflare edge rule from
`scripts/cloudflare_edge_rules.py`, which limits `POST /api/waitlist` to 5 requests per minute per IP and bypasses cache
for waitlist submissions. These existing application and edge limits remain layered protection alongside Turnstile;
Turnstile is not a replacement for rate limiting.

## Current Scope

The waitlist stores leads only. It does not send emails, Telegram messages, or daily alerts yet.

The 2026-07-12 operator decision pass records the waitlist owner role as founder/operator, review cadence as several
times per week during pilot, retention through beta end with earlier operator-approved deletion on request, and manual
founder/operator follow-up only. Deletion and unsubscribe requests use manual requests through the dedicated support
contact path kept outside Git; the support mailbox with project-domain alias is created and ready, and exact addresses
stay outside Git. Do not commit raw contacts, raw review output, private contact values, or query details.

The 2026-07-15 small operator-watched first-traffic observation did not include or claim a production waitlist POST. Use
an operator-approved test contact only when a future smoke test explicitly needs to verify `POST /api/waitlist`.
