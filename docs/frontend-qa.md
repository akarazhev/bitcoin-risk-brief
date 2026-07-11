# Frontend QA

This document records the current frontend production-quality checks for the public Bitcoin Risk Brief page.

## Automated Smoke Matrix

Last local run: 2026-06-29.

Command:

```bash
npm run smoke --prefix frontend
```

The smoke suite starts a production Vite preview build, mocks the public API responses in the browser, and checks:

- desktop and mobile layout render without horizontal overflow;
- risk history and risk levels chart canvases exist, are non-empty, and meet expected container width;
- readiness degraded state is visually distinct from a ready state;
- API failures render an unavailable-data state instead of a fresh risk signal.

| Target | Automated coverage | Result |
| --- | --- | --- |
| Desktop Chrome | Playwright Chromium, 1440 x 1000 | Passed |
| Desktop Firefox | Playwright Firefox, 1366 x 950 | Passed |
| Desktop Safari | Playwright WebKit desktop profile, 1366 x 950 | Passed |
| Mobile Chrome | Playwright Pixel 5 Chromium profile | Passed |
| Mobile Safari | Playwright iPhone 13 WebKit profile | Passed |

Visual inspection was also done on captured desktop and mobile screenshots from the same mocked API data. The checked
screens showed readable chart framing, stacked mobile content, no obvious text overlap, and no visible horizontal
overflow.

## Build Budget

The app lazy-loads the ECharts wrapper from `frontend/src/Chart.tsx` and registers only the bar, line, grid, tooltip,
mark-line, and canvas modules used by the page.

Last local `npm run build --prefix frontend` output:

- `index` JS: 216.21 kB minified, 68.64 kB gzip;
- `Chart` lazy chunk: 557.61 kB minified, 188.87 kB gzip.

`frontend/vite.config.ts` sets `chunkSizeWarningLimit` to `650` kB so this accepted lazy chart chunk does not produce an
ambiguous build warning. The initial app chunk remains well below the default 500 kB threshold.

## Public Hostname QA

Task 8 browser QA recorded on 2026-07-05 for `https://bitcoinriskbrief.minihub.app`.

### Automated Checks

| Check | Result |
| --- | --- |
| `npm test --prefix frontend` | Passed: 2 test files, 17 tests. |
| `npm run build --prefix frontend` | Passed. Output kept `index` at 210.53 kB minified / 67.43 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip. |
| `npm run smoke --prefix frontend` | First sandboxed attempt was blocked by `listen EPERM: operation not permitted 127.0.0.1:4173`; rerun outside the sandbox passed 15 Playwright checks. |

### Public Hostname Browser-Capable QA

Playwright was able to launch outside the sandbox after the first sandboxed browser launch failed with
`MachPortRendezvousServer... Permission denied`. The live public hostname was checked with:

| Profile | Result |
| --- | --- |
| Desktop Chromium, 1440 x 1000 | Passed |
| Mobile Chromium, Pixel 5 profile | Passed |
| Mobile WebKit, iPhone 13 profile | Passed |

Observed live page evidence:

- Page loaded at `https://bitcoinriskbrief.minihub.app/`.
- Latest risk was visible as `Current risk 29% Low`.
- Readiness/freshness was visible as degraded: updated `2026-06-30`, latest date `2026-06-30`, covered end
  `2026-06-30`, and data age `4 days old`.
- Risk history and risk levels charts each rendered two non-empty canvases. The mobile chart canvases were at least
  324 CSS px wide and 360 CSS px tall.
- Waitlist form was visible with the contact input and join button. No production waitlist submission was sent in this
  Task 8 pass.
- EN/RU locale switching worked; Russian risk and waitlist copy became visible after toggling.
- Programmatic mobile overflow checks reported `0` horizontal overflow and no off-viewport visible elements. Saved
  desktop and mobile screenshots showed no obvious text overlap.

Accepted limitations:

- This was browser-capable QA using Playwright profiles, not a physical iOS Safari, Android Chrome, or native branded
  desktop browser pass. Real device/native browser QA remains pending operator execution before treating the launch
  matrix as fully covered.
- The public page was visually checkable, but readiness was degraded because the latest visible data was four days old.
  This QA pass does not clear the separate production data-freshness gate.

## Browser, Accessibility, And Metadata Gap Pass

