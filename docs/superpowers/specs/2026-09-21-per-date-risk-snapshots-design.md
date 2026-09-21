# Per-Date Risk Snapshots Design

> Status: approved 2026-09-21. Covers sub-project S4b from the
> [Portfolio Transformation Strategy](2026-08-05-portfolio-transformation-strategy.md), tracked by issue #103.
> Builds on [S4a](2026-08-25-methodology-guide-and-addressable-urls-design.md).

## Goal

Let an article, a message or a channel post cite one observation by URL. `/risk/YYYY-MM-DD` shows what the risk was on
a single completed day, in the reader's language, with the content in the server response.

## Why The Backend Renders These, And The Build Does Not

S4a prerenders fourteen documents at build time and never calls the API, which is what stops a live value from being
frozen into a crawlable document. Per-date pages could in principle go the same way: a past date's value is settled,
so baking it in is safe.

Measured before deciding: the prerender costs **6 ms per document**, so 5,914 dates across seven locales would render
in about four minutes. Speed is not the objection.

The objections are the other three:

- **202 MB of build artefacts**, regenerated on every deploy.
- **41,398 sitemap URLs** against the protocol's 50,000-per-file ceiling — room for about two more years.
- **41,398 thin, near-identical pages.** This is the one that matters. Crawl budget spent on near-duplicates dilutes a
  site rather than strengthening it, so prerendering everything works against the goal it is meant to serve.

Rendering on the backend removes all three rather than shrinking them. The data is already there, nothing is built,
nothing is stored, and the sitemap advertises a bounded window while any date still works when linked.

It also leaves S4a's guarantee untouched. The prerender keeps its bright line — it never calls the API — because
per-date pages do not go through it.

## URL Scheme

```
/risk/2026-09-20          en
/ru/risk/2026-09-20  …  /ar/risk/2026-09-20
```

The same shape as S4a: English unprefixed, the other six carrying the locale code. Each page self-references with
`canonical`, lists all seven alternates plus `x-default`, and sets `lang` and `dir` on the document element.

### The SPA And Backend Boundary Moves

`frontend/nginx.conf` proxies only `/api/` to the backend today, so `/risk/2026-09-20` falls through to
`try_files $uri $uri.html =404` and correctly 404s. Two more proxied prefixes are added: `/risk/` and
`/<locale>/risk/`.

Everything else stays static, and the unknown-path contract holds: a date outside the series 404s from the backend,
and any other path still 404s from nginx. `backend/tests/test_agent_surface.py::NginxRouteTests` continues to guard
that.

## HTML Needs Its Own Security Headers

`backend/app/security.py` sets `Content-Security-Policy: default-src 'none'` — correct for JSON and fatal for a page,
which would be forbidden from loading its own styles.

`security_headers_middleware` applies headers with `setdefault`, so a route that sets its own wins. The fix is a
second function beside `build_security_headers` returning the header set for an HTML response, with a policy of
`default-src 'self'` and the same framing, referrer and permissions rules.

**This is not only S4b's problem.** The [S5b design](2026-08-17-consent-first-email-delivery-design.md) puts the
confirmation and unsubscribe pages on the backend and does not mention CSP at all; they would hit the same wall. The
function built here serves both, and S5b's spec gains a pointer to it.

## What The Page Shows

`btc_risk_daily` stores more than the value: `trend_dev`, `vol_regime`, `turnover` and their z-scores are on every
row, so the page can say **why** the risk was what it was rather than only what it was.

1. **The date, first and prominent.** It is the reason the page exists.
2. Risk, band, and the change from the previous day.
3. Model price — HLC3 of that day — and the day's low and high.
4. The three model drivers with direction: raised risk, neutral, lowered risk, derived from the z-scores exactly as
   the home page does it.
5. The localised brief prose for that state. `backend/app/brief.py` composes it from a pair of consecutive
   observations in all seven locales, so this is real text rather than a label.
6. The band boundaries and the methodology version.
7. Links to the live page and the methodology guide, and the analytics-not-advice boundary.

### No Ladder, No Chart

`write_risk_level_snapshot` is called once per import rather than per date, so `risk_level_snapshots` holds only the
most recent ladder. A page cannot show the ladder as it stood on a past day, because that was never stored. Adding
historical ladders is a data-pipeline change and is out of scope.

A chart would need client-side JavaScript and would break the requirement that the content be in the server response.

### The Page Must Never Read As Current

A reader arriving from a 2021 article must not spend a second believing they are looking at today's risk. The date and
its pastness are stated unmistakably, above the value, not beside it.

This is the product's freshness discipline turned around. Everywhere else it says the data might be stale; here it
says the data is deliberately old, and that is the point.

