# Telegram Channel And Honest CTA Design

> Status: approved 2026-08-07. Covers sub-project S5a from the
> [Portfolio Transformation Strategy](2026-08-05-portfolio-transformation-strategy.md), tracked by issue #51.

## Goal

Post the daily risk observation to a public Telegram channel automatically, and replace the waitlist copy that
promises delivery the product does not perform.

## Why The CTA Must Change

The page currently reads, in all seven locales:

> **Get the daily signal** — Leave an email or Telegram handle. The first test cohort gets the BTC risk alert free,
> plus access to the 2-year risk history and risk-level views during the pilot.

Neither half holds. No alert is sent; the backend stores leads and delivers nothing. The two-year history and the
risk-level views are already public to every visitor, so presenting them as earned by surrendering a contact is
misleading.

The product's single differentiator is operational honesty — visible readiness, visible freshness, HTTP 503 instead of
a stale number. This is the one place that honesty does not hold, and it is the only interactive element on the page.

Once a channel exists the fix is a link. "Get the daily signal" stops being a form: the visitor subscribes and
receives the signal, with no contact stored, no consent record, no schema migration for personal data, and no GDPR
contour. The form survives for the honest question that issue #43 already specifies.

## A Channel, Not A Group

One-way broadcast. The bot posts, subscribers read, leaving is the unsubscribe. A group is a chat and carries
moderation duty; a room of strangers discussing a financial signal is a liability with no matching upside. Nothing
here creates a group.

Note that a Telegram bot cannot initiate a conversation with a user, so the Telegram handles already in
`waitlist_leads` cannot be added to anything. Reaching those two records is a manual operator task, out of scope here.

## Architecture

**The publisher lives in the collector.**

The trigger is "an import completed and validation passed" — an event the collector owns and that no other service
observes directly. The backend would have to poll for it. The collector already runs APScheduler, and `httpx==0.28.1`
is already in `collector/requirements.txt`, so no new dependency enters any production container.

`import_csv_once` is the single funnel: the scheduled refresh, the downloaded-CSV path, the public CoinMarketCap
download, and `backfill` all pass through it. It writes in order — OHLCV, risk rows, level snapshot, brief, validation
— with `write_validation` last. Publication hooks in after that call, inside `try`/`except`:

```python
try:
    await publish_daily_post(pool)
except Exception:
    logger.exception("telegram_publish_failed")
```

Publication is best-effort and can never fail an import. A Telegram outage must not stop data collection.

`publish_daily_post` reads what it needs through the existing repository functions rather than re-deriving anything:
`fetch_latest_risk`, `fetch_previous_risk`, `fetch_latest_risk_level_snapshot`, and `fetch_latest_validation`. The
collector already imports from `app.*`, so these are available without new plumbing.

## Freshness Gate

Reuse `build_readiness_payload` from `backend/app/readiness.py`. Do not reimplement the freshness rule: two answers to
"is this data current" would drift apart, and the readiness semantics are the product's most load-bearing claim.

**Post only when readiness reports ready and fresh, and the observation covers the last completed UTC day.** The
readiness check keeps the publisher aligned with the product's freshness rule; the additional last-completed-day check
ensures a channel post never announces an observation that has fallen behind today's completed data. This second gate
must run before `claim_telegram_post`, so a behind observation does not consume the date. If CoinMarketCap returned
nothing new and the CSV tail did not advance, `import_csv_once` still runs and still rewrites derived rows — but the
covered date is unchanged and there is nothing to announce. Say nothing rather than publish a number the product itself
would serve behind a 503.

## Idempotency

Publication state must survive container restarts, so it is persisted.

New table, `migrations/004_telegram_posts.sql`:

```sql
CREATE TABLE IF NOT EXISTS telegram_posts (
    as_of DATE PRIMARY KEY,
    posted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    message_id BIGINT,
    risk DOUBLE PRECISION NOT NULL,
    risk_state TEXT NOT NULL
);
```

Keyed on `as_of`, the covered date of the observation. One post per date, enforced by the primary key rather than by
application logic.

**Claim first, then send.** An earlier revision of this design said the row is written only after Telegram confirms
the send, and that `ON CONFLICT DO NOTHING` made a concurrent double-run harmless. That was wrong: the conflict clause
protects the table from a duplicate row, not the channel from a duplicate post. Two runs could both read an empty
ledger, both send, and only then collide on the insert — by which point the duplicate is public.

The insert itself is the mutual exclusion:

1. `INSERT ... ON CONFLICT (as_of) DO NOTHING RETURNING as_of` claims the date. No row returned means another run owns
   it, and this one stops.
2. Send.
3. On success, update the row with the `message_id`.
4. On failure, delete the claim — guarded by `message_id IS NULL`, so a confirmed post is never removed.

`message_id` being null is what distinguishes a claim from a confirmed post, which is why the column is nullable.

The residual window is a process dying between claiming and sending: the date stays claimed and no post appears. That
is a **missed post, not a duplicate**, which is the correct way for this product to fail — the same principle as
returning 503 rather than a stale figure. It is found with `SELECT as_of FROM telegram_posts WHERE message_id IS NULL`
and cleared by deleting that row. Automatic reclaim is deliberately not implemented: it would trade a rare silence for
a rare duplicate.

