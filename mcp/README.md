# Bitcoin Risk Brief MCP Server

Run with `npx -y @akarazhev/bitcoin-risk-brief-mcp`.

The server is read-only and provides five tools:

- `check_readiness`
- `get_current_risk`
- `get_risk_history` with `days` (default `90`, maximum `730`)
- `get_risk_levels`
- `get_brief` with `locale` (`en`, `ru`, `zh`, `de`, `fr`, `es`, or `ar`; default `en`)

Each data tool fetches `/api/readiness` before its own endpoint and includes `covered_through`, `data_state`, and
`methodology` in its response. For example, `get_current_risk` first reads readiness and then reads
`/api/risk/latest`, so the returned risk is always paired with its freshness state.

Bitcoin Risk Brief provides analytics and research context, not financial advice, a price forecast, or a trade signal.
