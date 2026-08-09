# Security Policy

## Reporting a vulnerability

Email `hello@minihub.app` with the details. Please do not open a public issue for anything exploitable.

Include what you found, how to reproduce it, and what impact you think it has. A proof of concept helps but is not
required.

Expect an acknowledgement within a few days. This is a small project run by one person, so please allow reasonable
time before disclosing publicly.

## Scope

In scope: the public product at `https://bitcoinriskbrief.minihub.app`, its public API endpoints, and this repository.

Out of scope: findings that require physical access to the deployment host, denial of service through raw traffic
volume, and reports produced solely by automated scanners without a demonstrated impact.

## Product boundary

Bitcoin Risk Brief is an analytics and research product, not financial advice, investment advice, or a trading recommendation.

## What this product stores

The waitlist stores contacts submitted deliberately by visitors. There is no product analytics, no tracking cookie,
and no third-party beacon. See `docs/engineering/security-and-privacy.md`.
