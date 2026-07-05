# Documentation Index

This directory documents the current Bitcoin Risk Brief mini-product in English.

## Core Documents

- [Product Spec and Alignment Review](01-bitcoin-risk-brief.md): original validation-product spec plus current implementation alignment and remaining production-pilot operations.
- [Architecture](architecture.md): service layout, runtime flow, repository structure, and database responsibilities.
- [Data Pipeline](data-pipeline.md): canonical CSV source, automatic public CoinMarketCap download, manual downloaded CSV intake, optional CoinMarketCap API refresh, validation, import, and failure behavior.
- [Risk Methodology](risk-methodology.md): `crypto-scout-canonical-v1`, features, weights, risk states, and risk levels.
- [API Reference](api-reference.md): public endpoints, request/response shapes, and readiness semantics.
- [Waitlist](waitlist.md): lead capture behavior, validation rules, storage model, and privacy notes.
- [Security and Privacy](security-and-privacy.md): headers, input validation, rate limiting, bot/abuse protection, caching safety, secrets, and PII handling.
- [Operations](operations.md): local commands, automatic and manual CoinMarketCap CSV refresh, container lifecycle, database maintenance, USB kit packaging/updates, backups, ownership checks, and troubleshooting.
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md): local-server deployment for Ubuntu, ByFly, Cloudflare Tunnel, USB install/update flow, backups, monitoring, and rollback.
- [MSI Cubi 5 Ubuntu Server Setup](server-msi-cubi5-ubuntu-26.04.md): from-scratch guide for BIOS, Ubuntu Server 26.04 LTS, firewall, security, Podman Compose, USB kit deployments, ByFly, and Cloudflare Tunnel without remote SSH.
- [Production Readiness](production-readiness.md): release gates, production environment, data refresh choice, caching, security, browser/device QA, and external launch tasks.
- [Production Roadmap](production-roadmap.md): phased roadmap from current MVP to public production-pilot readiness.
- [Frontend QA](frontend-qa.md): desktop/mobile browser smoke matrix, chart rendering checks, visual QA notes, and frontend bundle budget.
- [Testing and Quality](testing-and-quality.md): test commands, coverage areas, browser/device QA, documentation hygiene, smoke checks, and CI workflow.

## Superpowers Archive

The `docs/superpowers/` directory contains design specs and implementation plans created during agent-assisted work.
Use [Superpowers Docs Index](superpowers/README.md) to see which files are completed, superseded, or still future-facing.
The core documents listed above remain the source of truth for current runtime and operational behavior.