Recorded on 2026-07-10.

Automated checks run from this workstation:

| Check | Result |
| --- | --- |
| `npm test --prefix frontend` | Passed: 2 test files, 25 tests. |
| `npm run build --prefix frontend` | Passed. Output kept `index` at 216.21 kB minified / 68.64 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip. |
| `npm run smoke --prefix frontend` | First sandboxed attempt was blocked by `listen EPERM: operation not permitted 127.0.0.1:4173`; rerun outside the sandbox passed 25 Playwright checks, including the focused axe scan and keyboard/focus navigation smoke. |

Browser/device status:

- Automated browser-profile coverage passed for the local production build with mocked API responses in Playwright
  Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles.
- This does not replace native/manual evidence on real branded desktop browsers, iOS Safari, Android Chrome, or physical
  devices. Native/manual launch-matrix coverage remains pending unless the operator explicitly accepts that limitation.
- No waitlist POST, deploy, data refresh/import, cache warmup, or Cloudflare/routing change was performed.

Accessibility status:

- `@axe-core/playwright` was added as focused accessibility tooling and integrated into
  `frontend/e2e/frontend-quality.spec.ts`.
- The new Playwright check loads the mocked local production page, waits for the chart canvases to render, runs axe on
  the rendered DOM, and fails on any axe violation.
- The keyboard/focus Playwright smoke uses mocked API routes, tabs through the top actions and waitlist controls,
  verifies reverse focus movement between the submit button and input, submits only to the mocked waitlist route with a
  reserved `.invalid` test address, and verifies the waitlist success status region.
- `npm install --prefix frontend --save-dev @axe-core/playwright` initially failed in the sandbox with DNS
  `ENOTFOUND`; the approved network rerun installed `@axe-core/playwright` 4.12.1 and `axe-core` 4.12.1, with npm audit
  reporting 0 vulnerabilities.
- `npm run smoke --prefix frontend` passed 25 checks outside the sandbox across Playwright Chromium, Firefox, WebKit,
  Pixel 5, and iPhone 13 profiles. The focused axe scan and keyboard/focus smoke passed in each profile.
- This is local automated evidence only. It is not a manual screen-reader/assistive-tech test, manual keyboard pass,
  physical-device/native browser pass, production-host pass, or full accessibility conformance audit.

Manual/source checklist:

| Area | Finding |
| --- | --- |
| Document language | `frontend/index.html` declares `<html lang="en">`. |
| Landmarks and semantic structure | The app renders a `main` landmark, a language `nav`, sections, articles, and a methodology `dl`. |
| Heading order | Source inspection shows one page `h1`, followed by section `h2` headings and brief-card `h3` headings. |
| Form labels and status messaging | The waitlist input has an `aria-label`; submit uses visible text plus `aria-busy` while disabled; submitting/success feedback uses `role="status"` with polite live semantics; error feedback uses `role="alert"` and is linked to the input with `aria-invalid`/`aria-describedby`. |
| Keyboard focus | CSS defines `:focus-visible` outlines for the methodology link, language button, waitlist input, and submit button. Automated Playwright keyboard smoke verifies tab/reverse-tab movement through the public controls with mocked local API routes. A manual tab-order pass was not run. |
| ARIA and live regions | Source includes `aria-label` on language/current-state/methodology/threshold areas, waitlist `role="status"`/`role="alert"` feedback, `role="status"` on chart loading/empty placeholders, and an `aria-live` API error state. |
| Chart accessibility | Charts render as non-empty canvas elements. The local implementation now provides a screen-reader-only current chart summary, recent risk-history table, and risk-threshold price table outside the canvas. Manual screen-reader/assistive-tech behavior remains unverified. |
| Color and contrast | Axe reported no violations for rendered DOM content it can evaluate. Canvas-drawn chart internals remain outside this evidence. |
| Reduced motion and responsive text fit | ECharts animation is disabled and the smoke suite checks horizontal overflow in desktop/mobile profiles. No separate OS reduced-motion or physical-device text-fit pass was run. |

Public metadata status from `GET https://bitcoinriskbrief.minihub.app/` on 2026-07-10:

- HTTP 200 returned public HTML with `title` set to `Bitcoin Risk Brief`.
- Present tags: `charset`, `viewport`, and `title`.
- Missing tags in the returned HTML: meta description, canonical link, Open Graph title/description/image/url, and
  Twitter card/title/description/image metadata.
