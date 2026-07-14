import { render, screen, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import type { RiskPoint } from './types'

const RUNTIME_YEAR = '2031'

const apiMocks = vi.hoisted(() => ({
  fetchLatestRisk: vi.fn(),
  fetchRiskHistory: vi.fn(),
  fetchRiskLevels: vi.fn(),
  fetchBrief: vi.fn(),
  fetchReadiness: vi.fn(),
  joinWaitlist: vi.fn(),
}))

vi.mock('./api', () => ({
  fetchReadiness: apiMocks.fetchReadiness,
  fetchLatestRisk: apiMocks.fetchLatestRisk,
  fetchRiskHistory: apiMocks.fetchRiskHistory,
  fetchRiskLevels: apiMocks.fetchRiskLevels,
  fetchBrief: apiMocks.fetchBrief,
  joinWaitlist: apiMocks.joinWaitlist,
}))

function latestRisk(): RiskPoint {
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
  }
}

beforeEach(() => {
  apiMocks.fetchLatestRisk.mockResolvedValue({ data: latestRisk() })
  apiMocks.fetchBrief.mockResolvedValue({
    data: {
      snapshot_version: 'v1',
      as_of: '2026-06-26T00:00:00Z',
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
  apiMocks.fetchRiskHistory.mockReturnValue(new Promise(() => {}))
  apiMocks.fetchRiskLevels.mockReturnValue(new Promise(() => {}))
})

afterEach(() => {
  vi.useRealTimers()
})

test('renders the Minihub copyright year from the runtime date', async () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date(`${RUNTIME_YEAR}-06-15T12:00:00Z`))
  const { default: RuntimeApp } = await import('./App')
  vi.useRealTimers()

  render(<RuntimeApp />)

  const supportLink = await screen.findByRole('link', { name: 'support@minihub.app' })
  const footer = supportLink.closest('footer.bottom-panel')
  expect(footer).not.toBeNull()

  expect(within(footer as HTMLElement).getByText(RUNTIME_YEAR)).toBeInTheDocument()
  expect(footer?.querySelector('.footer-legal')).toHaveTextContent(`© ${RUNTIME_YEAR} Minihub`)
})
