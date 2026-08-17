# Consent-First Email Delivery Design

> Status: approved 2026-08-17. Covers sub-project S5b from the
> [Portfolio Transformation Strategy](2026-08-05-portfolio-transformation-strategy.md), tracked by issue #52.

## Goal

Deliver band-change alerts by email to people who have explicitly confirmed they want them, on a permanently free
provider tier, with a consent contour a reader can audit.

## Scope

In: the schema migration, double opt-in, unsubscribe, the Brevo integration, the bounce webhook, and the
event-triggered band-change alert in all seven locales.

Out, and deliberately: the weekly digest and campaign attribution analytics, which became S5c because they are the
parts that need an audience. Also out: direct Telegram bot delivery, accounts, per-user thresholds, and any change to
the methodology.

## Why This Is Built Before Anyone Is Waiting For It

The earlier plan gated S5b on roughly a hundred Telegram subscribers. That gate measured demand with an instrument
nobody switched on: no marketing has run, so the count cannot rise, and a gate that cannot open is a cancellation
written as a condition. The gate was removed on 2026-08-17.

The replacement is a different justification rather than a lower threshold. This is a portfolio project, and a
consent-first pipeline — double opt-in, tokens, RFC 8058 one-click unsubscribe, suppression, bounce handling, an
idempotent send log — is stronger portfolio material than the channel, because the difficult part is legible in the
code rather than only in the result.

## Existing Leads Are Not Migrated

The rows already in `waitlist_leads` were collected under a different promise and are never emailed. They are not
marked, flagged, or re-confirmed; they simply never satisfy the send condition, because the columns that express
consent do not exist for them yet.

This was chosen over a re-permission campaign. A re-permission email is itself a message to someone who never
consented, and the list is three addresses — the legal exposure is real and the upside is nil.

## Schema

Migration `005_email_consent.sql`, backwards compatible, through the existing API/DB change-management gate.

```sql
ALTER TABLE waitlist_leads
    ADD COLUMN confirm_token       TEXT,
    ADD COLUMN confirm_sent_at     TIMESTAMPTZ,
    ADD COLUMN confirmed_at        TIMESTAMPTZ,
    ADD COLUMN unsubscribe_token   TEXT,
    ADD COLUMN unsubscribed_at     TIMESTAMPTZ,
    ADD COLUMN suppressed_at       TIMESTAMPTZ,
    ADD COLUMN suppression_reason  TEXT;

CREATE UNIQUE INDEX idx_waitlist_leads_confirm_token
    ON waitlist_leads (confirm_token) WHERE confirm_token IS NOT NULL;
CREATE UNIQUE INDEX idx_waitlist_leads_unsubscribe_token
    ON waitlist_leads (unsubscribe_token) WHERE unsubscribe_token IS NOT NULL;
```

**Subscription state extends `waitlist_leads` rather than living in a new table.** The reason is the clean-slate
decision above: with the state in the same rows, "legacy leads are never emailed" holds by construction. The new
columns are `NULL` for them and the send condition requires confirmation, so there is no flag anyone can forget to
set.

Eligibility is a condition, not a column:

```sql
confirmed_at IS NOT NULL AND unsubscribed_at IS NULL AND suppressed_at IS NULL
```

### Why `status` Is Left Alone

The strategy document called for a `status` constraint able to express more than `active`. This design does not widen
it and does not use it.

Three independent facts are involved: whether consent was given, whether it was withdrawn, and whether the mail system
rejects the address. A single enum conflates them, and the first real question — a subscriber who unsubscribed and
whose address later hard-bounced — has no correct single value. Three timestamps answer three questions and cannot
contradict each other. Documented consent under GDPR also wants a date rather than a boolean. `status` remains
vestigial.

### No IP Address Is Stored

Recording the IP at signup is the common way to evidence consent. It is not needed here: the evidence is the click on a
token that was delivered only to the mailbox in question. Holding less personal data suits a product whose stated
differentiator is operational honesty.

### Tokens

`secrets.token_urlsafe(32)` for both. Neither column is ever logged or returned by any API.

