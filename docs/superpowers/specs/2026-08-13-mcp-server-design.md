# MCP Server Design

> Status: approved 2026-08-13. Sub-project S3, tracked by issue #49.

## Goal

Let any MCP client read the Bitcoin risk signal correctly, without reading prose first, and make the
server findable in the public registry.

An article makes a human aware of the product. An MCP server in the registry makes an agent able to
call it. That is the whole reason this sub-project exists.

## Decisions

| Decision | Choice | Why |
| --- | --- | --- |
| Runtime | TypeScript | Around 1,200 MCP servers on npm and an SDK past 150M downloads. That is where clients and their users look. |
| Distribution | npm, installed with `npx`, plus the official MCP Registry | The one-line install everyone recognises in a client config. |
| Location | `mcp/` in this repository | One CI, one tracker, one place to look. A separate repository would be for reuse that does not exist. |
| Transport | stdio only | A hosted service is an explicit non-goal. |
| SDK | `@modelcontextprotocol/server` | The TypeScript SDK v2 retired the monolithic `@modelcontextprotocol/sdk`; use the split package. |

Both runtimes were viable. Python matches the repository's server side, but the server shares no code
with it — it is a thin HTTP client over a public API — so consistency bought nothing, and reach did.

## The Freshness Envelope

The acceptance criterion is that **a model cannot report a risk value without having seen its freshness
state**. There are three ways to attempt that, and only one of them works.

*Prose* — a `check_readiness` tool plus descriptions saying "call this first" — depends on the model
reading and obeying. It usually does. Sometimes it does not.

*Refusal* — return an error when data is degraded, mirroring the API's 503 — destroys the information a
model needs to answer honestly.

*Structure* — every data response carries its freshness inline. The model cannot obtain a number
without its state, not because it was instructed but because the shape does not permit it.

Structure is the choice. Every tool that returns data includes:

```
covered_through: 2026-08-12
data_state:      current | behind | stale
methodology:     crypto-scout-canonical-v1.1
```

`check_readiness` remains a tool because it is useful on its own, but the contract no longer rests on
anyone calling it.

This applies the product's own principle to the integration layer: a value never travels without its
date.

## Degraded Behaviour

The API returns 503 from `/api/readiness` because a numeric endpoint has nowhere to explain itself. A
tool response is structured text a model reads, and it has room. So the server neither refuses nor
answers as though nothing were wrong — it leads with the problem:

```
DATA IS STALE — do not present these values as current.
Last known observation: risk 0.23 (low), covered through 2026-08-09.
Readiness reports: data_fresh false, 3 days old, tolerance 2 days.
```

The model receives everything needed to answer honestly, and no way to answer as if the data were
current.

`data_state` is derived, not passed through: `current` when the observation covers the last completed
UTC day, `behind` when it is older but readiness still reports ready, `stale` when readiness reports
degraded. The middle value matters — the API tolerates two days, and a model should know it is looking
at yesterday-but-one even while everything reports healthy.

## Tools

| Tool | Returns | Parameters |
| --- | --- | --- |
| `check_readiness` | Freshness and validation state, all seven checks | — |
| `get_current_risk` | Latest observation: risk, state, model price, daily low and high | — |
| `get_risk_history` | Historical series | `days`, default 90, maximum 730 |
| `get_risk_levels` | The solved price ladder | — |
| `get_brief` | The daily brief | `locale`, default `en` |

**Two defaults deliberately differ from the HTTP contract.** `/api/risk/history` defaults to 2000 rows
and `/api/brief/latest` returns all seven locales at once. Both are reasonable over HTTP and wrong
here: a tool response lands in a model's context window, and two thousand rows or seven translations
consume it for nothing. Ninety days and one locale, with room to ask for more.

Every tool description states the analytics-not-advice boundary, and every response repeats it once.
A model relaying this output should find it hard to present the number as a trade signal.

## Configuration

`BRB_API_BASE_URL`, defaulting to `https://bitcoinriskbrief.minihub.app`. Tests and local development
point elsewhere; nothing in the test suite may reach production.

No other configuration. No keys, no quotas, no authentication — the API is public and free.

## Errors

Network failure, a non-JSON response, and an unexpected shape are three different situations and are
reported as three different messages. A model that cannot reach the API should say so, not invent a
value or report the absence as a risk reading.

Upstream HTTP status is surfaced rather than swallowed: a 503 from readiness is information, not a
failure to hide.

## Testing And CI

Unit tests against a fake fetch, following the pattern the collector already uses for Telegram — no
network, ever. A test asserts that no test opens a socket.

One CI job builds the package, type-checks, and runs the tests. It is added to the required checks once
it has reported green on `main`, as `image-build` was.

## Publishing

npm under the author's scope, then the official MCP Registry. The README carries the one-line install
and a worked example of the readiness-first sequence.

Documented in `docs/agents/`, alongside the existing agent access pack, and linked from `llms.txt` so
an agent that arrives by crawl finds the installable path.

## Non-Goals

- API keys, quotas, authentication, billing, or usage tracking.
- Any write operation. The server is read-only; the interest form is not exposed and will not be.
- A hosted or remote server. stdio only.
- Computing risk. The server reads the public API and calculates nothing.
- Any change to the backend, the collector, the database, or the methodology.
- Python or a second implementation.

## Acceptance Criteria

- An MCP client connects and reads the current risk state without reading any prose documentation.
- No tool returns a risk value without its covered date, data state, and methodology version.
- A degraded upstream produces a response that leads with the degradation and still carries the last
  known value, clearly labelled.
- Every tool description states the no-advice boundary.
- The test suite passes with sockets disabled.
- The package installs from npm with a single `npx` line, and resolves in the MCP Registry.
