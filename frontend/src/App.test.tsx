import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import App from './App'
import type { RiskPoint } from './types'

const chartMocks = vi.hoisted(() => ({
  resize: vi.fn(),
}))

vi.mock('./Chart', () => ({
  default: ({
    option,
    onChartReady,
    opts,
  }: {
    option: { series?: Array<{ name?: string }> }
    onChartReady?: (chart: { resize: typeof chartMocks.resize }) => void
    opts?: { width?: string; height?: string }
  }) => {
    const name = option.series?.[0]?.name?.toLowerCase() ?? 'unknown'
    onChartReady?.({ resize: chartMocks.resize })
    return <div data-testid={`chart-${name}`} data-has-ready={String(typeof onChartReady === 'function')} data-option={JSON.stringify(option)} data-opts={JSON.stringify(opts ?? {})} />
  },
}))

const apiMocks = vi.hoisted(() => ({
  fetchLatestRisk: vi.fn(),
  fetchRiskHistory: vi.fn(),
  fetchRiskLevels: vi.fn(),
  fetchBrief: vi.fn(),
  fetchReadiness: vi.fn(async () => ({
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
  })),
  joinWaitlist: vi.fn(async () => ({ data: { contact_type: 'email', locale: 'en', created: true } })),
}))

vi.mock('./api', () => ({
  fetchReadiness: apiMocks.fetchReadiness,
  fetchLatestRisk: apiMocks.fetchLatestRisk,
  fetchRiskHistory: apiMocks.fetchRiskHistory,
  fetchRiskLevels: apiMocks.fetchRiskLevels,
  fetchBrief: apiMocks.fetchBrief,
  joinWaitlist: apiMocks.joinWaitlist,
}))

function setCompactViewport(matches: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

async function findPriceMetric(title = 'BTC model price input') {
  const titleElement = await screen.findByText(title)
  const metric = titleElement.closest('.price-metric')
  expect(metric).not.toBeNull()
  return within(metric as HTMLElement)
}

async function findModelDriverSection(title = 'Model drivers') {
  const titleElement = await screen.findByRole('heading', { name: title })
  const section = titleElement.closest('.model-drivers')
  expect(section).not.toBeNull()
  return section as HTMLElement
}

async function findModelDrivers(title = 'Model drivers') {
  return within(await findModelDriverSection(title))
}

function getDriverCard(section: HTMLElement, label: string) {
  const labelElement = within(section).getByText(label)
  const card = labelElement.closest('.driver-card')
  expect(card).not.toBeNull()
  return within(card as HTMLElement)
}

function textContentMatcher(text: string) {
  return (_: string, element: Element | null) => element?.textContent === text
}

function deferred<T>() {
  let resolve: (value: T) => void = () => {}
  let reject: (error: Error) => void = () => {}
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve
    reject = promiseReject
  })
  return { promise, resolve, reject }
}

function latestRisk(overrides: Partial<RiskPoint> = {}): RiskPoint {
  return {
    timestamp: '2026-06-26T00:00:00Z',
    price_usd: 100000,
    model_price_usd: 100000,
    low_usd: 96500,
    high_usd: 104250,
    risk: 0.7,
    score: 1,
    risk_state: 'high',
    trend_dev: 1,
    vol_regime: 0.1,
    turnover: null,
    z_trend_dev: 1,
    z_vol_regime: 1,
    z_turnover: null,
    turnover_enabled: false,
    ...overrides,
  }
}

beforeEach(() => {
  document.documentElement.lang = 'en'
  document.documentElement.dir = 'ltr'
  chartMocks.resize.mockClear()
  apiMocks.fetchLatestRisk.mockReset()
  apiMocks.fetchLatestRisk.mockResolvedValue({ data: latestRisk() })
  apiMocks.fetchRiskHistory.mockReset()
  apiMocks.fetchRiskHistory.mockResolvedValue({ data: [
    { timestamp: '2026-06-24T00:00:00Z', price_usd: 98000, risk: 0.52, score: 0.52, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-25T00:00:00Z', price_usd: 99000, risk: 0.63, score: 0.63, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
  ], meta: { returned_points: 2 } })
  apiMocks.fetchRiskLevels.mockReset()
  apiMocks.fetchRiskLevels.mockResolvedValue({ data: [
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.65, price_usd: 118000 },
  ], meta: {
    base: latestRisk(),
    methodology_version: 'crypto-scout-canonical-v1',
    evaluation_date: '2026-06-26',
    current_price: 100000,
    current_risk: 0.7,
    turnover_enabled: false,
    risk_step: 0.025,
    source_row_count: 5827,
  } })
  apiMocks.fetchBrief.mockReset()
  apiMocks.fetchBrief.mockResolvedValue({ data: { snapshot_version: 'v1', as_of: '2026-06-26T00:00:00Z', risk: 0.7, risk_state: 'high', price_usd: 100000, delta_risk: 0.1, sections: { en: { summary: 'Risk elevated', what_changed: 'Changed', avoid_now: 'Avoid', confirm_next: 'Confirm' }, ru: { summary: 'Риск повышен', what_changed: 'Изменилось', avoid_now: 'Избегай', confirm_next: 'Проверь' } } } })
  apiMocks.fetchReadiness.mockClear()
  apiMocks.fetchReadiness.mockResolvedValue({
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
  })
  apiMocks.joinWaitlist.mockClear()
  setCompactViewport(false)
})

