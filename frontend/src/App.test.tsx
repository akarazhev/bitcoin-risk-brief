import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import App from './App'

const chartMocks = vi.hoisted(() => ({
  resize: vi.fn(),
}))

vi.mock('echarts-for-react', () => ({
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
  joinWaitlist: vi.fn(async () => ({ data: { contact_type: 'email', locale: 'en', created: true } })),
}))

vi.mock('./api', () => ({
  fetchLatestRisk: async () => ({ data: { timestamp: '2026-06-26T00:00:00Z', price_usd: 100000, risk: 0.7, score: 1, risk_state: 'high', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false } }),
  fetchRiskHistory: async () => ({ data: [
    { timestamp: '2026-06-24T00:00:00Z', price_usd: 98000, risk: 0.52, score: 0.52, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
    { timestamp: '2026-06-25T00:00:00Z', price_usd: 99000, risk: 0.63, score: 0.63, risk_state: 'neutral', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false },
  ], meta: { returned_points: 2 } }),
  fetchRiskLevels: async () => ({ data: [
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.65, price_usd: 118000 },
  ], meta: { base: {} } }),
  fetchBrief: async () => ({ data: { snapshot_version: 'v1', as_of: '2026-06-26T00:00:00Z', risk: 0.7, risk_state: 'high', price_usd: 100000, delta_risk: 0.1, sections: { en: { summary: 'Risk elevated', what_changed: 'Changed', avoid_now: 'Avoid', confirm_next: 'Confirm' }, ru: { summary: 'Риск повышен', what_changed: 'Изменилось', avoid_now: 'Избегай', confirm_next: 'Проверь' } } } }),
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

beforeEach(() => {
  chartMocks.resize.mockClear()
  apiMocks.joinWaitlist.mockClear()
  setCompactViewport(false)
})

test('renders the Bitcoin Risk Brief shell', async () => {
  render(<App />)
  expect(await screen.findByText('Bitcoin Risk Brief')).toBeInTheDocument()
  expect(await screen.findByText('Current risk')).toBeInTheDocument()
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