## Caching

`ON CONFLICT (timestamp) DO UPDATE SET` in `collector/collector/db_writer.py` means a re-import rewrites historical
rows. A corrected price changes the risk for that day and, through the rolling windows, for the days after it.

So the tempting `Cache-Control: immutable, max-age=31536000` is wrong. A past date's page is *settled*, not immutable,
and a year-long cache would make a correction unservable for a year.

The existing machinery already answers this. `build_cache_headers` in `backend/app/public_cache.py` emits `ETag`,
`X-Cache-Version` and `Cache-Control` with `stale-while-revalidate`, and the version comes from the validation row
through `fetch_public_data_version`. Per-date pages use the same function with the same version, so any re-import that
changes validation changes the version, changes the ETag, and invalidates every per-date page at once.

No new cache policy, no TTL, no list of pages to purge: the cache key is derived from the data rather than the clock.

## Sitemap

**A ninety-day window**: 90 dates × 7 locales = 630 URLs, plus S4a's fourteen documents and the documentation site.
645 in total, against a 50,000 ceiling.

Ninety is not arbitrary — it is the default `days` for `get_risk_history` in the MCP server, and "recent history"
should mean one number across the product.

**The sitemap is what we advertise, not what works.** A page for a 2021 date opens when linked and serves its content;
a crawler following that link indexes it, which is correct, because a cited observation deserves to be indexed. We
simply do not invite a crawl of 5,914 dates. For the same reason there is no `noindex` on older pages — it would
forbid exactly the case this sub-project exists for.

Like S4a's sitemap, the file stays committed and a Vitest test requires it to agree with the route matrix.

## One Source For The Localised Labels

The backend holds localised brief prose in `brief.py`, but the 121 interface labels live in `frontend/src/locales.ts`,
which is TypeScript the backend cannot read. Rendering a localised page on the backend needs those labels.

Checked before designing around it: **no directory is visible to both images today.** The backend builds with context
`./backend` and copies only `requirements.txt` and `app/`; the frontend builds with context `./frontend` and copies
its own tree. There is nowhere to put a shared file.

The collector already solves this shape: its context is the repository root and it copies `backend/app/` into itself.
The same move works here.

- The shared labels live in `frontend/src/localeStrings.json`, where the frontend imports them directly — Vite handles
  JSON imports natively.
- **The backend's build context changes from `./backend` to `.`**, and its Dockerfile copies that file in. Four lines:
  the CI build command, the compose service, and two `COPY` lines.

The backend reaching into the frontend's tree looks odd until you notice the collector already reaches into the
backend's. The alternative is a second home for translated text, and two copies of one string have drifted in this
repository before.

Only the labels a per-date page needs move into the JSON. `locales.ts` keeps everything else and imports the shared
set, so there is exactly one copy of each string.

## Verification

Existing checks must continue to pass: `./scripts/manage.sh test-python`, `npm test --prefix frontend`,
`npm run build --prefix frontend`, `npm run smoke --prefix frontend`, `./scripts/manage.sh validate`,
`mkdocs build --strict`.

New tests:

- a malformed date — `/risk/2026-13-45`, `/risk/yesterday` — returns 404, not a 500;
- a well-formed date outside the series, before the first row or after the covered end, returns 404;
- a known date renders the value, the band, the three drivers, and the localised prose, in each of the seven locales;
- the page never presents itself as a current observation, asserted on its wording the way the methodology guide is;
- an HTML response carries a CSP that permits its own styles, and **not** `default-src 'none'`;
- `ETag` and `X-Cache-Version` on a per-date page match what the JSON endpoints return for the same import;
- the sitemap contains exactly the ninety-day window across seven locales plus S4a's documents, agreeing with the
  route matrix in both directions;
- nginx proxies `/risk/` and `/<locale>/risk/` and still 404s everything else;
- the shared label file is present inside the built backend image, so the context change is proven rather than
  assumed.

## Acceptance Criteria

- `/risk/YYYY-MM-DD` and `/ru/risk/YYYY-MM-DD` can be pasted into a chat client and open to that observation in that
  language.
- The content is in the server response with JavaScript disabled.
- No page can be mistaken for a current reading.
- A re-import that changes a historical value invalidates the affected pages without a purge list.
- Unknown paths and dates outside the series still return 404.
- The sitemap stays bounded; older dates remain linkable and indexable.
- Each localised label exists in exactly one file.

## Non-Goals

- Prerendering per-date pages, for the reasons above.
- Historical ladder snapshots, which were never stored and would need a pipeline change.
- A chart, which would require client-side rendering.
- Opening up the home page body, which remains separate follow-up work from S4a.
- Any change to the methodology, the bands, or the risk computation.
