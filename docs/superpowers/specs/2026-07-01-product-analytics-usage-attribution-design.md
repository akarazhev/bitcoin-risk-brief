# Product Analytics And Usage Attribution Design

> Status: future-facing. Last reviewed 2026-07-01. This supports Phase 8 first-traffic validation and Phase 9
> integration/licensing experiments. It does not block the production-pilot gate unless the first traffic test cannot be
> interpreted from existing logs and edge analytics.

## Goal

Store enough usage statistics to understand demand for Bitcoin Risk Brief without turning the product into an account
system or collecting more personal data than the pilot needs.

The current backend already writes operational access logs for `/api/*`. Those logs are useful for debugging and abuse
review, but they are not enough for product decisions. Product analytics should answer:

- which sources bring traffic;
- which endpoints are used;
- whether users return;
- how waitlist conversion relates to source and locale;
- whether agents, widgets, or professional products create measurable integration demand;
- which future API clients or licensees generate billable usage.

## Roadmap Placement

This spans two stages:

- Phase 8 should define and, if needed, implement privacy-preserving first-traffic analytics for public page usage,
  source attribution, repeat visits, and waitlist conversion.
- Phase 9 should add client-level usage tracking only if agent access or risk-signal licensing demand appears.

## Recommended Approach

Start with minimal persisted analytics, not a full analytics platform.

The first implementation should either store daily/hourly aggregates directly or store short-lived raw events that roll
up into daily aggregates. The default preference is aggregates when they answer the question, because they lower privacy
and storage risk.

The public analytics layer should track:

- event time bucket;
- method and normalized path group, such as `risk_latest`, `risk_history`, `brief_latest`, `readiness`, `waitlist`;
- status family or status code;
- locale when provided;
- explicit source values, such as `landing`, `agent_access`, `risk_signal_license`, `pwa`, `telegram_mini_app`, or
  `browser_extension`;
- anonymous visitor or client hash for repeat-visit estimates;
- user-agent family, not the full raw user-agent string;
- cache status when available.

It should not store request bodies, waitlist contacts, raw IP addresses, full user-agent strings, or detailed browser
fingerprints.

## Attribution

Attribution should prefer explicit source values over inference.

For the public product, source values can come from waitlist payloads, URL parameters, embed or channel wrappers, and
agent-access examples. For anonymous page and API reads, source can be absent or derived from a small allowlist of
campaign parameters.

Do not infer identity from IP address alone. IP-derived values may be used only as rotating hashes for rough repeat-use
and abuse analysis.

## API Client Usage

If Phase 9 produces demand for licensed risk-metric access, add a separate client usage model instead of trying to turn
anonymous web analytics into billing data.

Future API usage tracking should use:

- `api_clients` or equivalent records for partner/product/agent identities;
- stored key identifiers or hashes, never raw API secrets;
- daily usage counters by client, endpoint group, status, and methodology version;
- limits and paid/free tier metadata when pricing is introduced;
- no SLA, redistribution, or white-label assumptions until a later commercial design approves them.

This is the right layer for "how many requests and from whom" when "whom" means a professional product, partner, or AI
agent. For anonymous visitors, "from whom" should remain a privacy-preserving source/client estimate.

## Privacy And Retention

Analytics must stay separate from waitlist PII.

Rules:

- do not join raw request history to waitlist contact values;
- keep raw events, if any, for a short retention window such as 30-90 days;
- keep aggregate daily stats longer when they contain no contact values, raw IPs, or full user-agent strings;
- make retention and fields explicit in `docs/security-and-privacy.md` before implementation;
- keep no-store behavior for `POST /api/waitlist`.

## Non-Goals

This design does not include:

- user accounts;
- a public analytics dashboard;
- detailed fingerprinting;
- storing raw IP addresses in product analytics tables;
- tying all anonymous visits to waitlist contacts;
- billing automation;
- API keys before integration demand exists;
- third-party analytics scripts as a default requirement.

## Success Criteria

The analytics work is useful when:

- first traffic can be summarized by visits, repeat-use estimate, source, locale, endpoint usage, and waitlist conversion;
- agent and integration experiments can identify whether requests came from `agent_access`, `risk_signal_license`, or
  another explicit source;
- future API licensing can count usage by client without relying on raw IP addresses;
- privacy documentation clearly states what is collected, what is not collected, and how long raw events are retained;
- product decisions use these measured signals instead of raw traffic volume alone.
