# Overview

Bitcoin Risk Brief answers one question every day: is modelled Bitcoin risk low, neutral, or high, and what would have
to change for that to move.

It is free, permanently. No paid tier, no accounts, no SLA. The source is open under Apache-2.0.

## What it does

- Computes a daily risk value from `0.0` to `1.0` out of canonical BTC/USD daily data, using the versioned
  `crypto-scout-canonical-v1.1` methodology.
- Maps that value to one of three states: low below `0.30`, neutral from `0.30` to below `0.70`, high at `0.70` and
  above.
- Shows a two-year history, and a scenario ladder of the prices at which the model would report each risk level.
- States whether today's data is current and whether the last import passed validation, on the page and through
  [`/api/readiness`](../engineering/api-reference.md).
- Publishes the daily observation to a free public [Telegram channel](https://t.me/bitcoinriskbrief).
- Serves everything through read-only endpoints and a [documented agent surface](../agents/agent-access-pack.md).

The interface is available in English, Russian, Simplified Chinese, German, French, Spanish and Arabic.

## What makes it different

**You can see whether to trust today's number.** The covered date, the freshness state and the methodology version
travel with the data. When the input goes stale the API returns HTTP 503 rather than a number that looks current.
Most risk dashboards show you a figure and leave you to guess how old it is.

**The metric is deterministic and reproducible.** No model weights you cannot inspect: the
[methodology](risk-methodology.md) is published, the inputs are named, and the same history produces the same value.

**It answers "what would change this".** The scenario ladder solves the model backwards — at which price does the
state become neutral, or high. That is the question a risk figure raises and rarely answers.

## What it is not

Analytics and research context. **Not financial advice, not investment advice, not a price forecast, and not a
trading recommendation.** The scenario prices are model outputs under held-fixed assumptions, not predictions or
targets.

The displayed price is HLC3 from the last completed daily candle — a model input, not a live quote.

A model omits things. Output quality depends on the input data and on the methodology's assumptions, and nothing in
the score estimates future returns or determines what action suits anyone.

## Where to go next

- [Risk methodology](risk-methodology.md) — features, weights, normalisation, and the level solver.
- [Freshness and validation](../engineering/freshness-and-validation.md) — what readiness asserts and why staleness
  returns 503.
- [Agent access pack](../agents/agent-access-pack.md) — the readiness-first call sequence for automated clients.
- [Production readiness](../operations/production-readiness.md) — current operational status and the limitations that
  are accepted rather than solved.
- [Archived validation spec](../archive/product-spec.md) — what the product was planned to be, in June 2026.