test('renders the Bitcoin Risk Brief shell', async () => {
  render(<App />)
  expect(await screen.findByText('Bitcoin Risk Brief')).toBeInTheDocument()
  expect(await screen.findByText('Current risk')).toBeInTheDocument()
})

test('renders a loading state while risk data is pending', () => {
  apiMocks.fetchLatestRisk.mockReturnValueOnce(new Promise(() => {}))

  render(<App />)

  expect(screen.getByText('Loading risk data...')).toBeInTheDocument()
})

test('does not request chart data until core page data is available', () => {
  apiMocks.fetchLatestRisk.mockReturnValueOnce(new Promise(() => {}))

  render(<App />)

  expect(screen.getByText('Loading risk data...')).toBeInTheDocument()
  expect(apiMocks.fetchRiskHistory).not.toHaveBeenCalled()
  expect(apiMocks.fetchRiskLevels).not.toHaveBeenCalled()
})

test('renders main content while chart requests are still pending', async () => {
  const historyRequest = deferred<{ data: []; meta: { returned_points: number } }>()
  const levelsRequest = deferred<{ data: []; meta: { base: object } }>()
  apiMocks.fetchRiskHistory.mockReturnValueOnce(historyRequest.promise)
  apiMocks.fetchRiskLevels.mockReturnValueOnce(levelsRequest.promise)

  render(<App />)

  expect(await screen.findByText('Current risk')).toBeInTheDocument()
  expect(screen.getByText('Risk elevated')).toBeInTheDocument()
  expect(screen.queryByText('Loading risk data...')).not.toBeInTheDocument()
  expect(screen.getAllByText('Loading chart...')).toHaveLength(2)
})

test('chart request failures do not hide the current risk', async () => {
  apiMocks.fetchRiskHistory.mockRejectedValueOnce(new Error('history failed'))
  apiMocks.fetchRiskLevels.mockRejectedValueOnce(new Error('levels failed'))

  render(<App />)

  expect(await screen.findByText('Current risk')).toBeInTheDocument()
  expect(screen.getByText('Risk elevated')).toBeInTheDocument()
  expect(await screen.findByText('Risk history is temporarily unavailable.')).toBeInTheDocument()
  expect(await screen.findByText('Risk levels are temporarily unavailable.')).toBeInTheDocument()
  expect(screen.queryByText('Risk data is temporarily unavailable')).not.toBeInTheDocument()
})

test('renders ready daily data with a report date after the latest completed day', async () => {
  render(<App />)

  expect(apiMocks.fetchReadiness).toHaveBeenCalled()
  expect(await screen.findByText('Report date')).toBeInTheDocument()
  expect(screen.getByText('2026-06-27')).toBeInTheDocument()
  expect(screen.getByText('Readiness ready')).toBeInTheDocument()
  expect(screen.getByText('Validation passed')).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Latest completed day: 2026-06-26'))).toBeInTheDocument()
  expect(screen.getByText('Freshness: current')).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Coverage through: 2026-06-26'))).toBeInTheDocument()
  expect(screen.queryByText('Current through')).not.toBeInTheDocument()
  expect(screen.queryByText('Fresh: 1 day old')).not.toBeInTheDocument()
  expect(screen.queryByText('Data is 1 day old')).not.toBeInTheDocument()
})

test('rolls the report date across UTC year boundaries', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: latestRisk({ timestamp: '2026-12-31T00:00:00Z' }),
  })
  apiMocks.fetchBrief.mockResolvedValueOnce({
    data: {
      snapshot_version: 'v1',
      as_of: '2026-12-31T00:00:00Z',
      risk: 0.7,
      risk_state: 'high',
      price_usd: 100000,
      delta_risk: 0.1,
      sections: {
        en: {
          summary: 'Risk elevated',
          what_changed: 'Changed',
          avoid_now: 'Avoid',
          confirm_next: 'Confirm',
        },
      },
    },
  })
  apiMocks.fetchReadiness.mockResolvedValueOnce({
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
      latest_date: '2026-12-31',
      covered_end: '2026-12-31',
      data_age_days: 1,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5827,
      methodology_version: 'crypto-scout-canonical-v1',
    },
  })

  render(<App />)

  expect(await screen.findByText('Report date')).toBeInTheDocument()
  expect(screen.getByText('2027-01-01')).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Latest completed day: 2026-12-31'))).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Coverage through: 2026-12-31'))).toBeInTheDocument()
})

