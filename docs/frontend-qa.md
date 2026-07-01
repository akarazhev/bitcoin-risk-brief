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
