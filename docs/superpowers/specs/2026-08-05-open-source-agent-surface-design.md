# Open Source And Agent Surface Design

> Status: approved 2026-08-05. Covers sub-projects S1 and S2 from the
> [Portfolio Transformation Strategy](2026-08-05-portfolio-transformation-strategy.md).

## Goal

Make the repository public under Apache-2.0, restructure documentation so engineering quality is the first thing a
reader meets, publish a technical documentation site, and give AI agents everything they need to discover and call the
product correctly.

## Outcome

Three artifacts served from one repository:

| Artifact | Address | Audience |
| --- | --- | --- |
| Public repository | `github.com/akarazhev/bitcoin-risk-brief` | Technical clients, contributors |
| Product | `bitcoinriskbrief.minihub.app` | Users and, newly, agents |
| Documentation site | `docs.bitcoinriskbrief.minihub.app` | Developers, agents, article references |

## Architecture Impact

Runtime services are unchanged. The compose topology, database schema, collector behaviour, and risk methodology are
untouched. No new dependency enters any production container. MkDocs runs only in CI.

The only backend change is the `FastAPI` constructor. The only nginx change is route handling. The only frontend
change is a new static asset directory plus structured data in `index.html`.

## Documentation Restructure

Nothing is deleted. Files move and gain a navigation structure.

```
docs/
  index.md                docs site landing page
  product/                what it is, methodology, how to read the score
  engineering/            architecture, data-pipeline, api-reference, testing, security
  agents/                 agent-access-pack, openapi          ← core of S2
  operations/             readiness, evidence-log, roadmap, runbooks, packet templates
  archive/                superpowers specs and plans, unchanged
```

Every page under `operations/` opens with one standard admonition:

> **Operational log.** These entries record what was verified and when. They are not claims about product capability.

This keeps the evidence discipline visible as a strength while removing it from the first impression. `mkdocs.yml`
owns navigation order.

`AGENTS.md` stays at the repository root and gains a pointer to the new documentation layout, since agents working in
the repository read it before anything else.

## README Shape

Target is roughly 120 lines, down from 223.

1. Title, one-sentence description, badges for CI, licence, and live status
2. Screenshot of the first viewport
3. Live link plus a `curl` example with a real response body
4. What it does — five bullets
5. What makes it different — freshness and readiness visibility, determinism, scenario ladder
6. **For AI agents** — `llms.txt`, OpenAPI, Agent Access Pack
7. Architecture — existing service table plus a mermaid diagram
8. Quick start — unchanged
9. Links into the documentation site
10. Disclaimer and licence

The present sixty-line Current Status block collapses to a single line linking
`docs/operations/production-readiness.md`.

## Agent Surface

### Static Files

`frontend/public/` does not exist yet and is created. Vite copies its contents into `dist`, nginx serves them, and
Cloudflare caches them.

| File | Purpose |
| --- | --- |
| `robots.txt` | Crawl permissions, sitemap reference, explicit rules for agent user-agents |
| `sitemap.xml` | Product routes plus documentation site entry points |
| `llms.txt` | Short map: what the product is, endpoints, readiness-first rule, no-advice framing, doc links |
| `llms-full.txt` | Methodology and API contract inline, for agents that fetch one file |

These files describe the dataset, the methodology, and endpoint semantics. They never embed a current risk value:
without server-side rendering any inlined number would go stale, and agents are directed to the API for live values.

### OpenAPI

The schema already exists and is unreachable. Exposing it is a constructor change:

```python
app = FastAPI(
    title="Bitcoin Risk Brief API",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)
```

The existing nginx `/api/` proxy then serves it without modification.

Interactive documentation is deliberately omitted. The default Swagger UI loads scripts from a CDN, which the strict
CSP blocks, and the CSP is worth more than the page. A self-hosted viewer is deferred to S4.

The schema is then enriched with endpoint descriptions, response examples drawn from real payloads, tags, and a
`servers` block, so that a generated client is usable without reading prose.

### Route Handling

`try_files $uri $uri/ /index.html` currently returns HTTP 200 for every path. With exactly one route today, the fix is
an explicit allowlist of SPA routes; everything else returns a genuine 404. S4 extends the list when `/methodology`
and `/risk/YYYY-MM-DD` arrive.

