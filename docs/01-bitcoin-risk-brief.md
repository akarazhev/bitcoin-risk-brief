# Bitcoin Risk Brief

## One-Line Product

A daily Bitcoin risk page that tells a user whether BTC is currently in a low, neutral, or high risk zone, with a price
ladder showing where risk levels would change.

## Why This Was First

This is the cleanest validation product because it has one asset, one core metric, one obvious user question, and one
compact output. A user does not need to understand the whole [Crypto Scout Analytics](https://github.com/akarazhev/crypto-scout-analytics) platform to understand the value.

The question is simple:

> Is Bitcoin risk currently attractive, neutral, or dangerous enough that I should wait?

That makes it easier to test with a landing page, a waitlist, and a daily brief than a broad dashboard would be.

## Target User

Primary:

- self-directed Bitcoin and crypto investors;
- users who buy or rebalance over days, weeks, or months;
- users who want an objective risk framing instead of social-media sentiment.

Secondary:

- analysts and creators who need a reusable BTC risk reference;
- founders testing demand for paid crypto analytics.

Not the target:

- intraday traders;
- users looking for leverage signals;
- users expecting financial advice or exact buy/sell instructions.

## Core Promise

In under one minute, the user can see:

- current Bitcoin risk;
- risk state: `low`, `neutral`, or `high`;
- how risk changed recently;
- historical context;
- price levels where risk would move to the next band;
- whether the latest data is fresh enough to trust.

## MVP Chart Set

Required:

- Bitcoin Risk history;
- Bitcoin Risk Levels price ladder;
- latest BTC price and latest risk;
- data freshness and validation state.

Optional later:

- BTC drawdown from ATH;
- Bitcoin log regression;
- 1-year rolling BTC ROI;
- Pi Cycle Top as a confirmation chart.

## MVP Features

- Public chart page.
- EN/RU daily brief copy.
- Waitlist capture.
- Methodology page.
- Readiness and data freshness indicator.
- Daily collector update.
- Admin/operator smoke checks.

This repository includes the standalone validation implementation:

- standalone frontend;
- FastAPI backend;
- TimescaleDB storage;
- canonical BTC CSV import;
- automatic public CoinMarketCap CSV download, manual downloaded CSV import, and optional CoinMarketCap API delta refresh;
- waitlist database;
- production deployment docs.

## Demand Signals

Strong signals:

- users join waitlist from the public risk page;
- users return after multiple daily updates;
- users ask for alerts at specific risk levels;
- users ask to compare risk with their personal buy/sell plan;
- users are willing to pay for daily/weekly notifications.

Weak signals:

- users only inspect the chart once;
- users ask for many unrelated coins before trusting the BTC signal;
- users mainly want free trading calls.

## Pricing Test

The first paid test should be simple:

- free public latest risk;
- email or Telegram daily brief for early users;
- paid beta at `EUR 9-19/month` only if users request alerts or history-based guidance.

Do not introduce multiple tiers for this micro-product.

## Reliability Requirements

The page must never imply certainty. It must show:

- last data date;
- data freshness state;
- methodology version;
- whether the latest import passed validation;
- disclaimer that risk levels are scenario outputs, not trading advice.

## Success Criteria

Validation is positive if, within a small traffic test:

- waitlist conversion is strong enough to justify direct outreach;
- at least a few users ask for daily notifications or alerts;
- repeat visits happen without a broad chart catalog;
- methodology questions are answerable without weakening trust.

## Next Action

Run the standalone product as the first public validation test. Do not add broad features until the waitlist and usage
data show whether a single Bitcoin risk signal can create a habit.

## Implementation Alignment Review

Reviewed: 2026-06-30

Overall status: the current implementation matches the MVP product and reliability requirements for a production pilot,
subject to environment-specific deployment, backups, monitoring, and first-traffic validation. The implemented system has
the standalone frontend, FastAPI backend, TimescaleDB storage, canonical BTC CSV import, automatic public CoinMarketCap
CSV download, manual downloaded CSV import, optional CoinMarketCap API delta refresh, waitlist database, readiness
endpoint, daily collector, production deployment docs, and EN/RU brief payloads.

### Confirmed Matches

- Public Bitcoin risk page exists in the React frontend.
- Latest BTC price, latest risk, and `low` / `neutral` / `high` state are exposed by `/api/risk/latest` and rendered in the hero.
- Recent risk change is exposed in `/api/brief/latest` as `delta_risk` and rendered as risk change versus the previous observation.
- Historical context is covered by `/api/risk/history` and the risk history chart.
- Risk-level price ladder is covered by `/api/risk/levels` and the risk levels chart.
- Nearest `0.35` and `0.65` threshold prices are derived from `/api/risk/levels` and rendered as public callouts.
- EN/RU daily brief copy is generated by the backend and rendered by locale switch in the frontend.
- Waitlist capture stores email or Telegram leads in PostgreSQL.
- Methodology documentation exists in `docs/risk-methodology.md`, and the public page includes a methodology section,
  methodology version, validation metadata, and no-advice disclaimer.
- Daily collector update exists through the scheduled collector service.
- Operator readiness and smoke checks are documented and exposed through `/api/readiness`.
- The frontend fetches `/api/readiness` and renders readiness, validation, latest date, covered end, and data age near the
  latest risk date.

### Gaps Against The Spec

No implementation gaps remain against the MVP reliability requirements in this product spec. Remaining work is external
production operation: deploy to the target host, run a live production refresh/import, configure Cloudflare edge controls,
schedule backups, verify restore, configure readiness alerts, repeat browser/device QA on the public hostname, and run the
first traffic test.

### Recommended Follow-Up

- Complete the production-pilot release gate in `docs/production-readiness.md`.
- Apply and smoke-test Cloudflare WAF, cache, bot-challenge, and rate-limit rules for the production hostname.
- Configure scheduled backups, off-server copy, restore drill, and readiness/collector alerts.
- Capture the first launch snapshot: commit, data date, readiness payload, public hostname, cache behavior, and waitlist
  test result.
- Keep post-launch product expansion gated by real waitlist, repeat-visit, alert, and agent-access demand signals.