The confirmation token is single-use and cleared on use. There is no separate expiry column: it is valid while
`confirm_sent_at > now() - interval '7 days'`, so a resend extends the same token's life rather than issuing a
competing one. That matters for the resend rule below — reissuing a token would kill the link in the message already
sitting in the subscriber's inbox.

The unsubscribe token never expires, because it travels in the headers of every message sent. It is generated at
confirmation, not at signup, since an unconfirmed lead has nothing to unsubscribe from.

## Consent Flow

Mail clients prefetch links. Gmail and Outlook fetch URLs found in a message before any human acts, which decides the
shape of everything below: **a `GET` that unsubscribes would unsubscribe people automatically.**

| Endpoint | Method | Effect |
| --- | --- | --- |
| `/api/waitlist` | POST | Existing. Turnstile, rate limit, upsert — now also enqueues a confirmation email |
| `/api/waitlist/confirm` | GET | Confirms and renders a page |
| `/api/waitlist/unsubscribe` | GET | **Renders a button. Changes nothing** |
| `/api/waitlist/unsubscribe` | POST | Unsubscribes |

Confirmation over `GET` is retained. A scanner that fetches it is the mailbox's own infrastructure, so control of the
mailbox is demonstrated either way. Unsubscription over `GET` is not acceptable, which is exactly why RFC 8058
specifies a `POST`:

```
List-Unsubscribe: <https://bitcoinriskbrief.minihub.app/api/waitlist/unsubscribe?token=…>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

One URL serves a human on `GET` and a mail client on `POST`.

### The Pages Are Rendered By The Backend

Not by the SPA, for three reasons. Messages are opened with JavaScript disabled. The nginx configuration deliberately
returns 404 for unknown paths rather than the app shell — asserted by `test_unknown_paths_are_not_rewritten_to_the_app_shell`
and `test_fallthrough_location_returns_404` in `backend/tests/test_agent_surface.py` — so a new SPA route would mean
editing that contract. And the lead record already carries a locale, so the backend can answer in the subscriber's
language with no frontend involvement.

Self-contained HTML with inline CSS, matching the product palette. All responses carry `Cache-Control: no-store`,
following `POST /api/waitlist`.

### Rules

- **No Turnstile on confirm or unsubscribe.** A mail client cannot solve a challenge, and unsubscription must never be
  blocked. Both endpoints are rate limited with the existing `FixedWindowRateLimiter`.
- **Resubmitting does not spam.** The address is unique and upserted; a new confirmation message is enqueued only if
  the previous one is more than an hour old.
- **The response never varies by whether the address is known.** Otherwise the endpoint is an existence oracle.
- **Confirming twice and unsubscribing twice are idempotent** and produce the same page.

## The Outbox

```sql
CREATE TABLE email_outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES waitlist_leads(id) ON DELETE CASCADE,
    kind            TEXT NOT NULL,
    dedupe_key      TEXT NOT NULL UNIQUE,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    claimed_at      TIMESTAMPTZ,
    sent_at         TIMESTAMPTZ,
    attempts        INT NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_error      TEXT,
    CONSTRAINT email_outbox_kind_check CHECK (kind IN ('confirm', 'band_change'))
);
CREATE INDEX idx_email_outbox_pending
    ON email_outbox (next_attempt_at) WHERE sent_at IS NULL;
