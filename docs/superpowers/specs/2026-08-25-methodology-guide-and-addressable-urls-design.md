# Methodology Guide And Addressable URLs Design

> Status: approved 2026-08-25. Covers sub-project S4a from the
> [Portfolio Transformation Strategy](2026-08-05-portfolio-transformation-strategy.md), tracked by issue #42.

## Goal

Give a reader enough public explanation to judge the signal, and give every page an address that can be pasted into a
message, cited by an article, and read by a crawler without running JavaScript.

## Scope

Issue #42 bundles a content deliverable with an infrastructure one, and the infrastructure half is dominated by
per-date snapshots at `/risk/YYYY-MM-DD` — 5,887 dates as of 2026-08-24, growing daily.

**S4a, this design:** the interpretation guide at `/methodology`, locale-addressable URLs, and the build-time
rendering that puts content in the server response.

**S4b, deferred:** per-date snapshot URLs. They exist so an article can cite one observation, and no article exists
yet. The routing and rendering foundation built here is what S4b will reuse, which is why splitting costs nothing.

Out of scope entirely: any change to `crypto-scout-canonical-v1.1`, new indicators, or a methodology v2.

## URL Scheme

```
/                  en   home       canonical=self, x-default
/ru/  /zh/  /de/  /fr/  /es/  /ar/  localised homes
/methodology       en   guide
/ru/methodology  …  /ar/methodology
```

Fourteen documents. The path carries the short locale code (`zh`); the full BCP-47 tag (`zh-CN`) goes in `hreflang`.
Both come from `localeOptions` in `frontend/src/locales.ts`, which already carries `lang` and `dir` per locale — so
Arabic gets `dir="rtl"` on the document element rather than by emulation.

Every document self-references with `canonical` and lists all seven alternates plus `x-default` pointing at the English
one.

`/en/` and `/en/methodology` are not generated and do not 404: two nginx `return 301` rules send them to `/` and
`/methodology`. The URL is plausible enough that someone will type it, and one canonical address per language matters
more than purism.

### The Language Switcher Becomes Navigation

Choosing German on `/ru/methodology` navigates to `/de/methodology`. That is the point of the exercise: a link carries
its language. Today locale is resolved from `navigator.languages` at runtime and appears nowhere in the URL, so a link
sent to a colleague opens in *their* language.

### Automatic Language Detection Is Kept, But Inverted

`/` prerenders in English. On the client, if the visitor has never chosen a language manually, it navigates to their
locale's home.

The order matters. A server-side redirect by `Accept-Language` would send crawlers somewhere unpredictable and make the
English page unreachable for a reader who wants it. Doing it after hydration means crawlers and JavaScript-less clients
see English and stay there. A manual choice is remembered and disables the automatic hop permanently, so someone who
deliberately opened the English version is not bounced away from it.

## Rendering

New modules, one responsibility each:

| File | Responsibility |
| --- | --- |
| `frontend/src/routes.ts` | The route × locale matrix. One source of truth, read by the app and by the build. |
| `frontend/src/Methodology.tsx` | The guide itself. |
| `frontend/src/head.ts` | Pure function: `(route, locale) → title, description, canonical, hreflang[], JSON-LD`. |
| `frontend/scripts/prerender.mjs` | Build step: walks the matrix and writes the files. |

`vite build` emits `dist/index.html` carrying the hashed asset URLs. `prerender.mjs` takes that as the shell and, for
each pair, calls `renderToString`, replaces the head and the contents of `#root`, and writes `dist/methodology.html`,
`dist/ru/index.html`, `dist/ru/methodology.html`, and so on. The English home overwrites `dist/index.html` itself.

`react-dom` is already a dependency, so this adds none. It needs no browser, and the output is a deterministic function
of the source rather than of whatever a headless page happened to finish painting.

### Three Things That Do Not Survive Server Rendering Today

- `App.tsx` reads `navigator.languages` during initialisation. Locale becomes an input; the automatic hop moves into a
  client-only effect. This work is required by the URL scheme regardless of how rendering is done.
- The ECharts chart and the Turnstile widget touch the DOM. The server renders their containers at the same
  dimensions; mounting stays on the client.
- `main.tsx` moves from `createRoot` to `hydrateRoot`, because every served document is now prerendered.

### The Prerender Never Calls The API

Not "we are careful about which numbers reach the HTML" — the build has no data to bake in. It renders the same
waiting state a visitor sees in the first millisecond, and the live value arrives after hydration.

This is the reason a prerendered home is safe at all. The homepage shows today's risk; freezing `risk 0.22 low` into a
crawlable document would have search engines repeating it for months, contradicting the one property this product is
built around. It is also why S4b's per-date URLs are the right citation target and the homepage is not: a past date's
value never changes.

The constraint is enforced, not documented: the prerender runs in a test with outbound sockets blocked and
`globalThis.fetch` replaced by a throwing stub. If the build ever starts fetching, the suite fails.

## The Guide

### Where The Line With The Documentation Site Falls

`docs.bitcoinriskbrief.minihub.app` already publishes the complete technical reference at
[`product/risk-methodology.md`](../../product/risk-methodology.md): input rows, feature construction, robust z-scores,
score weights, risk value, risk states, risk levels, interpretation limits.

**The in-product guide publishes exactly two numbers and one string:** the `0.30` and `0.70` band boundaries, and the
methodology version. All three are already visible in the interface, and all three are pinned by a test against
`backend/app/risk.py`, where `LOW_RISK_THRESHOLD`, `HIGH_RISK_THRESHOLD` and `METHODOLOGY_VERSION` live.

