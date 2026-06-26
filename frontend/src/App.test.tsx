import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import App from './App'

vi.mock('echarts-for-react', () => ({
  default: () => <div data-testid="chart" />,
}))

const apiMocks = vi.hoisted(() => ({
  joinWaitlist: vi.fn(async () => ({ data: { contact_type: 'email', locale: 'en', created: true } })),
}))

vi.mock('./api', () => ({
  fetchLatestRisk: async () => ({ data: { timestamp: '2026-06-26T00:00:00Z', price_usd: 100000, risk: 0.7, score: 1, risk_state: 'high', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false } }),
  fetchRiskHistory: async () => ({ data: [], meta: { returned_points: 0 } }),
  fetchRiskLevels: async () => ({ data: [], meta: { base: {} } }),
  fetchBrief: async () => ({ data: { snapshot_version: 'v1', as_of: '2026-06-26T00:00:00Z', risk: 0.7, risk_state: 'high', price_usd: 100000, delta_risk: 0.1, sections: { en: { summary: 'Risk elevated', what_changed: 'Changed', avoid_now: 'Avoid', confirm_next: 'Confirm' }, ru: { summary: 'Риск повышен', what_changed: 'Изменилось', avoid_now: 'Избегай', confirm_next: 'Проверь' } } } }),
  joinWaitlist: apiMocks.joinWaitlist,
}))

beforeEach(() => {
  apiMocks.joinWaitlist.mockClear()
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
