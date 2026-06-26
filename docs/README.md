# Documentation Index

This directory documents the current Bitcoin Risk Brief mini-product in English.

## Core Documents

- [Architecture](architecture.md): service layout, runtime flow, repository structure, and database responsibilities.
- [Data Pipeline](data-pipeline.md): canonical CSV source, CoinMarketCap refresh, validation, import, and failure behavior.
- [Risk Methodology](risk-methodology.md): `crypto-scout-canonical-v1`, features, weights, risk states, and risk levels.
- [API Reference](api-reference.md): public endpoints, request/response shapes, and readiness semantics.
- [Waitlist](waitlist.md): lead capture behavior, validation rules, storage model, and privacy notes.
- [Security and Privacy](security-and-privacy.md): headers, input validation, rate limiting, secrets, and PII handling.
- [Operations](operations.md): local commands, container lifecycle, database maintenance, and troubleshooting.
- [Production Readiness](production-readiness.md): release gates, production environment, guarantees, and external launch tasks.
- [Testing and Quality](testing-and-quality.md): test commands, coverage areas, smoke checks, and CI workflow.

## Historical Planning Docs

The `docs/superpowers/` directory contains historical implementation specs and plans. Those files are useful for audit trail and context, but the documents listed above describe the current runtime behavior.