test('does not render a report date when readiness is degraded despite fresh data', async () => {
  apiMocks.fetchReadiness.mockResolvedValueOnce({
    status: 'degraded',
    checks: {
      risk_data_available: true,
      validation_available: true,
      risk_range_ok: true,
      validation_has_rows: true,
      latest_matches_validation_end: false,
      source_is_canonical: true,
      data_fresh: true,
    },
    data: {
      latest_date: '2026-06-26',
      covered_end: '2026-06-25',
      data_age_days: 1,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5827,
      methodology_version: 'crypto-scout-canonical-v1',
    },
  })

  render(<App />)

  expect(await screen.findByText('Current risk')).toBeInTheDocument()
  expect(screen.queryByText('Report date')).not.toBeInTheDocument()
  expect(screen.queryByText('2026-06-27')).not.toBeInTheDocument()
  expect(screen.getByText('Readiness degraded')).toBeInTheDocument()
  expect(screen.getByText('Validation needs attention')).toBeInTheDocument()

  const methodology = within(screen.getByRole('region', { name: 'Methodology' }))
  expect(methodology.getByText('crypto-scout-canonical-v1')).toBeInTheDocument()
  expect(methodology.getByText('Latest completed day')).toBeInTheDocument()
  expect(methodology.getByText('2026-06-26')).toBeInTheDocument()
  expect(methodology.getByText('Coverage through')).toBeInTheDocument()
  expect(methodology.getByText('2026-06-25')).toBeInTheDocument()
})

test('renders degraded readiness copy without hiding the latest risk', async () => {
  apiMocks.fetchReadiness.mockResolvedValueOnce({
    status: 'degraded',
    checks: {
      risk_data_available: true,
      validation_available: true,
      risk_range_ok: false,
      validation_has_rows: true,
      latest_matches_validation_end: false,
      source_is_canonical: true,
      data_fresh: false,
    },
    data: {
      latest_date: '2026-06-20',
      covered_end: '2026-06-19',
      data_age_days: 6,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5827,
      methodology_version: 'crypto-scout-canonical-v1',
    },
  })

  render(<App />)

  expect(await screen.findByText('Current risk')).toBeInTheDocument()
  expect(screen.getByText('Readiness degraded')).toBeInTheDocument()
  expect(screen.getByText('Validation needs attention')).toBeInTheDocument()
  expect(screen.queryByText('Report date')).not.toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Latest completed day: 2026-06-20'))).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Stale: 6 days behind'))).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Coverage through: 2026-06-19'))).toBeInTheDocument()
  expect(screen.queryByText('Data is 6 days old')).not.toBeInTheDocument()
})

test('renders a distinct API unavailable state when risk data cannot load', async () => {
  apiMocks.fetchLatestRisk.mockRejectedValueOnce(new Error('Request failed: 500'))

  render(<App />)

  expect(await screen.findByText('Risk data is temporarily unavailable')).toBeInTheDocument()
  expect(screen.getByText('Request failed: 500')).toBeInTheDocument()
  expect(screen.queryByText('No collected data yet. Run the collector backfill to populate TimescaleDB.')).not.toBeInTheDocument()
})

test('renders explicit empty chart states when history or levels have no rows', async () => {
  apiMocks.fetchRiskHistory.mockResolvedValueOnce({ data: [], meta: { returned_points: 0 } })
  apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [], meta: { base: {} } })

  render(<App />)

  expect(await screen.findByText('Risk history is unavailable until observations are loaded.')).toBeInTheDocument()
  expect(screen.getByText('Risk levels are unavailable until the latest model input is ready.')).toBeInTheDocument()
  expect(screen.queryByTestId('chart-risk')).not.toBeInTheDocument()
  expect(screen.queryByTestId('chart-price')).not.toBeInTheDocument()
})

test('renders methodology reference, public data-source copy, and no-advice disclaimer', async () => {
  render(<App />)

  expect(await screen.findByText('Methodology')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /methodology/i })).toHaveAttribute('href', '#methodology')

  const methodology = within(screen.getByRole('region', { name: 'Methodology' }))
  expect(methodology.getByText('The public signal uses the canonical BTC risk model and validated daily Bitcoin market data.')).toBeInTheDocument()
  expect(methodology.getByText('crypto-scout-canonical-v1')).toBeInTheDocument()
  expect(methodology.getByText('Data source')).toBeInTheDocument()

  const sourceLink = methodology.getByRole('link', { name: 'CoinMarketCap' })
  expect(sourceLink).toHaveAttribute('href', 'https://coinmarketcap.com/currencies/bitcoin/historical-data/')
  expect(sourceLink).toHaveAttribute('target', '_blank')
  expect(sourceLink).toHaveAttribute('rel', 'noreferrer')

  expect(methodology.queryByText(/CSV/i)).not.toBeInTheDocument()
  expect(methodology.queryByText(/import/i)).not.toBeInTheDocument()
  expect(screen.getByText('Risk levels are scenario outputs for research. They are not financial advice or trading instructions.')).toBeInTheDocument()
})

