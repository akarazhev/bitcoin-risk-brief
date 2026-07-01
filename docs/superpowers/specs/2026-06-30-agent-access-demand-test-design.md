# Agent Access And Risk-Signal Licensing Demand Test Design

> Status: future-facing. Last reviewed 2026-07-01. This remains a Phase 9 post-launch experiment and does not block the
> production-pilot gate.

## Goal

Test whether AI agents, professional products, and lightweight integrations are useful distribution and monetization
channels for Bitcoin Risk Brief after the first public production pilot is live.

The experiment should validate demand without turning the product into a broad API platform before there is evidence
that users want agent, developer, or paid risk-signal integrations.

## Roadmap Placement

This belongs in Phase 9: Post-Launch Learning Loop.

It must not block the production-pilot gate. Production launch still depends on the public page, data freshness,
readiness, waitlist capture, Cloudflare protection, backups, restore, monitoring, and the first traffic test.

## Target Users

- people using general-purpose AI agents to summarize market context;
- analysts and creators who want a reusable BTC risk signal in their workflows;
- developers evaluating whether the public risk API is worth integrating;
- professional products or AI agents that may want to license one BTC risk metric;
- future paid users who may want API keys, webhooks, alerts, embeddable outputs, or commercial-use rights.

## Initial Scope

The first version is an Agent Access Pack, not a new product surface.

It includes:

- a public agent-access guide for any HTTP-capable agent;
- examples for reading existing public endpoints;
- a required readiness-first flow;
- interpretation rules that keep the output framed as analytics, not advice;
- a clear statement that risk levels are scenario outputs, not buy/sell instructions;
- waitlist or contact tracking with `source=agent_access`;
- waitlist or contact tracking with `source=risk_signal_license` for paid risk-metric reuse requests;
- a short list of integration requests to collect manually, such as API keys, webhooks, MCP, SDKs, alerts, embedding,
  commercial-use rights, or one-product risk-signal licensing.

The existing public endpoints are sufficient for the first test:

- `/api/readiness`
- `/api/risk/latest`
- `/api/risk/levels`
- `/api/brief/latest`
- `/api/risk/history`

## Non-Goals

The first experiment does not include:

- a new `/api/agent/*` endpoint;
- authentication or API keys;
- billing;
- SLA commitments;
- paid rate limits;
- SDKs;
- MCP server;
- Codex Skill;
- LangChain or LlamaIndex packages;
- agent-specific responses that bypass the public methodology and disclaimer constraints.

Those can be designed only after the experiment produces demand signals.

## Demand Signals

Valid demand signals are:

- waitlist leads or direct contacts that arrive through `source=agent_access`;
- waitlist leads or direct contacts that arrive through `source=risk_signal_license`;
- direct requests for API keys, webhooks, MCP server, SDK, embeddable widgets, commercial use, alerts, higher limits, or
  permission to reuse the BTC risk metric in a product or AI agent;
- explicit acceptance of an early `EUR 9-19/month` paid test for one product or AI agent.

Raw API traffic is not enough by itself. It may indicate scraping or curiosity, but it does not prove willingness to
integrate or pay.

## Monetization Path

The Agent Access Pack itself should stay free and copyable. Monetization should attach to backend capabilities and
reliable workflows, not to the guide.

If demand appears, the next validation increment can test:

- a lightweight `EUR 9-19/month` risk-signal license for one product or AI agent;
- API keys and usage limits;
- paid higher rate limits;
- risk-level alerts;
- webhook delivery;
- daily or weekly machine-readable briefs;
- historical export;
- embeddable widgets;
- commercial creator or analyst licenses;
- SLA-style reliability for integrations.

The `EUR 9-19/month` price is appropriate only for an early paid-intent test around one BTC risk metric. It should remain
low-friction and manually operated at first. It may include access to the existing public risk endpoints, methodology
version, latest data date, readiness/freshness metadata, attribution requirements, and modest usage for one product or
agent.

It should not include redistribution, resale, white-label use, custom branding, high-volume API limits, SLA commitments,
dedicated support, custom methodology work, or broad historical-data licensing. Those belong to a later commercial API or
enterprise licensing design if the early test proves demand.

## Safety Rules

Agent-facing instructions must require agents to:

- check `/api/readiness` before presenting risk as current;
- include latest data date and freshness state when available;
- include methodology version when available;
- avoid buy/sell instructions;
- state that outputs are analytics and scenario estimates, not financial advice;
- avoid implying certainty or prediction.

## Success Criteria

The experiment is worth extending when at least one of these happens after launch:

- agent-access waitlist leads appear from real users;
- users ask for API keys, webhooks, MCP, SDKs, embeds, or alerts;
- analysts or creators ask for permission to reuse the signal commercially;
- a professional product or AI-agent builder agrees that `EUR 9-19/month` is acceptable for lightweight access to one BTC
  risk metric;
- repeated user conversations show that agent access helps people understand the BTC risk signal.

If none of those happen, keep the public endpoints as-is and do not add agent-specific infrastructure.
