import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import App from './App'

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

async function findPriceMetric(title = 'BTC price model input') {
  const titleElement = await screen.findByText(title)
  const metric = titleElement.closest('.price-metric')
  expect(metric).not.toBeNull()
  return within(metric as HTMLElement)
}

beforeEach(() => {
  chartMocks.resize.mockClear()
  apiMocks.fetchLatestRisk.mockReset()
  apiMocks.fetchLatestRisk.mockResolvedValue({ data: { timestamp: '2026-06-26T00:00:00Z', price_usd: 100000, model_price_usd: 100000, low_usd: 96500, high_usd: 104250, risk: 0.7, score: 1, risk_state: 'high', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false } })
  apiMocks.fetchRiskHistory.mockReset()
  apiMocks.fetchRiskHistory.mockResolvedValue({ data: [
    { timestamp: '2026-06-24T00:00:00Z', price_usd: 98000, risk: 0.52, score: 0.52, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-25T00:00:00Z', price_usd: 99000, risk: 0.63, score: 0.63, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
  ], meta: { returned_points: 2 } })
  apiMocks.fetchRiskLevels.mockReset()
  apiMocks.fetchRiskLevels.mockResolvedValue({ data: [
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.65, price_usd: 118000 },
  ], meta: { base: {} } })
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

test('renders readiness freshness and validation near the latest data date', async () => {
  render(<App />)

  expect(apiMocks.fetchReadiness).toHaveBeenCalled()
  expect(await screen.findByText('Updated')).toBeInTheDocument()
  expect(screen.getAllByText('2026-06-26').length).toBeGreaterThan(0)
  expect(screen.getByText('Readiness ready')).toBeInTheDocument()
  expect(screen.getByText('Validation passed')).toBeInTheDocument()
  expect(screen.getByText('Latest date: 2026-06-26')).toBeInTheDocument()
  expect(screen.getByText('Fresh: 1 day old')).toBeInTheDocument()
  expect(screen.getByText('Covered end: 2026-06-26')).toBeInTheDocument()
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
  expect(screen.getByText('Data is 6 days old')).toBeInTheDocument()
  expect(screen.getByText('Covered end: 2026-06-19')).toBeInTheDocument()
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

test('renders methodology reference and no-advice disclaimer', async () => {
  render(<App />)

  expect(await screen.findByText('Methodology')).toBeInTheDocument()
  expect(screen.getByText('crypto-scout-canonical-v1')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /methodology/i })).toHaveAttribute('href', '#methodology')
  expect(screen.getByText('Risk levels are scenario outputs, not financial advice or trading instructions.')).toBeInTheDocument()
})

test('submits waitlist contacts to the backend API', async () => {
  render(<App />)

  fireEvent.change(await screen.findByPlaceholderText('email or @telegram'), { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'en', source: 'landing' })
  })
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

  fireEvent.click(screen.getByRole('button', { name: /ru/i }))

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

test('places the waitlist call to action before the charts', async () => {
  render(<App />)

  const waitlistTitle = await screen.findByText('Get the daily signal')
  const riskHistoryTitle = await screen.findByText('Risk history')

  expect(waitlistTitle.compareDocumentPosition(riskHistoryTitle) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
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

  expect(await screen.findByText('Low / Neutral')).toBeInTheDocument()
  expect(screen.getByText('Neutral / High')).toBeInTheDocument()
  expect(screen.getByText('Low / Neutral near $82,000')).toBeInTheDocument()
  expect(screen.getByText('Neutral / High near $118,000')).toBeInTheDocument()

  const riskChart = await screen.findByTestId('chart-risk')
  const riskOption = JSON.parse(riskChart.dataset.option ?? '{}')
  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(riskOption.animation).toBe(false)
  expect(priceOption.animation).toBe(false)
  expect(riskOption.series[0].markLine.label.show).toBe(false)
  expect(riskOption.series[0].markLine.data).toEqual([{ yAxis: 0.35 }, { yAxis: 0.65 }])
})

test('defines visible keyboard focus states for interactive controls', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.lang:focus-visible')
  expect(css).toContain('.lead-form input:focus-visible')
  expect(css).toContain('.lead-form button:focus-visible')
})
