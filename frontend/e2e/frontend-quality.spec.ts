import { expect, test, type Locator, type Page, type Route } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const latestRisk = {
  data: {
    timestamp: '2026-06-26T00:00:00Z',
    price_usd: 100000,
    model_price_usd: 100000,
    low_usd: 96500,
    high_usd: 104250,
    risk: 0.7,
    score: 0.7,
    risk_state: 'high',
    trend_dev: 1,
    vol_regime: 0.1,
    turnover: null,
    z_trend_dev: 1,
    z_vol_regime: 1,
    z_turnover: null,
    turnover_enabled: false,
  },
}

const riskHistory = {
  data: [
    { timestamp: '2026-06-20T00:00:00Z', price_usd: 94000, risk: 0.42, score: 0.42, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-21T00:00:00Z', price_usd: 96000, risk: 0.5, score: 0.5, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-22T00:00:00Z', price_usd: 98500, risk: 0.58, score: 0.58, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-23T00:00:00Z', price_usd: 100500, risk: 0.66, score: 0.66, risk_state: 'high', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-24T00:00:00Z', price_usd: 101500, risk: 0.69, score: 0.69, risk_state: 'high', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-25T00:00:00Z', price_usd: 100000, risk: 0.7, score: 0.7, risk_state: 'high', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
  ],
  meta: { returned_points: 6 },
}

const riskLevels = {
  data: [
    { risk: 0.2, price_usd: 72000 },
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.5, price_usd: 97000 },
    { risk: 0.65, price_usd: 118000 },
    { risk: 0.8, price_usd: 143000 },
  ],
  meta: { base: latestRisk.data },
}

const brief = {
  data: {
    snapshot_version: 'v1',
    as_of: '2026-06-26T00:00:00Z',
    risk: 0.7,
    risk_state: 'high',
    price_usd: 100000,
    delta_risk: 0.1,
    sections: {
      en: {
        summary: 'Risk is elevated while price remains near the high-risk band.',
        what_changed: 'The latest observation moved closer to the upper threshold.',
        avoid_now: 'Avoid treating the signal as a short-term trade command.',
        confirm_next: 'Confirm that the next daily import passes readiness.',
      },
      ru: {
        summary: 'Risk elevated.',
        what_changed: 'Latest observation changed.',
        avoid_now: 'Avoid using this as a trading command.',
        confirm_next: 'Confirm the next import.',
      },
    },
  },
}

const readyReadiness = {
  status: 'ready',
  checks: {
    risk_data_available: true,
    validation_available: true,
    risk_range_ok: true,
    validation_has_rows: true,
    latest_matches_validation_end: true,
    source_is_canonical: true,
    data_fresh: true,
  },
  data: {
    latest_date: '2026-06-26',
    covered_end: '2026-06-26',
    data_age_days: 1,
    max_age_days: 2,
    source: 'coinmarketcap_csv',
    row_count: 5827,
    methodology_version: 'crypto-scout-canonical-v1',
  },
}