test('localizes accessible chart labels and unavailable methodology metadata', async () => {
  apiMocks.fetchReadiness.mockResolvedValueOnce({
    status: 'degraded',
    checks: {
      risk_data_available: true,
      validation_available: true,
      risk_range_ok: true,
      validation_has_rows: true,
      latest_matches_validation_end: false,
      source_is_canonical: true,
      data_fresh: false,
    },
    data: {
      latest_date: null,
      covered_end: null,
      data_age_days: null,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5827,
      methodology_version: null,
    },
  })

  render(<App />)

  const languageSelector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(languageSelector, { target: { value: 'ru' } })

  expect(await screen.findByLabelText('Текущий риск')).toBeInTheDocument()
  expect(screen.getByLabelText('Порог риска')).toBeInTheDocument()
  expect(screen.queryByText('unknown')).not.toBeInTheDocument()
  expect(screen.getAllByText('недоступно')).toHaveLength(3)
})

test('renders an expandable privacy terms and disclaimer note near the waitlist', async () => {
  render(<App />)

  const summary = await screen.findByText('Privacy, terms, and disclaimer')
  const note = summary.closest('details')
  expect(note).not.toBeNull()
  const noteElement = note as HTMLDetailsElement

  expect(noteElement).not.toHaveAttribute('open')

  fireEvent.click(summary)

  expect(noteElement).toHaveAttribute('open')
  expect(noteElement).toHaveTextContent('informational research only')
  expect(noteElement).toHaveTextContent('not financial advice, investment advice, or a trading recommendation')
  expect(noteElement).toHaveTextContent('stores the contact you submit, a normalized copy, contact type, locale, source, status, and timestamps')
  expect(noteElement).toHaveTextContent('Operational logs may include request method, path, status, client key, Cloudflare ray ID, cache status, and timing')
  expect(noteElement).toHaveTextContent('Do not enter sensitive information')
  expect(noteElement).toHaveTextContent('No buy, sell, portfolio, or trading action is recommended')
  expect(noteElement).toHaveTextContent('no paid support SLA is provided')
  expect(noteElement).toHaveTextContent('does not include product analytics or tracking-cookie code')
})

test('localizes the privacy terms and disclaimer note', async () => {
  render(<App />)

  const languageSelector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(languageSelector, { target: { value: 'ru' } })

  const summary = await screen.findByText('Приватность, условия и дисклеймер')
  const note = summary.closest('details')
  expect(note).not.toBeNull()
  const noteElement = note as HTMLDetailsElement
  fireEvent.click(summary)

  expect(noteElement).toHaveAttribute('open')
  expect(noteElement).toHaveTextContent('только информационная аналитика')
  expect(noteElement).toHaveTextContent('платный SLA поддержки не предоставляется')
})

test('submits waitlist contacts to the backend API', async () => {
  render(<App />)

  fireEvent.change(await screen.findByPlaceholderText('email or @telegram'), { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'en', source: 'landing' })
  })
})

