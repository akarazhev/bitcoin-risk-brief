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
      methodology_version: 'crypto-scout-canonical-v1.1',
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

function getLanguageTrigger() {
  const trigger = document.querySelector<HTMLButtonElement>('.language-trigger')
  expect(trigger).not.toBeNull()
  return trigger as HTMLButtonElement
}

async function openLanguageMenu() {
  const trigger = await waitFor(() => getLanguageTrigger())
  fireEvent.click(trigger)
  return screen.findByRole('listbox')
}

async function selectLanguage(optionName: RegExp | string) {
  const listbox = await openLanguageMenu()
  fireEvent.click(within(listbox).getByRole('option', { name: optionName }))
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
    { risk: 0.30, price_usd: 78000 },
    { risk: 0.70, price_usd: 125000 },
  ], meta: {
    base: latestRisk(),
    methodology_version: 'crypto-scout-canonical-v1.1',
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
      methodology_version: 'crypto-scout-canonical-v1.1',
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
      methodology_version: 'crypto-scout-canonical-v1.1',
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
      methodology_version: 'crypto-scout-canonical-v1.1',
    },
  })

  render(<App />)

  expect(await screen.findByText('Current risk')).toBeInTheDocument()
  expect(screen.queryByText('Report date')).not.toBeInTheDocument()
  expect(screen.queryByText('2026-06-27')).not.toBeInTheDocument()
  expect(screen.getByText('Readiness degraded')).toBeInTheDocument()
  expect(screen.getByText('Validation needs attention')).toBeInTheDocument()

  const methodology = within(screen.getByRole('region', { name: 'Methodology' }))
  expect(methodology.getByText('crypto-scout-canonical-v1.1')).toBeInTheDocument()
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
      methodology_version: 'crypto-scout-canonical-v1.1',
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
  expect(methodology.getByText('crypto-scout-canonical-v1.1')).toBeInTheDocument()
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

  await selectLanguage(/^RU -/)

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

  await selectLanguage(/^RU -/)

  const summary = await screen.findByText('Приватность, условия и дисклеймер')
  const note = summary.closest('details')
  expect(note).not.toBeNull()
  const noteElement = note as HTMLDetailsElement
  fireEvent.click(summary)

  expect(noteElement).toHaveAttribute('open')
  expect(noteElement).toHaveTextContent('только информационная аналитика')
  expect(noteElement).toHaveTextContent('платный SLA поддержки не предоставляется')
})

test('submits waitlist contacts to the backend API and clears the input on success', async () => {
  render(<App />)

  const input = await screen.findByPlaceholderText('email or @telegram')
  fireEvent.change(input, { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'en', source: 'landing' })
  })
  await waitFor(() => {
    expect(input).toHaveValue('')
  })
  expect(screen.getByRole('status')).toHaveTextContent('Saved. You are on the Bitcoin Risk Brief waitlist.')
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

test('announces waitlist errors assertively, links them to the input, and preserves the contact', async () => {
  apiMocks.joinWaitlist.mockRejectedValueOnce(new Error('invalid contact'))
  render(<App />)

  const input = await screen.findByPlaceholderText('email or @telegram')
  fireEvent.change(input, { target: { value: 'not-a-contact' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Enter a valid email or Telegram handle.')
  expect(input).toHaveAttribute('aria-invalid', 'true')
  expect(input).toHaveAccessibleDescription('Enter a valid email or Telegram handle.')
  expect(input).toHaveValue('not-a-contact')
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

  await selectLanguage(/^RU -/)

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

  await selectLanguage(/^RU -/)

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
  expect(await screen.findByText(textContentMatcher('Low / Neutral near $78,000'))).toBeInTheDocument()
  expect(await screen.findByText(textContentMatcher('Neutral / High near $125,000'))).toBeInTheDocument()

  const riskChart = await screen.findByTestId('chart-risk')
  const riskOption = JSON.parse(riskChart.dataset.option ?? '{}')
  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(riskOption.animation).toBe(false)
  expect(priceOption.animation).toBe(false)
  expect(riskOption.series[0].markLine.label.show).toBe(false)
  expect(riskOption.series[0].markLine.data).toEqual([{ yAxis: 0.30 }, { yAxis: 0.70 }])
})

test('limits the risk levels chart to the practical public risk window', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({ data: latestRisk({ risk: 0.2158 }) })
  apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [
    { risk: 0.00, price_usd: 16256 },
    { risk: 0.10, price_usd: 43658 },
    { risk: 0.20, price_usd: 62340 },
    { risk: 0.30, price_usd: 79024 },
    { risk: 0.50, price_usd: 114797 },
    { risk: 0.70, price_usd: 166961 },
    { risk: 0.80, price_usd: 212058 },
    { risk: 0.90, price_usd: 304364 },
    { risk: 1.00, price_usd: 439659 },
  ], meta: {
    base: latestRisk({ risk: 0.2158 }),
    methodology_version: 'crypto-scout-canonical-v1.1',
    evaluation_date: '2026-07-26',
    current_price: 65026,
    current_risk: 0.2158,
    turnover_enabled: false,
    risk_step: 0.025,
    source_row_count: 5858,
  } })

  render(<App />)

  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(priceOption.xAxis.data).toEqual(['20%', '30%', '50%', '70%', '80%'])
  expect(priceOption.series[0].data).toEqual([62340, 79024, 114797, 166961, 212058])
  expect(priceOption.series[0].data).not.toContain(16256)
  expect(priceOption.series[0].data).not.toContain(439659)
  expect(priceOption.series[0].markLine.data).toEqual([{ xAxis: '20%' }])
  expect(priceOption.series[0].markLine.label.formatter).toBe('Current risk: 22%')
})

