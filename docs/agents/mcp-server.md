# MCP Server

Bitcoin Risk Brief provides a read-only MCP server over stdio. It reads the public API; it does not compute risk,
modify data, expose the interest form, or require an API key.

## Run it

Use this command in an MCP client configuration:

```bash
npx -y @akarazhev/bitcoin-risk-brief-mcp
```

The server reads `BRB_API_BASE_URL` when set. Its default is `https://bitcoinriskbrief.minihub.app`.

## Tools

| Tool | Parameters | Response |
| --- | --- | --- |
| `check_readiness` | Empty input schema | Readiness and validation state. |
| `get_current_risk` | Empty input schema | Latest risk observation, state, model price, and daily range. |
| `get_risk_history` | `days`: integer, default `90`, minimum `1`, maximum `730` | Historical risk observations. |
| `get_risk_levels` | Empty input schema | Solved price ladder for risk levels. |
| `get_brief` | `locale`: `en`, `ru`, `zh`, `de`, `fr`, `es`, or `ar`; default `en` | Daily brief in the selected locale. |

## Freshness Is Inline

`check_readiness` is available for an explicit readiness check. Every data tool also calls `/api/readiness` before its
own public endpoint, derives a freshness envelope, and includes it in the returned text. A model therefore receives
the observation together with:

```text
covered_through: YYYY-MM-DD | unknown
data_state:      current | behind | stale
methodology:     methodology version | unknown
```

This structure prevents a risk observation from travelling without its covered date, freshness state, and methodology
version. `current` means the data covers the last completed UTC day. `behind` means readiness is still `ready`, but the
covered day is older. `stale` means readiness is degraded. The server derives these states from readiness rather than
assuming that a returned row is current.

## Degraded Data

When `/api/readiness` is degraded, a data tool still returns the last stored data so its condition can be reported
honestly. Its response begins with:

```text
DATA IS STALE — do not present these values as current.
```

It then includes the last known observation where applicable, readiness diagnostics such as `data_fresh`,
`data_age_days`, and `max_age_days`, and the same freshness envelope. Do not relabel a stale or behind observation as
current.

## Interpretation Boundary

Bitcoin Risk Brief provides analytics and research context, not financial advice, investment advice, a price forecast,
or a trading recommendation. Scenario prices from `get_risk_levels` are model outputs, not predictions, targets, or
support levels. The server is read-only and does not make recommendations or collect interest-form submissions.