```

Both producers write a row in the same transaction as the state change they accompany. `POST /api/waitlist` upserts the
lead and enqueues its confirmation atomically; a failed transaction leaves no orphan message. Nothing in the request
path makes an outbound call, so the endpoint neither waits on Brevo nor fails when Brevo does.

**`dedupe_key UNIQUE` is the idempotency.** A band-change alert keys on `band_change:{as_of}:{lead_id}`, which makes
"one message per subscriber per band-change date" a database constraint rather than application logic — the property
`telegram_posts` gets from `PRIMARY KEY (as_of)`.

A confirmation keys on `confirm:{lead_id}:{confirm_sent_at}`, not on the token. Keying on the token would make a
permitted resend collide with the original row and silently send nothing, because the token deliberately survives a
resend; keying on the send time lets each permitted resend enqueue while still collapsing a double-submitted form.

**The outbox stores no address.** It holds `lead_id` and a payload of numbers; the address is joined at send time.
Deleting a lead therefore erases the address everywhere at once, and `ON DELETE CASCADE` clears the queue with it.
Personal data lives in one place.

### The Drain Loop

A job on the collector's existing APScheduler. Rows are claimed with `FOR UPDATE SKIP LOCKED`, the standard safe queue
claim in PostgreSQL, so concurrent workers cannot take the same row.

**On an unknown outcome, retry — the opposite of the rule the Telegram publisher follows.** That publisher treats
`TelegramDeliveryUnknown` as "never retry", because a duplicate public post is a permanent artifact visible to
everyone while a missed one is merely silence. Email inverts both halves: a duplicate is seen by one person and then
gone, whereas a missed alert is the product failing at the one thing it promised. Both message kinds are idempotent by
content — a repeated confirmation carries the same token and link, a repeated alert carries the same fact.

Up to five attempts with exponential backoff (1m, 5m, 25m, 2h, 10h). After that the row parks with `last_error` set.
Rows are never deleted; the table is the send log the strategy requires.

A definite rejection naming an invalid recipient suppresses the lead rather than retrying.

### The Daily Cap Is Internal, Not External

Brevo's free tier allows 300 messages per day, and every send here is a burst — a band change is one fact reaching
every subscriber at once. `EMAIL_DAILY_CAP`, default `300`, bounds each drain selection so the remainder parks until
tomorrow instead of meeting a provider refusal mid-burst.

## The Alert Trigger

`collector/collector/main.py` already calls `publish_daily_post` inside its own `try`/`except` after the import
completes. `enqueue_band_change_alerts(pool)` is added beside it in a second, independent guard, so email cannot break
the channel, the channel cannot break email, and neither can break the import.

The freshness gate is `build_readiness_payload`, the same function the channel uses. The project must not hold two
answers to "is this data current".

A message is enqueued **only when the band actually changed** — the latest `risk_state` differs from the previous row's.
No change, no email. That is the cadence decision made concrete: there is no daily email.

Enqueueing is one statement, and it is what makes a repeated import harmless:

```sql
INSERT INTO email_outbox (lead_id, kind, dedupe_key, payload)
SELECT id, 'band_change', 'band_change:' || $1 || ':' || id, $2
FROM waitlist_leads
WHERE confirmed_at IS NOT NULL AND unsubscribed_at IS NULL AND suppressed_at IS NULL
ON CONFLICT (dedupe_key) DO NOTHING
```

## Provider Integration

Brevo, chosen for its perpetual free tier; see the strategy's Delivery Design for the comparison and for why
ZeptoMail, Resend, and MailerSend were each excluded.

`collector/collector/brevo.py` follows `collector/collector/telegram.py` closely: a `BrevoSendError` for a definite
refusal and a `BrevoDeliveryUnknown` for an indeterminate one, a logging filter that redacts the API key, and an
injectable `client: httpx.AsyncClient | None = None`. Neither exception ever carries the key.

**An empty `BREVO_API_KEY` disables sending entirely**, the same safety property the Telegram publisher has. Local
development, CI, and the test suite cannot reach a real recipient.

New settings in `collector/collector/config.py`, following the existing frozen-dataclass pattern:

| Variable | Meaning |
| --- | --- |
| `BREVO_API_KEY` | Provider credential. **Empty disables sending entirely.** |
| `EMAIL_FROM_ADDRESS` | Envelope and header sender. |
| `EMAIL_FROM_NAME` | Display name. |
| `EMAIL_REPLY_TO` | A monitored address, not `noreply@`. |
| `PUBLIC_BASE_URL` | Base for confirmation and unsubscribe links. Defaults to `https://bitcoinriskbrief.minihub.app`. |
| `EMAIL_DAILY_CAP` | Free-tier burst bound. Defaults to `300`. |

Secrets follow the `TURNSTILE_SECRET` precedent: recorded in `.env.production.example`, delivered by the USB env
installer, never committed.

### Sending Domain

Send from a subdomain — `alerts@mail.bitcoinriskbrief.minihub.app` — rather than from `minihub.app`. A deliverability
problem in a broadcast must not damage the reputation of the domain carrying business correspondence. SPF, DKIM, and
DMARC records for that subdomain are operator work and are outside this design.

### Bounce And Complaint Webhook