test('marks the current risk on levels chart using levels snapshot metadata', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({ data: latestRisk({ risk: 0.2 }) })
  apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [
    { risk: 0.30, price_usd: 78000 },
    { risk: 0.70, price_usd: 125000 },
  ], meta: {
    base: latestRisk({ risk: 0.7 }),
    methodology_version: 'crypto-scout-canonical-v1.1',
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
    data: [{ xAxis: '70%' }],
    lineStyle: { color: '#f2b84b', width: 2 },
  })
  expect(priceOption.series[0].markLine.label).toMatchObject({
    show: true,
    formatter: 'Current risk: 70%',
  })
})

test('falls back to latest risk for levels marker when levels metadata omits current risk', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({ data: latestRisk({ risk: 0.35 }) })
  apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [
    { risk: 0.30, price_usd: 78000 },
    { risk: 0.35, price_usd: 86000 },
    { risk: 0.70, price_usd: 125000 },
  ], meta: { base: latestRisk({ risk: 0.35 }) } })

  render(<App />)

  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(priceOption.series[0].markLine.data).toEqual([{ xAxis: '35%' }])
  expect(priceOption.series[0].markLine.label.formatter).toBe('Current risk: 35%')
})

test.each([0.1, 0.9])(
  'does not clamp a current risk marker outside the public risk levels chart window: %s',
  async (currentRisk) => {
    apiMocks.fetchLatestRisk.mockResolvedValueOnce({ data: latestRisk({ risk: currentRisk }) })
    apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [
      { risk: 0.20, price_usd: 62340 },
      { risk: 0.30, price_usd: 79024 },
      { risk: 0.70, price_usd: 166961 },
      { risk: 0.80, price_usd: 212058 },
    ], meta: {
      base: latestRisk({ risk: currentRisk }),
      methodology_version: 'crypto-scout-canonical-v1.1',
      evaluation_date: '2026-07-26',
      current_price: 65026,
      current_risk: currentRisk,
      turnover_enabled: false,
      risk_step: 0.025,
      source_row_count: 5858,
    } })

    render(<App />)

    const priceChart = await screen.findByTestId('chart-price')
    const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

    expect(priceOption.series[0].markLine).toBeUndefined()
  },
)

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
  expect(levelsChart).toHaveAccessibleDescription(/The table lists the key risk threshold prices used with the risk levels chart\./)
  expect(levelsChart).toHaveAccessibleDescription(/Current risk: 70%/)

  const thresholdTable = screen.getByRole('table', { name: 'Risk threshold price table' })
  expect(within(thresholdTable).getByText('30%')).toBeInTheDocument()
  expect(within(thresholdTable).getByText('70%')).toBeInTheDocument()
  expect(within(thresholdTable).getByText('$78,000')).toBeInTheDocument()
  expect(within(thresholdTable).getByText('$125,000')).toBeInTheDocument()
})

test('defines visible keyboard focus states for interactive controls', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.language-trigger:focus-visible')
  expect(css).toContain('.language-menu:focus-visible')
  expect(css).toContain('.lead-form input:focus-visible')
  expect(css).toContain('.lead-form button:focus-visible')
  expect(css).toContain('.privacy-note summary:focus-visible')
  expect(css).toContain('.bottom-panel-link:focus-visible')
})

test('defines app-controlled language listbox styling', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.language-select { position: relative')
  expect(css).toContain('.language-trigger')
  expect(css).toContain('.language-menu')
  expect(css).toContain('.language-option.is-active')
  expect(css).toContain('[dir="rtl"] .language-menu')
})

test('defines compact bottom panel layout and RTL styles', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.bottom-panel')
  expect(css).toContain('border-top: 1px solid #2c3037')
  expect(css).toContain('[dir="rtl"] .bottom-panel')
})