- The public-host SEO/social metadata gate was therefore inspected but incomplete at that snapshot.

Local SEO/social metadata implementation recorded on 2026-07-10:

- `frontend/index.html` now keeps `title` as `Bitcoin Risk Brief` and adds a concise meta description, canonical URL,
  Open Graph `type`, `title`, `description`, `url`, and `site_name`, plus Twitter `card`, `title`, and `description`.
- `og:image` and `twitter:image` are intentionally omitted because no real production image asset exists in the repo and
  is served publicly.
- `npm test --prefix frontend` passed: 2 test files, 21 tests.
- `npm run build --prefix frontend` passed. Output included `dist/index.html` at 1.36 kB minified / 0.46 kB gzip,
  `index` JS at 211.31 kB minified / 67.61 kB gzip, and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip.
- Source/build inspection of `frontend/index.html` and `frontend/dist/index.html` confirmed the title, description,
  canonical, Open Graph, and Twitter tags.
- No deploy, waitlist POST, data refresh/import, cache warmup, or Cloudflare/routing change was performed in that local
  implementation pass. The later 2026-07-11 production update evidence below verifies the public-host metadata for the
  deployed update.

Public metadata, privacy, and browser-smoke evidence recorded on 2026-07-11:

- Scope/safety: documentation-only evidence note. During this docs update, no deploy, refresh/import, cache warmup,
  waitlist POST, Cloudflare/routing change, production endpoint call, monitor configuration, first traffic, commit, push,
  or tag was performed.
- Production update identity: target commit `86cb2dad889baf24a7464a105bbe2224f75b14ef`; evidence tag
  `predeployment-readiness-reconciled-2026-07-11`.
- Public metadata passed: title, description, canonical URL, Open Graph type/title/description/url/site name, and Twitter
  card/title/description were present. `og:image` and `twitter:image` were absent as expected because no real repo-served
  production image asset exists.
- Desktop/mobile browser smoke passed: H1/readiness/latest date were visible, charts were nonblank, EN/RU toggle worked,
  no horizontal overflow was observed, the privacy/disclaimer note was present, and no waitlist POSTs were observed.
- This evidence does not claim a manual keyboard pass, screen-reader/assistive-tech pass, physical-device/native browser
  pass, full WCAG/accessibility compliance audit, first traffic, or any waitlist submission.

Chart accessibility alternative local implementation recorded on 2026-07-10:

- Scope/safety: frontend code/tests/docs only. No deploy, waitlist POST, data refresh/import, cache warmup,
  Cloudflare/routing change, commit, push, or tag was performed.
- Local implementation: `frontend/src/App.tsx` now renders a semantic screen-reader-only alternative near the chart
  panels: a concise current chart summary with latest date, current risk/state, model price, and daily low/high when
  present; a recent risk-history table limited to the latest six history observations; and a risk-threshold price table
  for the key 35% and 65% bands. `frontend/src/App.css` defines a standard `.sr-only` utility so this data does not add
  visible clutter.
- Chart containers now have accessible names/descriptions tied to the non-canvas summary/table content. The canvas
  charts remain visible for sighted users, and the smoke suite still verifies both canvases are non-empty.
- Focused local tests verify the current risk summary, recent risk-history rows, threshold table content, `.sr-only`
  utility, chart accessible descriptions, Playwright chart-alternative presence, and the axe scan.
- Local verification passed: `npm test --prefix frontend` passed 2 files / 23 tests; `npm run build --prefix frontend`
  passed; `npm run smoke --prefix frontend` was first blocked in the sandbox by `listen EPERM: operation not permitted
  127.0.0.1:4173`, then passed 20 Playwright checks outside the sandbox across Chromium, Firefox, WebKit, Pixel 5, and
  iPhone 13 profiles, including the focused axe scan.
- Limitations: this is local automated/source evidence. It is not a manual screen-reader/assistive-tech pass, manual
  keyboard pass, physical-device/native browser pass, production-host pass, or full WCAG/accessibility compliance audit.

Waitlist live-region and keyboard/focus local implementation recorded on 2026-07-10:

- Scope/safety: frontend code/tests/docs only. No deploy, waitlist POST, data refresh/import, cache warmup,
  Cloudflare/routing change, commit, push, or tag was performed.
