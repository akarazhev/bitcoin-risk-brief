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

- `index` JS: 210.53 kB minified, 67.43 kB gzip;
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
| `npm test --prefix frontend` | Passed: 2 test files, 21 tests. |
| `npm run build --prefix frontend` | Passed. Output kept `index` at 211.31 kB minified / 67.61 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip. |
| `npm run smoke --prefix frontend` | First sandboxed attempt was blocked by `listen EPERM: operation not permitted 127.0.0.1:4173`; rerun outside the sandbox passed 20 Playwright checks, including the focused axe scan. |

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
- `npm install --prefix frontend --save-dev @axe-core/playwright` initially failed in the sandbox with DNS
  `ENOTFOUND`; the approved network rerun installed `@axe-core/playwright` 4.12.1 and `axe-core` 4.12.1, with npm audit
  reporting 0 vulnerabilities.
- `npm run smoke --prefix frontend` passed 20 checks outside the sandbox across Playwright Chromium, Firefox, WebKit,
  Pixel 5, and iPhone 13 profiles. The focused axe scan passed in each profile with no reported violations.
- This is local automated evidence only. It is not a screen-reader test, manual keyboard pass, physical-device/native
  browser pass, production-host pass, or full accessibility conformance audit.

Manual/source checklist:

| Area | Finding |
| --- | --- |
| Document language | `frontend/index.html` declares `<html lang="en">`. |
| Landmarks and semantic structure | The app renders a `main` landmark, a language `nav`, sections, articles, and a methodology `dl`. |
| Heading order | Source inspection shows one page `h1`, followed by section `h2` headings and brief-card `h3` headings. |
| Form labels and status messaging | The waitlist input has an `aria-label`; the submit button has visible text. Waitlist success/error text is visible but is not a live region, so announcement timing remains unverified. |
| Keyboard focus | CSS defines `:focus-visible` outlines for the methodology link, language button, waitlist input, and submit button. A manual tab-order pass was not run. |
| ARIA and live regions | Source includes `aria-label` on language/current-state/methodology/threshold areas, `role="status"` on chart loading/empty placeholders, and an `aria-live` API error state. |
| Chart accessibility | Charts render as non-empty canvas elements and nearby text exposes the current risk, threshold callouts, and model inputs, but there is no screen-reader-equivalent chart data table. |
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
- No deploy, waitlist POST, data refresh/import, cache warmup, or Cloudflare/routing change was performed. Production
  public-host metadata verification remains pending until the frontend is deployed and checked on
  `https://bitcoinriskbrief.minihub.app/`.

Overall browser/device/accessibility/metadata launch-gate status: partial/blocked. Automated Playwright smoke, the local
axe scan, source inspection, and local SEO/social metadata implementation provide useful evidence. The full
native/manual browser-device matrix, manual keyboard/screen-reader evidence, chart screen-reader alternative evidence,
and public-host SEO/social metadata verification are still not launch-passed.

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
