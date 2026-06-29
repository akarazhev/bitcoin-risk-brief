# Documentation Index

This directory documents the current Bitcoin Risk Brief mini-product in English.

## Core Documents

- [Product Spec and Alignment Review](01-bitcoin-risk-brief.md): original validation-product spec plus current implementation gaps against the MVP reliability requirements.
- [Architecture](architecture.md): service layout, runtime flow, repository structure, and database responsibilities.
- [Data Pipeline](data-pipeline.md): canonical CSV source, automatic public CoinMarketCap download, manual downloaded CSV intake, optional CoinMarketCap API refresh, validation, import, and failure behavior.
- [Risk Methodology](risk-methodology.md): `crypto-scout-canonical-v1`, features, weights, risk states, and risk levels.
- [API Reference](api-reference.md): public endpoints, request/response shapes, and readiness semantics.
- [Waitlist](waitlist.md): lead capture behavior, validation rules, storage model, and privacy notes.
- [Security and Privacy](security-and-privacy.md): headers, input validation, rate limiting, bot/abuse protection, caching safety, secrets, and PII handling.
- [Operations](operations.md): local commands, automatic and manual CoinMarketCap CSV refresh, container lifecycle, database maintenance, backups, and troubleshooting.
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md): local-server deployment for Ubuntu, ByFly, Cloudflare Tunnel, backups, monitoring, and rollback.
- [Production Readiness](production-readiness.md): release gates, production environment, data refresh choice, caching, security, browser/device QA, and external launch tasks.
- [Production Roadmap](production-roadmap.md): phased roadmap from current MVP to public production-pilot readiness.
- [Testing and Quality](testing-and-quality.md): test commands, coverage areas, browser/device QA, documentation hygiene, smoke checks, and CI workflow.

## Historical Planning Docs

The `docs/superpowers/` directory contains historical implementation specs and plans. Those files are useful for audit
trail and context. The documents listed above describe current runtime behavior and, where explicitly marked, planned
production-pilot work.
