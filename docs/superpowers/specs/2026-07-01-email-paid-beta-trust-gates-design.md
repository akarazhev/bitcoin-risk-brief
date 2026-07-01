# Email Paid Beta And Trust Gates

> Status: future-facing. Last reviewed 2026-07-01. This is a Phase 9 readiness gate for post-launch experiments, not a
> Phase 8 launch requirement.

## Context

Phase 9 may test alerts, daily email or Telegram briefs, paid beta access, paid API access, widgets, embeds, or
professional reuse of the BTC risk metric. Those experiments should not be blocked by heavy infrastructure before demand
exists, but the project should not send recurring messages or accept money without a few deliberate checks.

This spec captures the small gates that should run before:

- sending recurring email or Telegram messages;
- collecting the first paid-beta payment;
- issuing a risk-signal license;
- exposing the project more broadly as a professional product;
- relying on uptime or product trust claims beyond a small public pilot.

## Goal

Prevent avoidable post-launch mistakes around deliverability, payments, account recovery, synthetic monitoring, and
public trust evidence while keeping Phase 9 demand tests lightweight.

## Non-Goals

- Do not add billing, subscriptions, invoices, tax automation, or payment provider integration before paid demand exists.
- Do not add recurring email or Telegram delivery before users explicitly ask for it.
- Do not create enterprise legal, SLA, or compliance scope.
- Do not add a public status page before there are active users who would benefit from it.
- Do not replace the existing privacy, launch-governance, analytics, or agent-access designs.

## Recommended Approach

Use deferred gates instead of new product phases:

1. Email and outreach deliverability gate.
2. Paid beta and licensing gate.
3. Account recovery gate.
4. Synthetic journey monitor gate.
5. Public trust artifact gate.

Each gate should be completed only when its trigger appears. For example, the email gate is unnecessary for a waitlist
form with manual follow-up, but required before recurring email briefs.

## Email And Outreach Deliverability Gate

Before sending recurring email, product updates, or automated outreach, document and verify:

- sender identity and sender domain;
- SPF, DKIM, and DMARC records for the sending domain;
- email provider ownership and recovery path;
- unsubscribe or deletion request handling;
- bounce and complaint handling;
- rate limits and first-send volume;
- whether each recipient explicitly joined the waitlist or requested updates;
- no-advice framing in recurring content;
- privacy copy for what is sent, why it is sent, and how to stop it.

Telegram delivery has a similar gate, but with platform-specific details:

- bot ownership and token storage;
- opt-in source;
- stop or unsubscribe command;
- message cadence;
- no-advice wording;
- platform rules for automated messaging.

## Paid Beta And Licensing Gate

Before accepting the first payment, issuing a paid risk-signal license, or selling paid beta access, decide and record:

- payment provider or manual invoice path;
- who owns the merchant account;
- currency and displayed price;
- tax or VAT handling assumptions that need professional review if volume grows;
- refund and cancellation policy;
- paid entitlement: what the user receives and what is excluded;
- support expectation and response channel;
- attribution requirements for risk-signal reuse;
- usage limits and redistribution restrictions;
- whether billing records are stored outside the product database;
- how payment data is kept separate from anonymous product analytics.

For the early `EUR 9-19/month` risk-signal license, the default should remain narrow: one product or AI agent, current
methodology/freshness metadata, modest usage, no redistribution, no white-label use, no SLA, no custom methodology work,
and no high-volume API guarantees.

## Account Recovery Gate

Before broader professional exposure or paid experiments, verify recovery paths for:

- GitHub;
- Cloudflare;
- domain registrar;
- email sender/provider;
- payment provider, if used;
- Telegram bot account, if used;
- production `.env` storage;
- backup storage;
- 2FA backup codes.

The goal is not to centralize secrets in the repository. The goal is to make sure the operator can recover the project
after losing a device, browser session, or single account login.

## Synthetic Journey Monitor Gate

Readiness alerts are enough for the first public pilot. If the product gets active users, add a small synthetic journey
monitor before relying on uptime claims:

- public page loads over HTTPS;
- readiness endpoint returns 200;
- latest risk endpoint returns current data and expected cache headers;
- waitlist endpoint still returns `Cache-Control: no-store`;
- frontend renders the latest risk state without a JavaScript failure.

This can start as a scheduled external smoke check. It does not require a full observability platform.

## Public Trust Artifact Gate

If the product is shown to broader users, professional prospects, or portfolio reviewers, keep a small public or
portfolio-facing trust artifact aligned with the UI:

- methodology version;
- latest data date;
- data source;
- freshness expectation;
- no-advice disclaimer;
- last launch or release date;
- accepted limitations that matter to users.

This artifact can be a README section, product page copy, or release note. It should not imply regulatory approval,
investment advice, audited performance, or guaranteed availability.

## Error Handling

If a gate is skipped, record the reason and the boundary:

- manual waitlist follow-up does not require SPF/DKIM/DMARC yet;
- a verbal paid-intent conversation does not require billing setup yet;
- accepting payment does require refund/cancellation terms and a clear entitlement;
- active recurring messages do require unsubscribe or stop handling;
- paid or professional usage requires a support/contact path, even if no SLA is offered.

## Testing And Verification

Verification should match the gate:

- DNS records checked before recurring email;
- test email or Telegram message sent only to operator-controlled accounts before user sends;
- payment flow or invoice path tested with non-production or low-risk evidence before charging real users;
- account recovery checklist reviewed before paid experiments;
- synthetic monitor records expected HTTP status, cache headers, and frontend availability;
- trust artifact reviewed against the current methodology and data-source docs.

## Acceptance Criteria

- Phase 9 names email/outreach, paid beta/licensing, account recovery, synthetic journey monitoring, and trust artifact
  gates as deferred readiness checks.
- No paid or recurring-notification infrastructure is added before demand.
- Before the first real recurring send or payment, the relevant gate has explicit owner, evidence, and accepted
  limitations.
- The gates reinforce the current product boundaries: analytics, no investment advice, narrow risk-signal license, and
  no SLA before commercial demand justifies it.