const degradedReadiness = {
  status: 'degraded',
  checks: {
    ...readyReadiness.checks,
    risk_range_ok: false,
    latest_matches_validation_end: false,
    data_fresh: false,
  },
  data: {
    ...readyReadiness.data,
    latest_date: '2026-06-20',
    covered_end: '2026-06-19',
    data_age_days: 6,
  },
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function mockApi(
  page: Page,
  readiness: typeof readyReadiness | typeof degradedReadiness = readyReadiness,
  waitlistHandler?: (route: Route) => Promise<void>,
) {
  await page.route('**/api/risk/latest', (route) => fulfillJson(route, latestRisk))
  await page.route('**/api/risk/history?limit=2000', (route) => fulfillJson(route, riskHistory))
  await page.route('**/api/risk/levels', (route) => fulfillJson(route, riskLevels))
  await page.route('**/api/brief/latest', (route) => fulfillJson(route, brief))
  await page.route('**/api/readiness', (route) => fulfillJson(route, readiness, readiness.status === 'ready' ? 200 : 503))
  await page.route('**/api/waitlist', waitlistHandler ?? ((route) => fulfillJson(route, { data: { contact_type: 'email', locale: 'en', created: true } })))
}

async function expectNoHorizontalOverflow(page: Page) {
  await expect.poll(async () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
}

async function expectNonBlankCharts(page: Page, minimumCssWidth: number) {
  const canvases = page.locator('.chart-panel canvas')
  await expect(canvases).toHaveCount(2)

  for (let index = 0; index < 2; index += 1) {
    const canvas = canvases.nth(index)
    await expect.poll(async () => canvas.evaluate((node, expectedWidth) => {
      const canvasNode = node as HTMLCanvasElement
      const rect = canvasNode.getBoundingClientRect()
      const context = canvasNode.getContext('2d')
      if (!context || rect.width < expectedWidth || rect.height < 260) {
        return false
      }

      const pixels = context.getImageData(0, 0, canvasNode.width, canvasNode.height).data
      for (let pixel = 3; pixel < pixels.length; pixel += 80) {
        if (pixels[pixel] !== 0) return true
      }
      return false
    }, minimumCssWidth)).toBe(true)
  }
}

async function isFocused(locator: Locator) {
  return locator.evaluate((node) => node === document.activeElement)
}

test('renders desktop and mobile layouts with non-empty chart canvases', async ({ page }, testInfo) => {
  await mockApi(page)

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Bitcoin Risk Brief' })).toBeVisible()
  await expect(page.getByText('Readiness ready')).toBeVisible()
  const currentState = page.locator('.metrics-strip')
  await expect(currentState.getByText('Model price', { exact: true })).toBeVisible()
  await expect(currentState.getByText('Low', { exact: true })).toBeVisible()
  await expect(currentState.getByText('High', { exact: true })).toBeVisible()
  await expect(currentState.getByText('$96,500')).toBeVisible()
  await expect(currentState.getByText('$104,250')).toBeVisible()
  await expect(page.getByText('Low / Neutral near $82,000')).toBeVisible()
  await expect(page.getByText('Neutral / High near $118,000')).toBeVisible()
  await expect(page.getByRole('img', { name: 'Risk history' })).toHaveAttribute('aria-describedby', /risk-history-chart-summary/)
  await expect(page.getByRole('table', { name: 'Recent risk history table' })).toContainText('2026-06-25')
  await expect(page.getByRole('table', { name: 'Risk threshold price table' })).toContainText('$118,000')
  await expectNoHorizontalOverflow(page)
  await expectNonBlankCharts(page, testInfo.project.name.startsWith('mobile') ? 280 : 440)
})

test('keeps Arabic RTL layout numeric data isolated and readable', async ({ page }, testInfo) => {
  await mockApi(page, degradedReadiness)

  await page.goto('/')
  await page.getByRole('combobox', { name: /select language/i }).selectOption('ar')

  await expect(page.locator('html')).toHaveAttribute('lang', 'ar')
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl')
  await expect(page.locator('.numeric-value', { hasText: '$100,000' }).first()).toHaveAttribute('dir', 'ltr')
  await expect(page.locator('.numeric-value', { hasText: '70%' }).first()).toHaveAttribute('dir', 'ltr')
  await expect(page.locator('.numeric-value', { hasText: '2026-06-26' }).first()).toHaveAttribute('dir', 'ltr')
  await expect(page.locator('.freshness-metric .numeric-value', { hasText: /^6$/ })).toHaveAttribute('dir', 'ltr')
  await expect(page.locator('.trust-panel .numeric-value', { hasText: '2026-06-20' })).toHaveAttribute('dir', 'ltr')
  await expect(page.locator('.trust-panel .numeric-value', { hasText: '2026-06-19' })).toHaveAttribute('dir', 'ltr')
  await expect(page.locator('.threshold-callouts .numeric-value', { hasText: '$118,000' })).toHaveAttribute('dir', 'ltr')
  await expectNoHorizontalOverflow(page)
  await expectNonBlankCharts(page, testInfo.project.name.startsWith('mobile') ? 280 : 440)
})

test('passes a focused axe accessibility scan on the rendered page', async ({ page }, testInfo) => {
  await mockApi(page)

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Bitcoin Risk Brief' })).toBeVisible()
  await expectNonBlankCharts(page, testInfo.project.name.startsWith('mobile') ? 280 : 440)

  const accessibilityScanResults = await new AxeBuilder({ page }).analyze()
  const violations = accessibilityScanResults.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    description: violation.description,
    nodes: violation.nodes.map((node) => node.target),
  }))

  expect(violations).toEqual([])
})

test('supports keyboard focus navigation through public controls with mocked waitlist submit', async ({ page, browserName }) => {
  const waitlistPayloads: unknown[] = []
  const pressTab = () => page.keyboard.press(browserName === 'webkit' ? 'Alt+Tab' : 'Tab')
  const pressShiftTab = () => page.keyboard.press(browserName === 'webkit' ? 'Alt+Shift+Tab' : 'Shift+Tab')
  await mockApi(page, readyReadiness, async (route) => {
    expect(route.request().method()).toBe('POST')
    waitlistPayloads.push(route.request().postDataJSON())
    await fulfillJson(route, { data: { contact_type: 'email', locale: 'en', created: true } })
  })

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Bitcoin Risk Brief' })).toBeVisible()
  const methodologyLink = page.getByRole('link', { name: /methodology/i })
  const languageSelector = page.getByRole('combobox', { name: /select language/i })
  const waitlistInput = page.getByLabel('email or @telegram')
  const submitButton = page.getByRole('button', { name: /join waitlist/i })

  await pressTab()
  if (await isFocused(methodologyLink)) {
    await pressTab()
  }
  await expect(languageSelector).toBeFocused()
  await pressTab()
  await expect(waitlistInput).toBeFocused()
  await page.keyboard.type('keyboard@example.invalid')
  await pressTab()
  await expect(submitButton).toBeFocused()
  await pressShiftTab()
  await expect(waitlistInput).toBeFocused()
  await pressTab()
  await expect(submitButton).toBeFocused()
  await page.keyboard.press('Enter')

  await expect(page.locator('#waitlist-status')).toHaveText('Saved. You are on the Bitcoin Risk Brief waitlist.')
  expect(waitlistPayloads).toEqual([{ contact: 'keyboard@example.invalid', locale: 'en', source: 'landing' }])
})

test('renders degraded readiness as a visible degraded state', async ({ page }) => {
  await mockApi(page, degradedReadiness)

  await page.goto('/')

  await expect(page.getByText('Readiness degraded')).toBeVisible()
  await expect(page.getByText('Validation needs attention')).toBeVisible()
  await expect(page.getByText('Stale: 6 days behind')).toBeVisible()
  await expect(page.getByText('Readiness ready')).toHaveCount(0)
})

test('renders API failures as unavailable data, not a fresh signal', async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/risk/latest', (route) => fulfillJson(route, { detail: 'backend unavailable' }, 500))

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Risk data is temporarily unavailable' })).toBeVisible()
  await expect(page.getByText('Request failed: 500')).toBeVisible()
  await expect(page.getByText('Current risk')).toHaveCount(0)
})
