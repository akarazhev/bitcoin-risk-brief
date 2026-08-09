# Pilot Learning Loop

> **Operational log.** These entries record what was verified and when. They are not claims about product capability.

Phase 9 is the small-pilot learning loop after the 2026-07-15 watched first-traffic observation. Its purpose is to
collect enough sanitized evidence to decide the next narrow step without putting raw contacts, private messages,
account details, or production artifacts into Git.

This runbook is for observation and evidence summaries only. It does not authorize production database queries from this
workspace, waitlist POSTs, deployments, data refresh/imports, Cloudflare changes, monitor changes, backup operations,
tags, or pushes.

## Observation Cadence

During active pilot traffic windows, the operator should make a short same-day observation pass after deliberate traffic
promotion, link sharing, support follow-up, or a production update. If traffic is quiet, keep a twice-weekly pilot review
until the operator pauses the pilot or starts a broader launch-prep phase.

Each observation pass should produce either "no material change" or a sanitized evidence packet outside Git. Copy only
the final aggregate status into repository docs when it changes a readiness gate, roadmap decision, or launch boundary.

## Public Readiness Checks

Use GET-only checks for public readiness during the pilot:

- before a deliberate traffic window;
- after production updates or data-refresh events;
- after any report that the public page is stale, unavailable, or inconsistent;
- at least once per active pilot day while traffic is being watched.

Record only the check date, status, latest covered date, row count, freshness result, risk state if checked, and selected
cache/header outcomes. Do not copy raw JSON payloads, raw headers, screenshots, request logs, dashboard URLs, or private
paths into Git.

## Waitlist Review

Manual waitlist review is aggregate-only. The operator may review counts from the controlled production system, but Git
notes should contain only sanitized totals such as:

- total active leads;
- new leads since the previous packet;
- counts by source;
- counts by locale;
- counts by contact type;
- count of repeated/upserted contacts if available without exposing the contact value;
- first and last activity date buckets.

Do not record submitted contact values, normalized contacts, email addresses, Telegram handles, raw query output, query
text that embeds a private value, database connection strings, private database paths, or screenshots.

## Support And Feedback Review

Review support mail, direct messages, product questions, and operator conversations as sanitized themes only. Useful
summary categories include:

- confusion about risk meaning, freshness, methodology, or price fields;
- requests for alerts, daily email, Telegram delivery, API access, widgets, agent access, webhooks, embeddings, or
  licensing;
- bug reports grouped by visible symptom and affected surface;
- deletion, unsubscribe, privacy, or support-process requests by count and status;
- objections or trust questions that affect readiness copy, terms, methodology explanation, or launch boundaries.

Do not copy message text, sender identity, account IDs, profile URLs, dashboard URLs, private threads, support mailbox
addresses, phone numbers, screenshots, or raw transcripts into Git.

## Git Safety Rules

Repository notes may include sanitized dates, status labels, counts, source or locale categories, public endpoint names,
commit IDs, tag names, and pass/fail summaries.

Keep these out of Git:

- raw contacts, email addresses, Telegram handles, phone numbers, or user names;
- raw support messages, direct-message text, private threads, or screenshots with personal data;
- raw analytics events, raw access logs, IP addresses, full user-agent strings, or client fingerprints;
- account IDs, dashboard URLs, webhook URLs, private URLs, private filesystem paths, or provider secrets;
- `.env` values, tokens, API keys, database connection strings, recovery text, or backup contents.

## Decision Criteria

Use the smallest decision that fits the evidence.

Continue the current pilot when public readiness is fresh, no unresolved privacy/support issue exists, evidence remains
sanitized, and the signal is still too early or modest to justify a scope change.

Adjust the product or runbook when sanitized feedback shows a repeated clarity issue, locale/source mismatch, waitlist
friction, or small operational gap that can be corrected without expanding product scope.

Pause promotion when readiness is stale or non-200, waitlist submission health is uncertain, support/deletion/privacy
requests are unresolved, abuse exceeds the accepted pilot controls, a data-correction issue appears, or evidence cannot
be collected without risking raw private data in notes.

Broaden only to the next smallest launch step when several pilot observations show stable public readiness, no unresolved
privacy/support blocker, and explicit demand signals such as waitlist growth, repeat use, or direct requests for alerts,
API/agent access, licensing, or recurring delivery. Broader public launch, paid launch, commercial readiness, full
accessibility/legal approval, broader monitoring, and direct production import provenance still require their separate
readiness gates.

## First Phase 9 Evidence Packet Template

Fill this template outside Git first. Copy only the final sanitized summary into repository docs when it changes a gate
or roadmap decision.

```markdown
# Phase 9 Pilot Learning Packet

- Packet date:
- Scope: small operator-watched pilot learning loop
- Production revision checked:
- Public readiness summary:
  - health status:
  - readiness status:
  - latest covered date:
  - row count:
  - freshness result:
  - latest-risk state, if checked:
  - cache/header summary:
- Observation cadence:
  - window covered:
  - trigger: scheduled review | traffic promotion | support follow-up | production update | issue report
- Waitlist aggregate summary:
  - total active leads:
  - new leads since previous packet:
  - by source:
  - by locale:
  - by contact type:
  - repeat/upsert count, if available:
- Feedback/support summary:
  - direct-question themes and counts:
  - alert or delivery requests:
  - API, agent, widget, webhook, embedding, or licensing requests:
  - bug or confusion themes:
  - deletion, unsubscribe, privacy, or support-process requests:
- Safety checks:
  - raw contacts excluded:
  - raw messages excluded:
  - raw logs/analytics excluded:
  - account IDs/dashboard URLs/private paths excluded:
  - secrets/tokens/webhook URLs excluded:
- Decision:
  - continue | adjust | pause | broaden narrowly
  - reason:
  - next review date or trigger:
- Repository update needed:
  - none | production readiness | roadmap | operations | other:
```

If any field cannot be filled without raw private data, mark that field as omitted and explain the sanitized reason.