- Local implementation: waitlist submitting and success feedback now has polite `role="status"` live-region semantics;
  waitlist errors use `role="alert"`; the input is marked invalid and described by the error text when a submit fails;
  the disabled submit button exposes `aria-busy` while the mocked submit is pending.
- Focused local tests verify the submitting status region, success status region, error alert, input error description,
  disabled/busy submit state, and the absence of browser-storage persistence for waitlist contacts.
- Playwright keyboard/focus smoke uses only mocked API routes, tabs through the top controls and waitlist form, verifies
  reverse focus movement from submit back to input, and submits a reserved `.invalid` test address only to the mocked
  route.
- Local verification passed: `npm test --prefix frontend` passed 2 files / 25 tests; `npm run build --prefix frontend`
  passed; `npm run smoke --prefix frontend` was first blocked in the sandbox by `listen EPERM: operation not permitted
  127.0.0.1:4173`, then passed 25 Playwright checks outside the sandbox across Chromium, Firefox, WebKit, Pixel 5, and
  iPhone 13 profiles.
- Limitations: this is local automated evidence. It is not a manual keyboard pass, screen-reader/assistive-tech pass,
  native/physical-device pass, production-host pass, first-traffic pass, or WCAG conformance claim.

Privacy/terms/disclaimer local implementation recorded on 2026-07-10:

- Scope/safety: frontend code/tests/docs only. No deploy, refresh/import, cache warmup, real waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, private URLs, tokens, `.env` values, raw logs, or PII were recorded.
- Local implementation: the waitlist section now includes a compact native expandable note with English and Russian
  copy. The note states the product is informational research only, not financial advice, investment advice, or a
  trading recommendation; warns users not to enter sensitive information; describes implemented waitlist storage and
  operational log fields; states that no buy, sell, portfolio, or trading action is recommended; states that no paid
  support SLA is provided; and narrowly records that the current app source has no product analytics or tracking-cookie
  code.
- Focused local tests verify the note expands, includes the conservative English copy, localizes to Russian, and has a
  visible focus style for the summary control.
- Local verification passed: `npm test --prefix frontend` passed 2 files / 27 tests; `npm run build --prefix frontend`
  passed with `index` at 218.57 kB minified / 69.43 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip;
  `npm run smoke --prefix frontend` was first blocked in the sandbox by `listen EPERM: operation not permitted
  127.0.0.1:4173`, then passed 25 Playwright checks outside the sandbox across Chromium, Firefox, WebKit, Pixel 5, and
  iPhone 13 profiles, including the focused axe scan and keyboard/focus smoke.
- Limitations: this is local automated/source evidence. It is not production-host verification, legal approval, a full
  privacy policy, a terms-of-service page, a support process, or a promise of deletion/unsubscribe handling.

Overall browser/device/accessibility/metadata/privacy launch-gate status: partial/blocked. Automated Playwright smoke,
the local axe scan, source inspection, local chart data alternative, local waitlist live-region/keyboard smoke, local
SEO/social metadata implementation, local privacy/terms/disclaimer note, and 2026-07-11 public-host metadata/privacy
smoke provide useful evidence. The full native/manual browser-device matrix, manual keyboard/screen-reader/assistive-tech
evidence, production-host accessibility evidence, first traffic, and full WCAG/accessibility compliance remain not
launch-passed.

## Reproducing Locally

Install Playwright browsers once:

```bash
npx --prefix frontend playwright install chromium firefox webkit
```

Run the smoke suite:

```bash
npm run smoke --prefix frontend
```

If a sandbox blocks local port binding or browser launch, rerun in an environment that permits a Vite preview server on
`127.0.0.1:4173`.

## Launch Notes

The automated matrix uses Playwright browser engines and device profiles. Before public launch on the production
hostname, repeat a short manual pass on available physical devices or real branded browsers, especially iOS Safari and
Android Chrome, and record any accepted limitations here.

If Phase 8 localization expansion is implemented before active traffic, repeat the launch pass for every enabled locale:
English, Russian, Spanish, and German. Check long localized labels in buttons, badges, chart labels, waitlist states,
degraded/error states, and mobile layouts. Arabic and Chinese remain disabled until separate RTL, Simplified/Traditional,
platform, and channel requirements are documented and tested.