A date that is no longer the latest is skipped permanently. Back-filling yesterday's announcement into a channel is
noise, not a correction.

This table holds no personal data and does not touch `waitlist_leads`. It is nonetheless a schema change and passes
through the existing API/DB change-management gate: migration, focused tests, rollback note.

## Band Change

`risk_state` is already computed and stored. A band change is simply the latest `risk_state` differing from the
previous row's. `LOW_RISK_THRESHOLD = 0.30` and `HIGH_RISK_THRESHOLD = 0.70` live in `backend/app/risk.py`; nothing new
is defined here.

Daily data cannot observe a crossing that reverses within the same day. That is a property of the dataset, not a defect
to work around.

On a band-change day the post leads with the change. Otherwise it leads with the current state.

## Post Content

```
<b>Bitcoin Risk Brief</b> — report date 2026-08-11

<b>Risk 0.24 — low</b>
Change: −0.01 from 2026-08-09
Neutral band at risk 0.30 — model price $71,400
Coverage through 2026-08-10 · crypto-scout-canonical-v1.1

bitcoinriskbrief.minihub.app

<i>Analytics and research context, not financial advice.</i>
```

The boundary line is what makes the post worth reading. It answers the question the product exists to answer — what
would have to happen for the state to change — instead of restating a number the reader could have guessed.

Its source is the `risk_level_snapshots` row the collector already writes. The ladder uses `risk_step: 0.025`, so
`0.30` and `0.70` are exact points on it and need no interpolation. Selection:

| Current state | Boundary shown |
| --- | --- |
| `low` | `Neutral` at `0.30`, the entry into neutral |
| `neutral` | `Low` at `0.30` or `High` at `0.70`, whichever is nearer to the current risk |
| `high` | `Neutral` at `0.70`, the return to neutral |

If the snapshot is missing or lacks that point, **omit the line**. This follows the rule the product already applies to
`low_usd` and `high_usd`: hide a value rather than show a zero or a stale one.

English only in the first pass.

## Configuration And Secrets

Two settings join `collector/collector/config.py`, following the existing frozen-dataclass pattern:

| Variable | Meaning |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Bot credential. **Empty disables publication entirely.** |
| `TELEGRAM_CHANNEL_ID` | Target channel. |

An empty token is the default, so local development, CI, and the test suite never post. This is a safety property, not
a convenience: a test that posts to a public channel is a defect that cannot be undone.

Secret handling follows the `TURNSTILE_SECRET` precedent already in the repository — recorded in
`.env.production.example`, delivered through the USB env installer, never committed.

## CTA Rewrite

Implements the copy scope of issue #43 across all seven locales.

- "Get the daily signal" becomes a subscribe link to the channel.
- Stop presenting the already-public history and risk-level views as gated benefits.
- The form remains, asking whether a band-change alert delivered to a personal contact would be useful, recorded under
  an explicit source value rather than the generic `landing`.
- Copy states plainly what happens to a submitted contact today: stored for manual follow-up, with no automated
  delivery yet.
- Validation, server-side storage, rate limiting, Turnstile, and `Cache-Control: no-store` are unchanged.

Arabic RTL behaviour must be re-checked, since the block gains a link where it previously had only a form.

## Verification

Existing checks must continue to pass: `./scripts/manage.sh test-python`, `npm test --prefix frontend`,
`npm run build --prefix frontend`, `./scripts/manage.sh validate`.

New tests, all offline against a fake HTTP client:

- an empty token disables publication and performs no HTTP call;
- a fresh import for a new date posts exactly once;
- a repeated import for the same date posts nothing;
- a failed send writes no row, and the following import retries the same date;
- a date that is no longer the latest is never posted;
- degraded or stale readiness suppresses the post;
- band-change detection is correct at both boundaries, including the `>=` edge at `0.70`;
- a missing or incomplete level snapshot omits the boundary line rather than failing.

## Non-Goals

- Direct bot delivery to individual users, which belongs to S5b and issue #52.
- A Telegram group or any chat surface.
- Any change to `waitlist_leads`, and no storage of personal data anywhere in this work.
- Reply handling, commands, or an interactive bot.
- Multi-locale posting.
- Back-filling historical observations into the channel.
- Any change to risk methodology, band thresholds, or the collector's data paths.

## Acceptance Criteria

- A post appears automatically after a successful daily import, with no operator action.
- No post is published while readiness is degraded or the data is stale.
- Re-running an import for an already-published date produces no second post.
- Every post carries the report date, coverage-through date, and methodology version.
- A Telegram failure of any kind leaves the import successful.
- No personal data is read, written, or transmitted by the publishing path.
- With an empty `TELEGRAM_BOT_TOKEN`, the test suite makes no outbound request.
- The page promises nothing the product does not do: every stated benefit is either delivered on click or described
  accurately as not yet existing.
- All seven locales remain complete and consistent, including Arabic RTL.