test('announces waitlist submitting and success states politely', async () => {
  let resolveWaitlist: (value: { data: { contact_type: string; locale: string; created: boolean } }) => void = () => {}
  apiMocks.joinWaitlist.mockReturnValueOnce(new Promise((resolve) => {
    resolveWaitlist = resolve
  }))
  render(<App />)

  fireEvent.change(await screen.findByPlaceholderText('email or @telegram'), { target: { value: '@status_smoke' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  const submittingStatus = await screen.findByRole('status')
  expect(submittingStatus).toHaveTextContent('Saving...')
  expect(submittingStatus).toHaveAttribute('aria-live', 'polite')
  expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled()
  expect(screen.getByRole('button', { name: /saving/i })).toHaveAttribute('aria-busy', 'true')

  resolveWaitlist({ data: { contact_type: 'email', locale: 'en', created: true } })

  await waitFor(() => {
    expect(screen.getByRole('status')).toHaveTextContent('Saved. You are on the Bitcoin Risk Brief waitlist.')
  })
  expect(screen.getByRole('button', { name: /join waitlist/i })).toHaveAttribute('aria-busy', 'false')
})

test('announces waitlist errors assertively and links them to the input', async () => {
  apiMocks.joinWaitlist.mockRejectedValueOnce(new Error('invalid contact'))
  render(<App />)

  const input = await screen.findByPlaceholderText('email or @telegram')
  fireEvent.change(input, { target: { value: 'not-a-contact' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Enter a valid email or Telegram handle.')
  expect(input).toHaveAttribute('aria-invalid', 'true')
  expect(input).toHaveAccessibleDescription('Enter a valid email or Telegram handle.')
})


test('does not persist waitlist contacts in browser storage', async () => {
  const setItemSpy = vi.spyOn(Storage.prototype, 'setItem')
  render(<App />)

  fireEvent.change(await screen.findByPlaceholderText('email or @telegram'), { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'en', source: 'landing' })
  })
  expect(setItemSpy).not.toHaveBeenCalled()
  setItemSpy.mockRestore()
})

test('labels risk delta as a contextual risk change metric', async () => {
  render(<App />)

  expect(await screen.findByText('Risk change')).toBeInTheDocument()
  expect(screen.getByText('vs previous observation')).toBeInTheDocument()
  expect(screen.queryByText('Delta')).not.toBeInTheDocument()
})

test('renders model price, low, and high when latest risk includes OHLC fields', async () => {
  render(<App />)

  const priceMetric = await findPriceMetric()

  expect(priceMetric.getByText('Model price')).toBeInTheDocument()
  expect(priceMetric.getByText('Low')).toBeInTheDocument()
  expect(priceMetric.getByText('High')).toBeInTheDocument()
  expect(priceMetric.getByText('$100,000')).toBeInTheDocument()
  expect(priceMetric.getByText('$96,500')).toBeInTheDocument()
  expect(priceMetric.getByText('$104,250')).toBeInTheDocument()
})

test('renders localized model drivers from latest risk component directions', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: latestRisk({
      turnover: -10.1,
      z_trend_dev: 0.8,
      z_vol_regime: -0.7,
      z_turnover: 0.05,
      turnover_enabled: true,
    }),
  })

  render(<App />)

  const driverSection = await findModelDriverSection()
  const drivers = within(driverSection)
  const trendDriver = getDriverCard(driverSection, 'Trend')
  const volatilityDriver = getDriverCard(driverSection, 'Volatility')
  const activityDriver = getDriverCard(driverSection, 'Activity')

  expect(drivers.getByText('Plain-language direction of each model component from the latest validated daily data.')).toBeInTheDocument()
  expect(trendDriver.getByText('Price vs long-term baseline')).toBeInTheDocument()
  expect(trendDriver.getByText('Raises risk')).toBeInTheDocument()
  expect(volatilityDriver.getByText('Recent price swings')).toBeInTheDocument()
  expect(volatilityDriver.getByText('Lowers risk')).toBeInTheDocument()
  expect(activityDriver.getByText('Trading activity adjusted for market size')).toBeInTheDocument()
  expect(activityDriver.getByText('Neutral')).toBeInTheDocument()
  expect(drivers.queryByText('-10.1')).not.toBeInTheDocument()
  expect(drivers.queryByText('0.05')).not.toBeInTheDocument()

  const languageSelector = screen.getByRole('combobox', { name: /select language/i })
  fireEvent.change(languageSelector, { target: { value: 'ru' } })

  const ruDriverSection = await findModelDriverSection('Драйверы модели')
  const ruDrivers = within(ruDriverSection)
  const ruTrendDriver = getDriverCard(ruDriverSection, 'Тренд')
  const ruVolatilityDriver = getDriverCard(ruDriverSection, 'Волатильность')
  const ruActivityDriver = getDriverCard(ruDriverSection, 'Активность')

  expect(ruDrivers.getByText('Понятное направление каждого компонента модели по последним валидированным дневным данным.')).toBeInTheDocument()
  expect(ruTrendDriver.getByText('Цена относительно долгосрочной базы')).toBeInTheDocument()
  expect(ruTrendDriver.getByText('Повышает риск')).toBeInTheDocument()
  expect(ruVolatilityDriver.getByText('Недавние колебания цены')).toBeInTheDocument()
  expect(ruVolatilityDriver.getByText('Снижает риск')).toBeInTheDocument()
  expect(ruActivityDriver.getByText('Торговая активность с учетом размера рынка')).toBeInTheDocument()
  expect(ruActivityDriver.getByText('Нейтрально')).toBeInTheDocument()
})

test('marks trading activity unavailable when turnover is disabled', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: latestRisk({
      turnover: null,
      z_trend_dev: 0.1,
      z_vol_regime: 0.1,
      z_turnover: null,
      turnover_enabled: false,
    }),
  })

  render(<App />)

  const drivers = await findModelDrivers()

  expect(drivers.getByText('Activity')).toBeInTheDocument()
  expect(drivers.getByText('Unavailable')).toBeInTheDocument()
  expect(drivers.getByText('Market-adjusted activity unavailable')).toBeInTheDocument()
  expect(drivers.queryByText('0')).not.toBeInTheDocument()
  expect(drivers.queryByText('0%')).not.toBeInTheDocument()
})

