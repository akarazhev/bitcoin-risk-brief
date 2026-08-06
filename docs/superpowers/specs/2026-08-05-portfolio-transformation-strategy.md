# Portfolio Transformation Strategy

> Status: active decomposition, agreed 2026-08-05. This document defines the sub-project breakdown and the decisions
> that constrain each one. Individual sub-projects get their own design spec and implementation plan.
>
> Supersedes [Documentation And Portfolio Presentation Design](2026-07-01-documentation-portfolio-presentation-design.md),
> which assumed a private portfolio repository and explicitly excluded an open-source launch.

## Goal

Turn Bitcoin Risk Brief into a free, professional, publicly inspectable product that works as a portfolio artifact for
clients, as source material for articles and video, and as a first-class data source for AI agents.

The product remains genuinely useful to Bitcoin holders and is never degraded to serve the portfolio goal. But user
acquisition is deliberately not this quarter's objective: the aim is a product strong enough to be shown, rather than
another public risk chart competing for retail attention. See
[Prioritisation Principle](#prioritisation-principle-portfolio-audience-first).

## Starting Position

Verified 2026-08-05 against the live host and the repository.

Production is healthy and the pipeline runs unattended:

```
GET /api/readiness  → ready, latest_date=2026-08-04, data_age_days=1, row_count=5867
GET /api/risk/latest → risk=0.2395, risk_state=low, crypto-scout-canonical-v1.1
```

Strengths that are genuinely uncommon:

- operational honesty as a product feature: `/api/readiness`, `data_fresh`, `X-Cache-Version`, and the methodology
  version travel with the data;
- a deterministic, reproducible metric rather than an opaque model;
- a risk-level scenario ladder that answers "what price would change the state";
- seven product locales including RTL;
- CI, focused unit tests, Playwright and axe-core checks, strict CSP, Turnstile, rate limiting, ETag caching, USB
  deploy kit, backup tooling, and evidence packets.

Constraints that block portfolio value:

- the repository is private and carries no licence, so none of the engineering above is visible or reusable;
- the README leads with roughly sixty lines of accepted limitations before it states what the product does;
- the SPA answers HTTP 200 for every path, including `/robots.txt`, `/sitemap.xml`, and `/llms.txt`, so there is
  nothing addressable to link, crawl, or cite;
- there is no agent-facing surface at all: the FastAPI OpenAPI schema exists but is unreachable because nginx proxies
  only `/api/` while the default schema route sits outside that prefix;
- Phase 9 of the roadmap gates every remaining product issue behind traffic evidence that zero traffic cannot produce.

## Demand Baseline

Read 2026-08-05 from the checksum-verified server backup `20260804T183922Z`. Aggregates only; no contact value was
extracted or retained.

```
waitlist_leads total   5

contact_type           email 3, telegram 2
locale                 en 4, ru 1
source                 landing 5
status                 active 5

signups                2026-07-02  1
                       2026-07-15  1
                       2026-07-21  2
                       2026-07-25  1
```

No lead carries a campaign source value, so the controlled vocabulary defined in
[Marketing and Growth](../../marketing-and-growth.md) is not represented in the data.

**These five leads are organic arrivals that predate any promotion.** The four-week acquisition test described in that
playbook has never been run, by deliberate decision: the product is being built as a portfolio artifact first, not as
another public risk chart competing for retail attention.

The numbers are therefore a pre-promotion baseline, not evidence about demand. They say nothing about whether the
product would find users, because nobody has asked. Read them as the starting line for a future test, and do not treat
the marketing scorecard thresholds as failed — they have not been attempted.

What the baseline does establish is scale for planning: any work sized for an existing audience must account for an
audience of five.

## Role In The MiniHub Probe

Bitcoin Risk Brief is not an abstract portfolio piece. It is the sole evidence artifact behind an outreach campaign
that is live as of 2026-08-06, run from the sibling `minihub` workspace.

`minihub.app` is deployed and lists exactly one project under `Live`, linking here. The probe letters carry no direct
link to the Brief; the recipient's path is message signature → `minihub.app` → this product. The landing page exists
specifically to survive that check.

The campaign sends 34 messages to two buyer archetypes, six per weekday from 2026-08-06:

| Archetype | Rows | Channel | Problem stated in the letter |
| --- | ---: | --- | --- |
| Treasury / COO | 22 | Governance forum direct messages | What a treasury could withdraw under stress, and at what price |
| Data / Engineering Lead | 12 | Discord, X, Telegram | Feed degradation discovered downstream, unprovable after the fact |

The probe records the Brief as a relevant evidence asset for the Data / Engineering Lead archetype only. For Treasury
it demonstrates practice quality rather than their specific problem.

### The Unexploited Overlap

The Data / Engineering letter describes gaps, stale windows, silent sequence loss, and the inability to prove what a
feed did during an incident window. The Brief is already a working answer to exactly that: `/api/readiness` exposing
`data_fresh`, `data_age_days`, `covered_end`, and `latest_matches_validation_end`; the `btc_risk_validation` table;
`X-Cache-Version` bound to the validation row; HTTP 503 on staleness; and import provenance packets.

None of this is visible on the public surface. A Data Lead who follows the path sees a Bitcoin risk chart, not feed
observability. The proof exists and cannot be found.

Closing that gap needs two things already scoped: the public repository, which makes the pipeline inspectable, and one
docs-site page on freshness and validation semantics. Neither is an offer, so neither is blocked by the portfolio's
rule against offer artifacts before the minimum rate is fixed.

### Publication Gate

Improving the evidence artifact mid-campaign would make early and late responses within a segment incomparable, which
is the one thing the probe's own measurement discipline forbids.

**Nothing that changes the public surface ships until the last probe message is sent, on 2026-08-13.** This
includes repository visibility, the docs site, the agent surface, and any product copy change.

The campaign schedule is fixed: 34 messages at six per weekday from 2026-08-06, last message 2026-08-13, and the probe
itself closes 2026-08-27 under its fourteen-day stop rule. The gate uses the send date rather than the close date
because domain checks cluster at message receipt; waiting the extra fortnight would buy little additional purity.

The gate applies to publication, not to preparation. All S1 and S2 work proceeds on a branch and lands in a single
flip once the window closes, so the constraint costs sequencing rather than time.

**The gate is a floor, not a target.** S1 and S2 are estimated at two to two and a half weeks from 2026-08-06, which
lands after 2026-08-13 regardless. On current estimates the gate is not the binding constraint on the release date —
readiness of the branch is.

## Prioritisation Principle: Portfolio Audience First

The product serves two audiences, and they are not the same people:

- the **portfolio audience** — technical clients, collaborators, employers, and readers of articles, who judge the
  engineering, the documentation, and the decisions behind them;
- the **product audience** — long-horizon Bitcoin holders, who judge the daily signal.

The current objective is the portfolio audience, and it currently has a concrete instance: the Data / Engineering Lead
who arrives from the MiniHub probe with a few seconds of attention and a specific problem in mind. When a design
question is ambiguous, resolve it for that reader.

Sub-projects are ranked by what that audience sees:

| Sub-project | Portfolio value | Product value |
| --- | --- | --- |
| S1 open source | Highest — nothing is visible without it | — |
| S2 agent surface and docs site | High — the docs site is itself an artifact | Low |
| S3 MCP server | High — a strong 2026 signal, registry listing, article material | Low |
| S6a articles and content | High — the stated reason for the whole transformation | Medium |
| S4 methodology and addressable URLs | Medium — visible craft, organic search | High |
| S5a Telegram channel | Low — but cheap, and shows the product is alive daily | High |
| S5b email delivery and analytics | — | Medium, already gated |

Two consequences follow. A sub-project that serves only the product audience is deferred until the portfolio objective
is met, however useful it would be to users. And when this plan is revisited, re-rank by what a technical reader
encounters, not by feature appeal.

This ordering is a statement about sequence, not about worth. The product audience is not abandoned; it is simply not
what the current quarter optimises for.

## Competitive Position

Reviewed 2026-08-05. Directional only; re-check before publishing a named comparison.

| Alternative | Model | Strength | Where this product differs |
| --- | --- | --- | --- |
| [AlphaSquared](https://alphasquared.io/) | Paid | ML risk metric, brand recognition | Deterministic and reproducible rather than a black box |
| [btcriskindex.com](https://btcriskindex.com/) | Free | Live index, multiple timeframes | Visible freshness and readiness, scenario ladder, seven locales |
| [bitcoinrisk.net](https://bitcoinrisk.net/) | Free | Public methodology, alerts, API | Operational transparency and explanation quality |
| [CryptoQuant](https://cryptoquant.com/), Glassnode | Paid terminal | Data breadth, MCP server | Different ICP; not a competitor for the one-minute daily check |
| [Bitcoin-Risk-Metric-V2](https://github.com/BitcoinRaven/Bitcoin-Risk-Metric-V2) | Open source | Code is public | A complete production pipeline rather than a script |

Competing on "another risk score" is not winnable. Three positions are currently unoccupied:

1. the only BTC risk product that shows the user whether the underlying data can be trusted today;
2. the only one with a fully open, reproducible pipeline, once the repository is public;
3. the first free BTC risk signal built to be consumed by AI agents.

[CryptoQuant already ships an MCP server and `llms.txt`](https://coinpaprika.com/education/what-is-the-model-context-protocol-mcp/),
which validates the agent channel at the professional tier while leaving the free niche empty. MCP has become the
[de facto agent integration standard through 2026](https://dev.to/alexmercedcoder/the-state-of-agentic-ai-standards-in-2026-mcp-a2a-webmcp-osi-and-the-protocol-stack-taking-3o2l).

## Evidence Posture

The roadmap's evidence-first discipline is the strongest engineering signal in the project and must not be weakened.
The problem is placement, not principle.

Two registers apply from now on:

- **Operational claims** — freshness, backups, monitoring, deployment, import provenance — keep the current strict
  evidence language and stay in `docs/operations/`.
- **Product and portfolio surfaces** — README, docs site, product pages, agent files — use ordinary descriptive
  language. Stating that the product displays data freshness is a description of implemented behaviour, not a claim
  requiring an evidence packet.

This resolves the Phase 9 deadlock without lowering any operational standard.

## Agreed Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Portfolio artifact | Repository and live site, equally | Technical clients read code; everyone else reads the product |
| Source availability | Fully public | Git history audit found no secrets, so no rewrite is required |
| Licence | Apache-2.0 | Patent grant and attribution on modification; standard for data and infrastructure projects |
| Horizon | One quarter, including content | Supports the full S1 through S6a sequence |
| Docs site | MkDocs Material on GitHub Pages | Docs are already Markdown; Python matches backend and collector |
| Docs domain | `docs.bitcoinriskbrief.minihub.app` | Separate origin keeps the product CSP untouched and the server unloaded |
| Operator evidence | Public, relabelled | Retained in `docs/operations/` under an explicit operational-log banner |
| Email provider | ZeptoMail with the list in PostgreSQL | List, consent, and suppression stay in owned code; roughly zero cost at pilot volume |
| First delivery channel | Public Telegram channel | No recipients, therefore no consent, opt-in, or schema migration |
| Publication timing | After the last probe message, 2026-08-13 | Changing the evidence artifact mid-campaign would make responses within a segment incomparable |

## Git History Audit

Run 2026-08-05 across all 268 commits and two authors, as a precondition for going public.

- `.env` was never tracked; `.gitignore` has been disciplined since the first commit.
- No API keys, secrets, passwords, or tokens in tracked content.
- No private IP addresses, server hostnames, or filesystem paths in `docs/`, `scripts/`, or `server-kit/`.
- No personal email addresses in tracked files.

No history rewrite is required. Re-run the scan immediately before flipping visibility.

## Sub-Projects

Each sub-project gets its own design spec and implementation plan.

| ID | Sub-project | Resolves | Depends on | Estimate |
| --- | --- | --- | --- | --- |
| S1 | Open-source release | Private repo, no licence, README shape | — | ~1 week |
| S2 | Agent surface and docs site | Agent discoverability, soft-404, docs hosting | — | ~1-1.5 weeks |
| S3 | MCP server | Agent integration depth, registry presence | S2 | ~1 week |
| S6a | Articles and content | Source material for writing and video, OG images | S1, S2, S3 | ~2 weeks |
| S4 | Public methodology and addressable URLs | #42, SEO, shareable links | S1, S2 | ~2 weeks |
| S5a | Telegram channel autoposting | Recurring visibility, daily proof of life | #41 (soft) | ~3-4 days |
| S5b | Email delivery, consent, and analytics | #43, #41, #45 | S4, S5a, **audience gate** | ~3 weeks |

S1 and S2 are specified together in
[Open Source And Agent Surface Design](2026-08-05-open-source-agent-surface-design.md).

### Sequencing Constraints

- **The probe publication gate precedes everything.** No public-surface change ships before 2026-08-13; see
  [Role In The MiniHub Probe](#publication-gate). Branch work is unaffected.
- GitHub Pages on the free tier publishes only from a public repository, so the docs site cannot exist before S1.
- S3 needs the OpenAPI contract stabilised by S2.
- S6a follows S3 so that the open-source release, the docs site, the agent surface, and the MCP server are all
  available to write about. Publishing earlier would spend the strongest material before it exists.
- Product analytics (#45) moved out of the content work and into S5b. Instrumenting traffic that is not being sought
  produces noise, and the same measurement becomes meaningful once an acquisition test actually runs.
- S4 splits the methodology audience: the docs site holds the technical reference in English, while the in-product
  `/methodology` page holds the localised interpretation guide that issue #42 actually asks for. They do not duplicate.
- S5b requires a schema migration that S5a does not, because a public Telegram channel has no individual recipients.
- Issue #41 is a soft dependency for S5a and a hard one for S5b: a templated brief is tolerable in a channel feed and
  not tolerable in a personal inbox.
- **S5b is gated on audience size, not on the calendar.** Do not start it below fifty confirmed subscribers. At the
  current list of three email addresses, the consent, opt-in, unsubscribe, suppression, and migration work would
  exceed its own audience by an order of magnitude. Re-evaluate when S1, S2, S5a, and S4 have run long enough to move
  the number.

## Delivery Channel Analysis

Recorded here because the constraints are non-obvious and shape S5a and S5b.

### Telegram

A bot [cannot initiate a conversation with a user](https://community.make.com/t/telegram-bot-error-bot-cant-initiate-conversation-with-a-user/47720);
`sendMessage` accepts a username only for channels, never for private chats. Every `@handle` already stored in
`waitlist_leads` is therefore undeliverable by bot.

In practice this affects two records, so it is an operator task rather than a planning constraint: contact both people
directly and ask them to press `/start` if direct bot delivery is ever built.

A public channel avoids the problem entirely: the bot posts to the channel and users subscribe themselves. This makes
S5a a distribution channel as much as a delivery mechanism.

Direct bot delivery, if it is ever built in S5b, needs a deep link of the form `https://t.me/<bot>?start=<token>`, a
webhook that binds the resulting `chat_id` to the lead record, and treatment of `/start` as the consent event.

### Email

Zoho Mail is mailbox hosting, not a sending platform:
[200 messages per day per user on the free plan, with IMAP and SMTP moved behind Mail Lite](https://mail.mailbux.com/blog/email-comparisons/zoho-mail-free-plan-limitations-alternative).
It has no `List-Unsubscribe` handling, no bounce processing, and no suppression list. Broadcasting through it damages
domain reputation.

[ZeptoMail is the transactional product at $2.50 per 10,000 messages with no monthly base and 10,000 free on signup](https://www.zoho.com/zeptomail/pricing.html);
Zoho Campaigns is the marketing product. A band-change alert is event-triggered and fits ZeptoMail cleanly. A scheduled
weekly digest is a marketing send and sits in a grey area under transactional terms; confirm against current ZeptoMail
terms before building it, or route digests through Campaigns or a provider that permits both.

### Schema Gap Blocking S5b

`waitlist_leads` currently cannot express any state other than active:

```sql
CONSTRAINT waitlist_leads_status_check CHECK (status IN ('active'))
```

S5b must add consent records, confirmation and unsubscribe tokens, `telegram_chat_id`, bounce and suppression state,
and a send log for idempotency. That is a backwards-compatible migration governed by the existing API/DB
change-management gate, and it is the main reason S5b carries an audience gate: the migration is the same size whether
the list holds three addresses or three thousand.

### Legal Frame For S5b

The product is localised into German, French, and Spanish and quotes prices in EUR, so an EU audience must be assumed.
Recurring email requires documented consent and easy withdrawal. The current single-field form records no consent, and
issue #43 already documents that the copy overstates what happens. Delivery cannot be built on the existing list
without double opt-in, including re-confirmation of existing email leads.

## Non-Goals

- Broadening into a general crypto dashboard or multi-indicator terminal.
- Changing `crypto-scout-canonical-v1.1` as part of this transformation.
- Paid tiers, accounts, billing, or SLA commitments.
- Weakening the strict CSP, the no-financial-advice posture, or the operational evidence discipline.
- Implementing more than one distribution channel at a time.

## Acceptance Criteria

- A technical reader reaches a working local stack from the public README without private context.
- An AI agent can discover the product, read its contract, and call it correctly using only public files.
- Every operational limitation remains documented and findable, without appearing on product surfaces.
- Each sub-project ships with its own spec, plan, tests, and verification record.
