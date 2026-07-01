# Risk Methodology Research Design

> Status: future-facing. Last reviewed 2026-07-01. This is a post-launch research phase and does not change
> `crypto-scout-canonical-v1` or block the production-pilot gate.

## Goal

Evaluate whether Bitcoin Risk Brief can make the BTC risk metric more accurate, robust, or explainable after the first
public pilot creates usage evidence.

This work is research first. It must not replace the current production methodology until a candidate model has been
benchmarked, documented, and explicitly versioned.

## Roadmap Placement

This belongs after Phase 9 as a separate Risk Methodology Research phase.

Phase 6-8 should keep using `crypto-scout-canonical-v1` so the public pilot has a stable baseline. Phase 9 should first
measure whether users care about the existing signal. Methodology changes are only worth prioritizing after the product
has evidence that the BTC risk signal creates repeat use, waitlist interest, or integration requests.

## Research Questions

The research should start by defining what "more accurate" means for this product.

Candidate evaluation questions:

- Does the metric better identify overheated market-cycle zones?
- Does it better identify low-risk accumulation zones?
- Does it reduce false high-risk or low-risk readings compared with `crypto-scout-canonical-v1`?
- Does it stay explainable to non-technical investors?
- Does it remain stable when upstream data is revised, delayed, or noisy?
- Does it improve the public product promise without turning the page into a broad dashboard?

## Candidate Inputs

### Fear And Greed Index

Treat the Fear and Greed Index as external context or a confirmation signal, not as a first-choice component of the core
risk score.

Reasons:

- it may duplicate price momentum, volatility, and sentiment already reflected in market data;
- its methodology and availability are outside this product's control;
- users can view it directly elsewhere, so it is weak product differentiation;
- mixing public sentiment with structural market risk can make the core score harder to explain.

It can still be evaluated as an optional context line or comparison chart if user questions show demand for sentiment
confirmation.

### On-Chain Data

On-chain data is a stronger candidate for a future methodology version because it can measure behavior that OHLCV cannot
fully capture.

Candidate families include:

- valuation relative to realized cap, such as MVRV or realized price;
- holder profitability and stress, such as NUPL or supply in profit/loss;
- spending behavior, such as SOPR-style metrics;
- capitulation or realized profit/loss signals.

The first research pass should prefer one durable on-chain valuation family over a large basket of indicators. A small
model is easier to explain, validate, and maintain.

## Data Source Requirements

Any candidate data source must have:

- enough historical coverage for multiple Bitcoin cycles;
- clear licensing and acceptable production use;
- reproducible daily backfill;
- stable update timing;
- documented revision behavior;
- operational failure behavior that does not break `/api/readiness`;
- a path for local storage, validation, and backups.

If those conditions are not met, the input should remain a research-only comparison and not enter the production risk
metric.

## Versioning Rules

Do not silently change `crypto-scout-canonical-v1`.

If a candidate methodology is worth shipping, publish it as a new version such as `crypto-scout-canonical-v2`. The new
version should include:

- documented formula changes;
- side-by-side comparison with v1;
- updated risk-level solver behavior if needed;
- updated API metadata;
- migration or backfill notes;
- clear interpretation limits and no-advice language.

A v2 candidate may run in shadow mode before public release, but users should not see methodology churn without a clear
version label.

## Non-Goals

This phase does not include:

- changing the production metric before launch;
- adding many indicators at once;
- turning the product into a chart catalog;
- using Fear and Greed as a default core score input;
- adding trading advice or buy/sell recommendations;
- optimizing for a backtest without preserving explainability and operational reliability.

## Deliverables

- A research note defining the accuracy and quality criteria for the BTC risk metric.
- A short candidate list covering v1 baseline, Fear and Greed context, and one on-chain valuation-family candidate.
- A reproducible historical comparison against `crypto-scout-canonical-v1`.
- A recommendation to keep v1, publish a context-only signal, or design a `crypto-scout-canonical-v2` implementation.

## Acceptance Criteria

- The current production methodology remains stable through the public pilot.
- Any proposed v2 has better evidence than "it might be more accurate."
- Candidate data sources meet operational and licensing requirements before production use.
- The output remains explainable and consistent with the product's no-financial-advice positioning.
- If evidence is weak, the decision is to keep v1 and avoid expanding methodology scope.