test('hides low and high labels when the matching OHLCV values are missing', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: {
      timestamp: '2026-06-26T00:00:00Z',
      price_usd: 100000,
      model_price_usd: 100000,
      low_usd: null,
      high_usd: null,
      risk: 0.7,
      score: 1,
      risk_state: 'high',
      trend_dev: 1,
      vol_regime: 0.1,
      turnover: null,
      z_trend_dev: 1,
      z_vol_regime: 1,
      z_turnover: null,
      turnover_enabled: false,
    },
  })

  render(<App />)

  const priceMetric = await findPriceMetric()

  expect(priceMetric.getByText('Model price')).toBeInTheDocument()
  expect(priceMetric.getByText('$100,000')).toBeInTheDocument()
  expect(priceMetric.queryByText('Low')).not.toBeInTheDocument()
  expect(priceMetric.queryByText('High')).not.toBeInTheDocument()
})

test('preserves English and Russian labels for the price input group', async () => {
  render(<App />)

  let priceMetric = await findPriceMetric()

  expect(priceMetric.getByText('Model price')).toBeInTheDocument()
  expect(priceMetric.getByText('Low')).toBeInTheDocument()
  expect(priceMetric.getByText('High')).toBeInTheDocument()

  const languageSelector = screen.getByRole('combobox', { name: /select language/i })
  fireEvent.change(languageSelector, { target: { value: 'ru' } })

  priceMetric = await findPriceMetric('Цена BTC в модели')

  expect(priceMetric.getByText('Цена модели')).toBeInTheDocument()
  expect(priceMetric.getByText('Мин.')).toBeInTheDocument()
  expect(priceMetric.getByText('Макс.')).toBeInTheDocument()
})

test('defines a stable responsive grid for the price input group', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.price-input-grid')
  expect(css).toContain('grid-template-columns: repeat(3, minmax(0, 1fr))')
  expect(css).toContain('@media (max-width: 560px)')
  expect(css).toContain('.price-input-grid')
})

test('defines a stable responsive layout for model drivers', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.model-drivers')
  expect(css).toContain('grid-template-columns: minmax(220px, 0.65fr) minmax(0, 1fr)')
  expect(css).toContain('.driver-list')
  expect(css).toContain('grid-template-columns: repeat(3, minmax(0, 1fr))')
  expect(css).toContain('.driver-card.unavailable strong')
  expect(css).toContain('@media (max-width: 900px)')
})