Everything else numeric — the weights, the 1460-day z-score window, the 365-day minimum, the clip at 6.0, the 365-day
EMA, the 30-day volatility window — stays in the reference and is reached by link. Two copies of the same number drift,
and a test spanning seven locales would police that badly.

### Structure

Ordered by the questions a reader actually asks:

1. **What this number is** — the scale, and more importantly what it is not: not a probability, not a price target,
   not an instruction to act.
2. **Why today reads "low"** — the two boundaries and the version. The worked example fills in with the live value
   after hydration.
3. **What goes into it** — the four inputs in words: deviation from the long-run trend, recent volatility, turnover,
   and the point that each is compared against its own history rather than an absolute level. Formulas and weights by
   link.
4. **The price shown is not a quote** — HLC3 of the last completed daily candle. The most common misunderstanding, and
   the one that already forced a wording change in the Telegram post.
5. **The level ladder is not a forecast** — solved backwards with the non-price inputs held fixed. It answers "at what
   price would the model say X", not "the price will be X".
6. **When not to trust today's number** — freshness, readiness, and why the API returns 503 rather than a stale figure.
7. **What the model cannot see** — regime change, no on-chain data, no news, and daily granularity that cannot observe
   an intraday reversal.
8. **What happens when the methodology changes** — the version policy.

### Translation

Roughly a thousand words of prose in seven languages. This is the real cost of the sub-project, and unlike UI labels
the text carries statements about limitations.

All seven get the full guide. **The six non-English versions carry a visible notice that they are translations and
that the English version is authoritative.** Issue #42 permits either full localisation or an explicit honest
fallback; this is both. It does not pretend to a review that cannot happen — the author can verify English and Russian
by eye and cannot verify Chinese or Arabic — and it does not drop the seven-locale promise for convenience.

## Serving

### nginx

`location /` changes from `try_files $uri =404` to `try_files $uri $uri.html $uri/ =404`. That one directive covers all
four shapes: `/` takes `index.html`, `/ru/` the directory index, `/methodology` the file `methodology.html` with no
redirect and no trailing slash, `/ru/methodology` likewise.

An unknown path still finds no file, no `.html` and no directory, and still gets a genuine 404 — so
`test_unknown_paths_are_not_rewritten_to_the_app_shell` and `test_fallthrough_location_returns_404` keep protecting
that contract instead of being loosened to accommodate this change.

Issue #42 proposed extending an allowlist of SPA routes. Generating real files removes the need for one: there is
nothing to enumerate, and no list to forget to update when S4b adds per-date URLs.

The `image-build` CI job already runs `nginx -t` inside the built image, so the configuration is validated on every
pull request.

### Sitemap

`frontend/public/sitemap.xml` currently holds two hand-written URLs. It becomes fifteen — fourteen documents plus the
documentation site — and is generated by the same build step from `routes.ts`. A test asserts agreement in both
directions: every route in the matrix appears, and nothing appears that is not in the matrix.

`frontend/public/llms.txt` gains a line for `/methodology`, since it is a new citable surface for an agent.
`robots.txt` is unchanged.

## Verification

Existing checks must continue to pass: `./scripts/manage.sh test-python`, `npm test --prefix frontend`,
`npm run build --prefix frontend`, `npm run smoke --prefix frontend`, `./scripts/manage.sh validate`,
`mkdocs build --strict`.

New tests:

- `head.ts` is a pure function, so it is asserted exactly: self-referencing canonical, seven `hreflang` entries plus
  `x-default`, and the correct `lang` and `dir` per locale including `rtl` for Arabic;
- all fourteen documents are generated, each with a localised `<title>` and, on the six non-English ones, the
  translation notice;
- the prerender completes with outbound sockets blocked and `globalThis.fetch` throwing;
- the boundaries and version stated in the guide match `backend/app/risk.py`, asserted from Python, following the
  precedent in `backend/tests/test_agent_surface.py` which already reads `frontend/public/llms.txt`;
- `NginxRouteTests` covers `/methodology`, `/ru/methodology`, the `/en/` redirects, and an unknown path still 404;
- hydration produces no mismatch between the server and client trees;
- the sitemap and the route matrix agree in both directions;
- a localised route is added to the Playwright smoke run, which already applies axe checks, covering the issue's
  keyboard-accessibility criterion.

`documentHead.test.ts` and `structuredData.test.ts` currently read the source `frontend/index.html`, which is a
template. They move to the generated documents — what is actually served. The assertion gets stronger rather than
merely relocated.

**Deliberately not written:** a test asserting that no generated file contains something shaped like a risk value. It
would chase a symptom, and unreliably. The network guard catches the cause: there is nowhere for the data to come from.

## Acceptance Criteria

- `/methodology` and `/ru/methodology` can be pasted into a chat client and open directly to that content, in that
  language.
- The content of any of the fourteen documents is present in the server response with JavaScript disabled.
- No live risk value appears in any generated document.
- A reader can explain why `0.25` is classified as low and how the next band is determined.
- A reader can distinguish the model price from a live spot price, and a level scenario from a forecast.
- The boundaries and methodology version shown in the guide match the running backend.
- Unknown paths still return 404.
- All seven locales render, Arabic right-to-left, with the translation notice on the six non-English versions.

## Non-Goals

- Per-date snapshot URLs, which are S4b.
- Server-side language redirection.
- Publishing weights, z-score windows, or clipping values in the product; those stay in the reference.
- Any claim of audited performance or predictive accuracy.
- Changing the methodology, its version, or its inputs.