Required, not optional: without it `suppressed_at` is never populated and a dead address is mailed indefinitely, which
damages domain reputation.

`POST /api/email/events` accepts Brevo's `hard_bounce` and `spam` events, sets `suppressed_at` with a reason, and
ignores everything else. Authentication is a long random path segment compared in constant time. Soft bounces are
ignored deliberately; the retry policy already covers transient failure.

## Content

The structure mirrors the Telegram path so that understanding one explains the other.

| | Channel | Email |
| --- | --- | --- |
| Composition | `daily_post.py` | `email_content.py` |
| Transport | `telegram.py` | `brevo.py` |
| Orchestration | `publisher.py` | `mailer.py` |

The alert body comes from `backend/app/brief.py`, which already generates `summary`, `what_changed`, `avoid_now`, and
`confirm_next` for all seven locales at `SUPPORTED_BRIEF_LOCALES`. Only the surrounding chrome is new — subject,
greeting, the line explaining why this message arrived, the unsubscribe link, and the footer. Roughly ten strings per
locale, following the `RISK_COPY` dictionary pattern already in that module.

Messages are multipart: HTML and plain text. The text part is not optional; it serves deliverability and is the honest
fallback. Arabic renders with `dir="rtl"` and must be checked in a real client rather than by inspection.

Every message states the analytics-not-advice boundary, in the same words the channel post and the MCP responses use.

**Open and click tracking are explicitly disabled.** Brevo enables them by default. A tracking pixel would contradict
both the decision not to store IP addresses and the product's stated position on privacy. This is a configuration
assertion, not an intention.

## Verification

Existing checks must continue to pass: `./scripts/manage.sh test-python`, `npm test --prefix frontend`,
`npm run build --prefix frontend`, `./scripts/manage.sh validate`, `mkdocs build --strict`.

New tests, all offline against a fake HTTP client, with a socket guard asserting the suite opens no outbound
connection:

- an empty `BREVO_API_KEY` sends nothing and performs no HTTP call;
- `GET /api/waitlist/unsubscribe` changes no state — the guard against mail-client prefetch, without which a
  regression would silently unsubscribe everyone;
- `POST /api/waitlist/unsubscribe` sets `unsubscribed_at`, including the RFC 8058 one-click body form;
- a legacy row with `confirmed_at IS NULL` is never selected — the clean-slate property, asserted rather than assumed;
- confirming twice and unsubscribing twice are idempotent;
- a band change enqueues exactly one row per eligible subscriber, and a repeated import for the same date enqueues
  none;
- no band change enqueues nothing;
- unconfirmed, unsubscribed, and suppressed leads are excluded;
- an unknown send outcome retries to the fifth attempt and then parks with `last_error`;
- a definite rejection naming an invalid recipient suppresses the lead;
- `EMAIL_DAILY_CAP` bounds a single drain and parks the remainder;
- the webhook sets `suppressed_at` on `hard_bounce`, ignores unknown event types, and rejects a bad path secret;
- every locale renders both parts, each containing the advice boundary and an unsubscribe link;
- the API key and both token columns appear in no log line and no exception message.

## Acceptance Criteria

- No message reaches an address that has not confirmed through double opt-in.
- Rows predating this work never receive a message.
- Unsubscription works from a mail client with one click, without JavaScript, and without a challenge.
- No link prefetch by a mail scanner can unsubscribe or suppress anyone.
- A repeated import for an already-alerted date produces no second message.
- A provider outage delays messages and loses none.
- A hard bounce or spam complaint suppresses the address without operator action.
- Deleting a lead removes every copy of that address, including anything queued.
- With an empty `BREVO_API_KEY`, the test suite makes no outbound request.
- Sending stays inside the free tier without a provider refusal.
- No message contains a tracking pixel or a rewritten click URL.

## Non-Goals

- The weekly digest and campaign attribution analytics, which are S5c.
- Any daily email.
- Direct Telegram bot delivery to individuals.
- Accounts, preferences, or per-user thresholds. The signal is market-wide and identical for everyone.
- Renaming `waitlist_leads` or `POST /api/waitlist`; that decision stands as recorded in
  [waitlist.md](../../engineering/waitlist.md).
- Any change to risk methodology or band thresholds.
