import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import App from './App'

vi.mock('./api', () => ({
  fetchLatestRisk: async () => ({ data: { timestamp: '2026-06-26T00:00:00Z', price_usd: 100000, risk: 0.7, score: 1, risk_state: 'high', trend_dev: 1, vol_regime: 0.1, turnover: null, z_trend_dev: 1, z_vol_regime: 1, z_turnover: null, turnover_enabled: false } }),
  fetchRiskHistory: async () => ({ data: [], meta: { returned_points: 0 } }),
  fetchRiskLevels: async () => ({ data: [], meta: { base: {} } }),
  fetchBrief: async () => ({ data: { snapshot_version: 'v1', as_of: '2026-06-26T00:00:00Z', risk: 0.7, risk_state: 'high', price_usd: 100000, delta_risk: 0.1, sections: { en: { summary: 'Risk elevated', what_changed: 'Changed', avoid_now: 'Avoid', confirm_next: 'Confirm' }, ru: { summary: 'Риск повышен', what_changed: 'Изменилось', avoid_now: 'Избегай', confirm_next: 'Проверь' } } } }),
}))

test('renders the Bitcoin Risk Brief shell', async () => {
  render(<App />)
  expect(await screen.findByText('Bitcoin Risk Brief')).toBeInTheDocument()
  expect(await screen.findByText('Current risk')).toBeInTheDocument()
})