test('offers all issue 28 languages and applies document language metadata', async () => {
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  expect(trigger).toHaveTextContent('EN')
  expect(trigger).toHaveAttribute('aria-haspopup', 'listbox')
  expect(trigger).toHaveAttribute('aria-expanded', 'false')

  fireEvent.click(trigger)
  expect(trigger).toHaveAttribute('aria-expanded', 'true')
  const listbox = screen.getByRole('listbox', { name: /select language/i })
  expect(within(listbox).getAllByRole('option').map((option) => option.textContent)).toEqual([
    'EN - English',
    'RU - Русский',
    'ZH - 简体中文',
    'DE - Deutsch',
    'FR - Français',
    'ES - Español',
    'AR - العربية',
  ])

  fireEvent.click(within(listbox).getByRole('option', { name: /^DE -/ }))
  expect(await screen.findByText('Aktuelles Risiko')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'de')
  expect(document.documentElement).toHaveAttribute('dir', 'ltr')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(getLanguageTrigger()).toHaveTextContent('DE')

  await selectLanguage(/^FR -/)
  expect(await screen.findByText('Risque actuel')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'fr')
  expect(getLanguageTrigger()).toHaveTextContent('FR')

  await selectLanguage(/^ES -/)
  expect(await screen.findByText('Riesgo actual')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'es')
  expect(getLanguageTrigger()).toHaveTextContent('ES')

  await selectLanguage(/^ZH -/)
  expect(await screen.findByText('当前风险')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'zh-CN')
  expect(getLanguageTrigger()).toHaveTextContent('ZH')

  await selectLanguage(/^AR -/)
  expect(await screen.findByText('المخاطر الحالية')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ar')
  expect(document.documentElement).toHaveAttribute('dir', 'rtl')
  expect(getLanguageTrigger()).toHaveTextContent('AR')
})

test('opens and closes the custom language listbox from keyboard and outside pointer interaction', async () => {
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  fireEvent.keyDown(trigger, { key: 'Enter' })

  const listbox = await screen.findByRole('listbox', { name: /select language/i })
  expect(listbox).toHaveFocus()
  expect(trigger).toHaveAttribute('aria-expanded', 'true')

  fireEvent.keyDown(listbox, { key: 'Escape' })
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(trigger).toHaveFocus()
  expect(trigger).toHaveAttribute('aria-expanded', 'false')

  fireEvent.keyDown(trigger, { key: ' ' })
  expect(await screen.findByRole('listbox')).toBeInTheDocument()
  fireEvent.pointerDown(document.body)
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(trigger).toHaveAttribute('aria-expanded', 'false')
})

test('closes the custom language listbox on Tab without returning focus to the trigger', async () => {
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  fireEvent.keyDown(trigger, { key: 'Enter' })

  const listbox = await screen.findByRole('listbox', { name: /select language/i })
  expect(listbox).toHaveFocus()
  expect(trigger).toHaveAttribute('aria-expanded', 'true')

  fireEvent.keyDown(listbox, { key: 'Tab' })

  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(trigger).toHaveAttribute('aria-expanded', 'false')
  expect(trigger).not.toHaveFocus()
})

test('supports arrow navigation and keyboard selection in the custom language listbox', async () => {
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  fireEvent.keyDown(trigger, { key: 'ArrowDown' })

  let listbox = await screen.findByRole('listbox', { name: /select language/i })
  expect(listbox.getAttribute('aria-activedescendant')).toMatch(/-ru$/)

  fireEvent.keyDown(listbox, { key: ' ' })
  expect(await screen.findByText('Текущий риск')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ru')
  expect(document.documentElement).toHaveAttribute('dir', 'ltr')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(getLanguageTrigger()).toHaveFocus()

  fireEvent.keyDown(getLanguageTrigger(), { key: 'ArrowUp' })
  listbox = await screen.findByRole('listbox')
  expect(listbox.getAttribute('aria-activedescendant')).toMatch(/-en$/)
  fireEvent.keyDown(listbox, { key: 'ArrowUp' })
  expect(listbox.getAttribute('aria-activedescendant')).toMatch(/-ar$/)
  fireEvent.keyDown(listbox, { key: 'Enter' })

  expect(await screen.findByText('المخاطر الحالية')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ar')
  expect(document.documentElement).toHaveAttribute('dir', 'rtl')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})

test('isolates mixed-direction language option labels as LTR while Arabic is active', async () => {
  render(<App />)

  await selectLanguage(/^AR -/)
  fireEvent.click(getLanguageTrigger())

  const listbox = await screen.findByRole('listbox')
  const arabicOption = within(listbox).getByRole('option', { name: /^AR - العربية$/ })
  const isolatedLabel = arabicOption.querySelector('bdi')

  expect(isolatedLabel).not.toBeNull()
  expect(isolatedLabel as HTMLElement).toHaveAttribute('dir', 'ltr')
  expect(isolatedLabel as HTMLElement).toHaveTextContent('AR - العربية')
})

test('isolates visible Arabic numeric, date, and currency values as LTR', async () => {
  render(<App />)

  await selectLanguage(/^AR -/)

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
    '$78,000',
    '$125,000',
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
      methodology_version: 'crypto-scout-canonical-v1.1',
    },
  })

  render(<App />)

  await selectLanguage(/^AR -/)

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

  await selectLanguage(/^FR -/)
  fireEvent.change(await screen.findByPlaceholderText('email ou @telegram'), { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /rejoindre la liste/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'fr', source: 'landing' })
  })
})

test('keeps Arabic waitlist contact entry LTR and submits locale metadata', async () => {
  render(<App />)

  await selectLanguage(/^AR -/)

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

  await selectLanguage(/^DE -/)

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
