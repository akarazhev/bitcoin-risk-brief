# Marketing And Growth Design

> Status: approved through GitHub issue #44 and the 2026-07-31 user continuation request.

## Goal

Create a founder-executable four-week go-to-market test for the existing Bitcoin Risk Brief web product. The test must
produce qualified traffic, explicit alert interest, repeat-use evidence, direct feedback, and paid-intent signals without
adding a new product surface or overstating what the risk model proves.

## Approaches Considered

### Broad content and SEO

Publish a large educational library and optimize for generic Bitcoin searches. This can compound over time, but it is
slow, difficult to attribute during a small pilot, and likely to attract readers who want free education rather than a
repeatable risk workflow.

### Multi-channel packaging

Ship a PWA, Telegram Mini App, browser extension, or several social accounts before testing the current web page. This
may improve reach, but it introduces maintenance and confounds whether users value the signal or merely try a new
wrapper. The existing distribution-channel research keeps this as a later phase.

### Focused founder-led pilot

Use direct founder outreach, X, and permission-based Telegram community posts to reach a narrowly defined audience.
Publish a small set of repeatable evidence-led messages, use explicit campaign source names, and evaluate the existing
page over four weekly cycles. This is the selected approach because it is fast, inexpensive, and compatible with the
active Phase 9 learning loop.

## Audience

Primary ICP:

- self-directed Bitcoin holders who review allocation or DCA decisions weekly or monthly;
- hold BTC for months or years rather than trade intraday;
- already use charts, sentiment, or cycle indicators but want one concise daily risk context;
- care about methodology, data freshness, and the conditions that would change a signal;
- can consume English product copy.

Secondary ICP:

- Russian-speaking Bitcoin holders with the same long-horizon behavior;
- reachable through founder relationships and permission-based Telegram communities;
- interested in alerts or concise recurring briefs rather than a broad terminal.

English is the primary acquisition language because it provides the larger addressable audience and competitive research
surface. Russian is the secondary acquisition language because the product already supports it and the founder has a
credible direct-distribution path. Other locales remain available but are not treated as active launch markets until
source-attributed evidence supports them.

## Positioning

Bitcoin Risk Brief is a one-minute daily research brief that shows whether modelled BTC risk is low, neutral, or high,
what changed, whether the data is trustworthy, and which price scenarios would move the signal into another band.

The product competes with professional market-intelligence suites, free Bitcoin risk dashboards, and manual chart
workflows. It does not try to win on chart count, intraday data, DCA instructions, or portfolio allocation. It should win
on focus, deterministic explanation, visible readiness/freshness, and honest scenario framing.

Current reference alternatives reviewed on 2026-07-31:

- [Glassnode Market Compass](https://glassnode.com/products/studio/market-compass)
- [Glassnode Bitcoin Vector](https://glassnode.com/pricing/vector)
- [CryptoQuant pricing and alert packaging](https://cryptoquant.com/en/pricing)
- [BitcoinRisk.net](https://bitcoinrisk.net/)

## Deliverable

Create `docs/marketing-and-growth.md` with:

- ICP and non-target users;
- positioning and competitive alternatives;
- message hierarchy and EN/RU copy variants;
- three initial acquisition channels;
- campaign/source naming rules;
- a four-week experiment calendar;
- ready-to-use social, founder outreach, community, and weekly digest assets;
- numeric strong, continue, adjust, and stop criteria;
- an operator workflow that produces only sanitized aggregate evidence;
- prohibited claims and promotion rules.

Link the playbook from `README.md`, `docs/README.md`, and Phase 9 of `docs/production-roadmap.md`.

## Measurement Boundary

The playbook may use explicit campaign links, allowlisted source values, Cloudflare or operational aggregate counts, and
sanitized waitlist totals. It must not assume that issue #45 product analytics or issue #43 alert-specific CTA is already
implemented. Where those issues would improve attribution or conversion, the playbook must name them as dependencies
rather than describe them as current behavior.

## Safety And Trust Boundary

- No investment advice, allocation instructions, return claims, price predictions, or artificial urgency.
- No claims of audited accuracy, adoption, or user outcomes without evidence.
- No scraped contact lists, unsolicited bulk messages, or promotion that violates community rules.
- No raw contacts, private messages, IP addresses, analytics exports, or campaign dashboard links in Git.
- Current risk values may be used in time-stamped posts only with the report date, readiness state, methodology version,
  and scenario/not-advice framing.

## Verification

This is documentation-only work. Verification consists of:

- targeted reads of every changed file;
- link and terminology checks against current product docs;
- a placeholder/ambiguity scan;
- `git diff --check`;
- confirmation that no runtime code, data, configuration, or generated assets changed.