test('places the waitlist call to action before the charts', async () => {
  render(<App />)

  const waitlistTitle = await screen.findByText('Get the daily signal')
  const riskHistoryTitle = await screen.findByText('Risk history')

  expect(waitlistTitle.compareDocumentPosition(riskHistoryTitle) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
})

test('renders the compact Minihub bottom panel after the charts', async () => {
  render(<App />)

  const supportLink = await screen.findByRole('link', { name: 'support@minihub.app' })
  const footer = supportLink.closest('footer.bottom-panel')
  expect(footer).not.toBeNull()

  const bottomPanel = within(footer as HTMLElement)
  expect(supportLink).toHaveAttribute('href', 'mailto:support@minihub.app')
  expect(bottomPanel.getByText(textContentMatcher(`© ${new Date().getFullYear()} Minihub`))).toBeInTheDocument()

  const websiteLink = bottomPanel.getByRole('link', { name: /https:\/\/minihub\.app/i })
  expect(websiteLink).toHaveAttribute('href', 'https://minihub.app')
  expect(websiteLink).toHaveAttribute('target', '_blank')
  expect(websiteLink).toHaveAttribute('rel', 'noreferrer')

  const riskLevelsTitle = screen.getByRole('heading', { name: 'Risk levels' })
  expect(riskLevelsTitle.compareDocumentPosition(footer as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
})

test('uses compact chart options on narrow viewports', async () => {
  setCompactViewport(true)
  render(<App />)

  const riskChart = await screen.findByTestId('chart-risk')
  const riskOption = JSON.parse(riskChart.dataset.option ?? '{}')

  expect(riskOption.animation).toBe(false)
  expect(riskOption.grid.left).toBeLessThanOrEqual(38)
  expect(riskOption.xAxis.data[0]).toBe('06-24')
  expect(riskOption.xAxis.axisLabel.hideOverlap).toBe(true)
  expect(riskOption.series[0].markLine.label.show).toBe(false)
})

test('resizes charts after ECharts reports readiness', async () => {
  render(<App />)

  expect(await screen.findByTestId('chart-risk')).toHaveAttribute('data-has-ready', 'true')
  expect(await screen.findByTestId('chart-price')).toHaveAttribute('data-has-ready', 'true')
  await waitFor(() => {
    expect(chartMocks.resize).toHaveBeenCalledWith({ width: 'auto', height: 'auto' })
  })
})

test('lets ECharts derive chart dimensions from the rendered container', async () => {
  render(<App />)

  expect(await screen.findByTestId('chart-risk')).toHaveAttribute('data-opts', JSON.stringify({ width: 'auto', height: 'auto' }))
  expect(await screen.findByTestId('chart-price')).toHaveAttribute('data-opts', JSON.stringify({ width: 'auto', height: 'auto' }))
})

test('uses accessible risk threshold labels outside the chart canvas', async () => {
  render(<App />)

  const visibleThresholds = within(await screen.findByLabelText('Risk threshold'))
  expect(visibleThresholds.getByText('Low / Neutral')).toBeInTheDocument()
  expect(visibleThresholds.getByText('Neutral / High')).toBeInTheDocument()
  expect(await screen.findByText(textContentMatcher('Low / Neutral near $82,000'))).toBeInTheDocument()
  expect(await screen.findByText(textContentMatcher('Neutral / High near $118,000'))).toBeInTheDocument()

  const riskChart = await screen.findByTestId('chart-risk')
  const riskOption = JSON.parse(riskChart.dataset.option ?? '{}')
  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(riskOption.animation).toBe(false)
  expect(priceOption.animation).toBe(false)
  expect(riskOption.series[0].markLine.label.show).toBe(false)
  expect(riskOption.series[0].markLine.data).toEqual([{ yAxis: 0.35 }, { yAxis: 0.65 }])
})

test('marks the current risk on levels chart using levels snapshot metadata', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({ data: latestRisk({ risk: 0.2 }) })
  apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.65, price_usd: 118000 },
  ], meta: {
    base: latestRisk({ risk: 0.7 }),
    methodology_version: 'crypto-scout-canonical-v1',
    evaluation_date: '2026-06-26',
    current_price: 100000,
    current_risk: 0.7,
    turnover_enabled: false,
    risk_step: 0.025,
    source_row_count: 5827,
  } })

  render(<App />)

  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(priceOption.series[0].markLine).toMatchObject({
    symbol: 'none',
    silent: true,
    data: [{ xAxis: '65%' }],
    lineStyle: { color: '#f2b84b', width: 2 },
  })
  expect(priceOption.series[0].markLine.label).toMatchObject({
    show: true,
    formatter: 'Current risk: 70%',
  })
})

test('renders screen-reader chart data alternatives for current risk, recent history, and thresholds', async () => {
  render(<App />)

  const riskChart = await screen.findByRole('img', { name: 'Risk history' })
  expect(riskChart).toHaveAccessibleDescription(/Latest observation 2026-06-26: current risk is 70% \(High\)/)
  expect(riskChart).toHaveAccessibleDescription(/model price is \$100,000/)
  expect(riskChart).toHaveAccessibleDescription(/latest daily low \$96,500 and high \$104,250/)

  const historyTable = screen.getByRole('table', { name: 'Recent risk history table' })
  expect(within(historyTable).getByText('2026-06-24')).toBeInTheDocument()
  expect(within(historyTable).getByText('52%')).toBeInTheDocument()
  expect(within(historyTable).getByText('$98,000')).toBeInTheDocument()
  expect(within(historyTable).getAllByText('Neutral')).toHaveLength(2)

  const levelsChart = screen.getByRole('img', { name: 'Risk levels' })
  expect(levelsChart).toHaveAccessibleDescription('The table lists the key risk threshold prices used with the risk levels chart.')

  const thresholdTable = screen.getByRole('table', { name: 'Risk threshold price table' })
  expect(within(thresholdTable).getByText('35%')).toBeInTheDocument()
  expect(within(thresholdTable).getByText('65%')).toBeInTheDocument()
  expect(within(thresholdTable).getByText('$82,000')).toBeInTheDocument()
  expect(within(thresholdTable).getByText('$118,000')).toBeInTheDocument()
})

test('defines visible keyboard focus states for interactive controls', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.language-select select:focus-visible')
  expect(css).toContain('.lead-form input:focus-visible')
  expect(css).toContain('.lead-form button:focus-visible')
  expect(css).toContain('.privacy-note summary:focus-visible')
  expect(css).toContain('.bottom-panel-link:focus-visible')
})

test('defines compact bottom panel layout and RTL styles', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.bottom-panel')
  expect(css).toContain('border-top: 1px solid #2c3037')
  expect(css).toContain('[dir="rtl"] .bottom-panel')
})

