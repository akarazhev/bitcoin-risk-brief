import { beforeEach, expect, test, vi } from 'vitest'
import { fetchReadiness } from './api'

beforeEach(() => {
  vi.restoreAllMocks()
})

test('parses degraded readiness payloads returned with a 503 status', async () => {
  const payload = {
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
  }
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: false,
    status: 503,
    json: async () => payload,
  })))

  await expect(fetchReadiness()).resolves.toEqual(payload)
})

test('requests readiness with browser cache disabled', async () => {
  const payload = {
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
      latest_date: '2026-07-10',
      covered_end: '2026-07-10',
      data_age_days: 1,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5841,
      methodology_version: 'crypto-scout-canonical-v1',
    },
  }
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => payload,
  }))
  vi.stubGlobal('fetch', fetchMock)

  await expect(fetchReadiness()).resolves.toEqual(payload)

  expect(fetchMock).toHaveBeenCalledWith('/api/readiness', { cache: 'no-store' })
})
