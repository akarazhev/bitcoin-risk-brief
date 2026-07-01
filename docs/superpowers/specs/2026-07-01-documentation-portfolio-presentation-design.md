# Documentation And Portfolio Presentation Design

> Status: future-facing final polish. Last reviewed 2026-07-01. This is for a private or portfolio repository, not an
> open-source community launch.

## Goal

After implementation stabilizes, update the repository so it reads like a professional production-oriented portfolio
project.

The target reader is a future collaborator, client, reviewer, investor, employer, or buyer who has access to the private
repository and needs to understand the product, architecture, operational maturity, and current status quickly.

## Timing

Do this after the active implementation items are complete or frozen:

- scheduled public CoinMarketCap refresh;
- public payload cache warmup or accepted latency decision;
- USB update/install kit v2 if it remains in the deployment path;
- first-viewport price model input polish if accepted before traffic;
- launch readiness checks and any final production configuration updates.

Doing the presentation pass too early would create churn because the README and docs would need to be rewritten after
each implementation change.

## Scope

The pass should include:

- professional root `README.md`;
- refreshed `docs/README.md`;
- current-state cleanup across roadmap, readiness, operations, deployment, API, methodology, security, testing, and data
  pipeline docs;
- clear separation between current runtime behavior and historical/future-facing `docs/superpowers/` specs;
- GitHub repository description and topics suitable for a private or portfolio project;
- synchronized external product brief in the sibling `product-ideas` workspace;
- optional screenshot or short GIF of the first viewport;
- optional social preview image if the repository is shown in a portfolio context.

## README Shape

The final root README should be a concise product and engineering overview, not a full operations manual.

Recommended sections:

- product summary and positioning;
- current status, including whether the public pilot is live or internal-only;
- live/demo URL if it is safe to share;
- screenshot or GIF;
- feature list;
- architecture summary;
- tech stack;
- quick start;
- common commands;
- data source and refresh model;
- risk methodology summary;
- deployment and operations summary;
- documentation index;
- disclaimer that the project is analytics, not financial advice.

The README should link to detailed docs instead of duplicating them.

## External Product Brief

The portfolio pass should also update the sibling product-ideas brief:

```text
/Users/andrey.karazhev/Developer/startups/product-ideas/01-bitcoin-risk-brief.md
```

That file should stay product-facing rather than engineering-facing. It should explain why the product exists, what
validation hypothesis it tests, what has actually been built, and which future ideas remain unvalidated.

Recommended updates:

- current product status and pilot URL if it is safe to share;
- implemented product surface and reliability controls;
- current pricing/demand-test hypothesis;
- completed operational maturity points, such as readiness, caching, no-key data refresh, deployment docs, and backups
  when verified;
- future-facing ideas clearly separated from implemented behavior: agent/API access, widgets, localization,
  distribution-channel research, and risk methodology research;
- explicit non-goals: intraday trading signals, broad multi-asset dashboard, financial advice, and open-source community
  launch.

The product-ideas brief is not the runtime source of truth. If it conflicts with the repository README, API docs, or
operations docs, update it to match the repository rather than changing runtime docs to match the older product brief.

## Documentation Cleanup

Update docs to match implemented behavior at the time of the pass:

- remove or revise stale planned notes for work that has been implemented;
- keep future-facing research or distribution ideas clearly marked as future-facing;
- ensure API examples match current response shapes;
- ensure operations and deployment commands match the selected production path;
- ensure risk methodology docs match the implemented formula and UI labels;
- ensure production readiness reflects actual launch checks and accepted limitations;
- keep `docs/superpowers/README.md` accurate as an archive index.

## GitHub Presentation

Recommended private/portfolio repository description:

```text
Production-oriented Bitcoin risk signal with FastAPI, React, TimescaleDB, daily CMC CSV ingestion, readiness checks, and local-server deployment docs.
```

Recommended topics:

```text
bitcoin, risk-metric, crypto-analytics, fastapi, react, vite, timescaledb, podman, cloudflare, data-pipeline, portfolio-project
```

If the project is later made public, revisit the description and topics after a separate public-release review.

## Repository Hygiene

Before presenting the repository:

- confirm `.env` and production secrets are not tracked;
- run a secret scan or manual secret audit over `.env*`, docs, scripts, and committed history as far as practical;
- ensure `.env.example` and `.env.production.example` contain placeholders only;
- confirm backups, local database volumes, dependency caches, browser test artifacts, and generated build output are not
  tracked;
- decide whether to add a private/proprietary license notice or leave the repository unlicensed while private.

## Non-Goals

Do not add open-source community scaffolding unless the repository is intentionally made public.

Out of scope for the private/portfolio pass:

- `CONTRIBUTING.md`;
- `CODE_OF_CONDUCT.md`;
- public issue templates;
- public support policy;
- open-source license selection;
- broad marketing copy that overstates demand or production adoption.

## Acceptance Criteria

- A reviewer can understand the product, architecture, data pipeline, risk methodology, and deployment posture from the
  README and linked docs within a few minutes.
- The README does not claim that planned features are already implemented.
- Core docs agree with the implemented code and selected production/deployment path.
- The external product-ideas brief is synchronized with the final product narrative and clearly separates shipped,
  validated, and future-facing ideas.
- GitHub description and topics are ready for a private or portfolio repository.
- No local secrets, backups, or generated artifacts are tracked.
- The project remains positioned as analytics, not financial advice or trading recommendations.