### Structured Data

`index.html` gains JSON-LD describing `Dataset` and `WebSite`. Static, versioned, and free of daily values for the
same reason as the agent text files.

### Agent Access Pack

`docs/agents/agent-access-pack.md` implements the existing
[Agent Access And Risk-Signal Licensing Demand Test Design](2026-06-30-agent-access-demand-test-design.md):
the readiness-first call sequence, every endpoint with worked examples, cache semantics covering `ETag` and
`X-Cache-Version`, rate limits, the analytics-not-advice framing, and an explicit list of what an agent must not
present the output as.

## Documentation Site

MkDocs Material, built and deployed by a new CI job to GitHub Pages, served at
`docs.bitcoinriskbrief.minihub.app` via a Cloudflare DNS record.

`mkdocs build --strict` fails the build on broken internal links, which makes the restructure safe to iterate on. The
site is a separate origin, so it neither touches the product CSP nor adds load to the production host.

The site also serves its own `llms.txt`, giving agents stable canonical URLs for the technical reference.

## Repository Furniture

`LICENSE` (Apache-2.0), `CONTRIBUTING.md`, `SECURITY.md`. Repository visibility flipped to public, Discussions
enabled, description refreshed, and topics extended with `ai-agents`, `openapi`, `llms-txt`, `mcp`, and
`open-source`. Social preview image set.

## Verification

Existing checks must continue to pass:

- `./scripts/manage.sh test-python`
- `npm test --prefix frontend`
- `npm run build --prefix frontend`
- `./scripts/manage.sh validate`

New checks:

- agent files are present and well-formed in the built `dist`;
- `GET /api/openapi.json` responds and lists all seven public routes;
- nginx returns 404 for an unknown path and 200 for each allowlisted SPA route;
- `mkdocs build --strict` succeeds;
- the secret scan from the strategy document is re-run immediately before visibility is flipped.

## Work Order

One constraint shapes the order: GitHub Pages on the free tier requires a public repository, so the documentation
site cannot precede the flip.

Steps 1 to 4 are branch work. Steps 5 to 7 are publication and land together.

1. Re-run the secret scan; add `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`
2. Restructure `docs/`, write `mkdocs.yml`, verify locally with `mkdocs serve`
3. Rewrite `README.md`
4. Build the agent surface: `frontend/public/`, FastAPI constructor, nginx routes, JSON-LD
5. **Flip the repository to public**, enable Pages, add the `docs.` DNS record
6. Deploy the product through the USB kit — agent files reach production only after this operator step
7. Update GitHub metadata, enable Discussions, set topics and social preview

Step 6 is operator work and gates public verification of the agent surface.

Because everything lands in one flip, the branch must be complete and reviewed before step 5 begins. Release timing
is determined by branch readiness.

## Freshness And Validation Page

`docs/engineering/data-pipeline.md` gains, or is joined by, a page that explains the freshness and validation contract
in its own terms: what `/api/readiness` asserts, how `data_fresh` and `data_age_days` are derived, what
`latest_matches_validation_end` rules out, why staleness returns 503 rather than stale data, how `X-Cache-Version`
binds cached payloads to a validation row, and what an import provenance packet records.

This page is called out separately from the general documentation restructure because it carries the most weight per
line in the whole set. Freshness and validation handling is the strongest engineering in the product and currently the
least visible: a visitor sees a risk chart, and the machinery that decides whether that chart can be trusted is
invisible. This page is where a technical reader finds it.

## Non-Goals

- Interactive API documentation, which waits for S4 and a self-hosted viewer.
- Any change to risk methodology, database schema, or collector behaviour.
- The MCP server, which is S3.
- The in-product methodology page, which is S4.
- Relaxing the Content-Security-Policy for any reason.

## Acceptance Criteria

- A reader with no private context can clone, run, and understand the stack from the public README.
- An agent can fetch `llms.txt`, follow it to the OpenAPI schema and Agent Access Pack, and make a correct
  readiness-first call sequence without human help.
- Requesting a nonexistent path returns 404 rather than the application shell.
- Every operations document remains published, navigable, and clearly labelled as an operational log.
- `docs.bitcoinriskbrief.minihub.app` serves the technical reference with working internal links.
- No secret, credential, private hostname, or personal contact detail is present in the public repository.