test('offers all issue 28 languages and applies document language metadata', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  expect(within(selector).getAllByRole('option').map((option) => option.getAttribute('value'))).toEqual([
    'en',
    'ru',
    'zh',
    'de',
    'fr',
    'es',
    'ar',
  ])

  fireEvent.change(selector, { target: { value: 'de' } })
  expect(await screen.findByText('Aktuelles Risiko')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'de')
  expect(document.documentElement).toHaveAttribute('dir', 'ltr')

  fireEvent.change(selector, { target: { value: 'fr' } })
  expect(await screen.findByText('Risque actuel')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'fr')

  fireEvent.change(selector, { target: { value: 'es' } })
  expect(await screen.findByText('Riesgo actual')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'es')

  fireEvent.change(selector, { target: { value: 'zh' } })
  expect(await screen.findByText('当前风险')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'zh-CN')

  fireEvent.change(selector, { target: { value: 'ar' } })
  expect(await screen.findByText('المخاطر الحالية')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ar')
  expect(document.documentElement).toHaveAttribute('dir', 'rtl')
})

test('isolates visible Arabic numeric, date, and currency values as LTR', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(selector, { target: { value: 'ar' } })

  const metrics = document.querySelector('.metrics-strip')
  expect(metrics).not.toBeNull()
  const metricValues = within(metrics as HTMLElement).getAllByText((_, element) => element?.classList.contains('numeric-value') ?? false)
  expect(metricValues.map((element) => element.textContent)).toEqual(expect.arrayContaining([
    '$100,000',
    '$96,500',
    '$104,250',
    '2026-06-26',
    '+10%',
  ]))
  for (const value of metricValues) {
    expect(value).toHaveAttribute('dir', 'ltr')
  }

  const thresholdValues = document.querySelectorAll('.threshold-callouts .numeric-value')
  expect(Array.from(thresholdValues).map((element) => element.textContent)).toEqual(expect.arrayContaining([
    '$82,000',
    '$118,000',
  ]))
  for (const value of thresholdValues) {
    expect(value).toHaveAttribute('dir', 'ltr')
  }

  const trustValues = document.querySelectorAll('.trust-panel .numeric-value')
  expect(Array.from(trustValues).map((element) => element.textContent)).toEqual(expect.arrayContaining([
    '2026-06-26',
  ]))
  for (const value of trustValues) {
    expect(value).toHaveAttribute('dir', 'ltr')
  }
})

test('isolates visible Arabic degraded freshness counts as LTR', async () => {
  apiMocks.fetchReadiness.mockResolvedValueOnce({
    status: 'degraded',
    checks: {
      risk_data_available: true,
      validation_available: true,
      risk_range_ok: false,
      validation_has_rows: true,
      latest_matches_validation_end: false,
      source_is_canonical: true,
      data_fresh: false,
    },
    data: {
      latest_date: '2026-06-20',
      covered_end: '2026-06-19',
      data_age_days: 6,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5827,
      methodology_version: 'crypto-scout-canonical-v1',
    },
  })

  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(selector, { target: { value: 'ar' } })

  const freshnessValues = document.querySelectorAll('.freshness-metric .numeric-value')
  expect(Array.from(freshnessValues).map((element) => element.textContent)).toEqual(expect.arrayContaining([
    '2026-06-26',
    '2026-06-20',
    '2026-06-19',
    '6',
  ]))
  for (const value of freshnessValues) {
    expect(value).toHaveAttribute('dir', 'ltr')
  }
})

test('submits the selected expanded locale to the waitlist API', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(selector, { target: { value: 'fr' } })
  fireEvent.change(await screen.findByPlaceholderText('email ou @telegram'), { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /rejoindre la liste/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'fr', source: 'landing' })
  })
})

test('keeps Arabic waitlist contact entry LTR and submits locale metadata', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(selector, { target: { value: 'ar' } })

  const input = await screen.findByPlaceholderText('email أو @telegram')
  expect(input).toHaveAttribute('dir', 'ltr')

  fireEvent.change(input, { target: { value: '@arabic_test' } })
  fireEvent.click(screen.getByRole('button', { name: /انضم/ }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: '@arabic_test', locale: 'ar', source: 'landing' })
  })
})

test('falls back to the English generated brief when selected locale is absent from an old snapshot', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(selector, { target: { value: 'de' } })

  expect(await screen.findByText('Heutiger Brief')).toBeInTheDocument()
  expect(screen.getByText('Risk elevated')).toBeInTheDocument()
})

test('defines RTL layout rules for Arabic locale', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('[dir="rtl"] .topbar')
  expect(css).toContain('[dir="rtl"] .top-actions')
  expect(css).toContain('[dir="rtl"] .chart-visual')
})

test('defines a standard screen-reader-only utility for hidden chart data', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.sr-only')
  expect(css).toContain('position: absolute')
  expect(css).toContain('width: 1px')
  expect(css).toContain('clip: rect(0, 0, 0, 0)')
})
