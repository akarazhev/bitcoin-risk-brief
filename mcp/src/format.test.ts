import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  ADVICE_LINE,
  formatBrief,
  formatCurrentRisk,
  formatHistory,
  formatLevels,
  formatReadiness,
} from './format.js'
import type { Envelope } from './freshness.js'

const currentEnvelope: Envelope = {
  coveredThrough: '2026-06-25',
  dataState: 'current',
  methodology: 'crypto-scout-canonical-v1.1',
  dataFresh: true,
  dataAgeDays: 1,
  maxAgeDays: 2,
}

const latestPayload = {
  data: {
    timestamp: '2026-06-25T00:00:00+00:00',
    price_usd: 60100.0,
    model_price_usd: 60100.0,
    low_usd: 58800.0,
    high_usd: 61584.0,
    risk: 0.3025,
    score: -0.82,
    risk_state: 'neutral',
    trend_dev: 0.0,
    vol_regime: 0.0,
    turnover: -10.2,
    z_trend_dev: 0.0,
    z_vol_regime: 0.0,
    z_turnover: 0.0,
    turnover_enabled: true,
  },
}

const historyPayload = {
  data: [
    { timestamp: '2026-06-24T00:00:00+00:00', risk: 0.31, risk_state: 'neutral' },
    { timestamp: '2026-06-25T00:00:00+00:00', risk: 0.3025, risk_state: 'neutral' },
  ],
  meta: { returned_points: 2 },
}

const levelsPayload = {
  data: [
    { risk: 0.0, price_usd: 10000.0 },
    { risk: 0.025, price_usd: 11000.0 },
  ],
  meta: {
    base: { timestamp: '2026-06-25T00:00:00+00:00', risk: 0.3025 },
    methodology_version: 'crypto-scout-canonical-v1.1',
    evaluation_date: '2026-06-25',
    current_price: 60100.0,
    current_risk: 0.3025,
    turnover_enabled: true,
    risk_step: 0.025,
    source_row_count: 5827,
  },
}

const briefPayload = {
  data: {
    snapshot_version: 'bitcoin-risk-brief-v1',
    as_of: '2026-06-25T00:00:00+00:00',
    risk: 0.3025,
    risk_state: 'neutral',
    price_usd: 60100.0,
    delta_risk: -0.01,
    sections: {
      en: { summary: 'English summary', what_changed: 'English changed', avoid_now: 'English avoid', confirm_next: 'English confirm' },
      ru: { summary: 'Russian summary', what_changed: 'Russian changed', avoid_now: 'Russian avoid', confirm_next: 'Russian confirm' },
      zh: { summary: 'Chinese summary', what_changed: 'Chinese changed', avoid_now: 'Chinese avoid', confirm_next: 'Chinese confirm' },
      de: { summary: 'German summary', what_changed: 'German changed', avoid_now: 'German avoid', confirm_next: 'German confirm' },
      fr: { summary: 'French summary', what_changed: 'French changed', avoid_now: 'French avoid', confirm_next: 'French confirm' },
      es: { summary: 'Spanish summary', what_changed: 'Spanish changed', avoid_now: 'Spanish avoid', confirm_next: 'Spanish confirm' },
      ar: { summary: 'Arabic summary', what_changed: 'Arabic changed', avoid_now: 'Arabic avoid', confirm_next: 'Arabic confirm' },
    },
  },
}

const readinessPayload = {
  status: 'ready',
  checks: { data_fresh: true },
  data: {
    latest_date: '2026-06-25',
    covered_end: '2026-06-25',
    data_age_days: 1,
    max_age_days: 2,
    source: 'coinmarketcap_csv',
    row_count: 5827,
    methodology_version: 'crypto-scout-canonical-v1.1',
  },
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => {
    throw new Error('formatters must not call fetch')
  }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('response formatters', () => {
  it('formats current risk with the value, state, and envelope', () => {
    const text = formatCurrentRisk(latestPayload, currentEnvelope)

    expect(text).toContain('0.30')
    expect(text).toContain('neutral')
    expect(text).toContain('covered_through: 2026-06-25')
    expect(text).toContain('data_state:      current')
  })

  it('leads stale current risk with diagnostics while retaining the last known observation', () => {
    const text = formatCurrentRisk(latestPayload, {
      ...currentEnvelope,
      coveredThrough: '2026-08-09',
      dataState: 'stale',
      dataFresh: false,
      dataAgeDays: 3,
      maxAgeDays: 2,
    })

    expect(text.startsWith('DATA IS STALE — do not present these values as current.')).toBe(true)
    expect(text).toContain('Last known observation: risk 0.30 (neutral), covered through 2026-08-09.')
    expect(text).toContain('Readiness reports: data_fresh false, 3 days old, tolerance 2 days.')
  })

  it('names the covered date for a behind current-risk response without a stale banner', () => {
    const text = formatCurrentRisk(latestPayload, {
      ...currentEnvelope,
      coveredThrough: '2026-06-24',
      dataState: 'behind',
    })

    expect(text).toContain('covered_through: 2026-06-24')
    expect(text).not.toContain('DATA IS STALE')
  })

  it('appends the advice boundary to every formatter response', () => {
    const outputs = [
      formatReadiness(readinessPayload, currentEnvelope),
      formatCurrentRisk(latestPayload, currentEnvelope),
      formatHistory(historyPayload, currentEnvelope),
      formatLevels(levelsPayload, currentEnvelope),
      formatBrief(briefPayload, currentEnvelope, 'en'),
    ]

    for (const output of outputs) {
      expect(output.endsWith(ADVICE_LINE)).toBe(true)
    }
  })

  it('defines an advice boundary that says it is not financial advice', () => {
    expect(ADVICE_LINE).toContain('not financial advice')
  })

  it('renders one history line per point and says how many were returned', () => {
    const text = formatHistory(historyPayload, currentEnvelope)

    expect(text).toContain('2 points returned.')
    expect(text).toContain('2026-06-24: risk 0.31 (neutral)')
    expect(text).toContain('2026-06-25: risk 0.30 (neutral)')
  })

  it('selects only the requested brief locale', () => {
    const text = formatBrief(briefPayload, currentEnvelope, 'ru')

    expect(text).toContain('Russian summary')
    for (const phrase of ['English summary', 'Chinese summary', 'German summary', 'French summary', 'Spanish summary', 'Arabic summary']) {
      expect(text).not.toContain(phrase)
    }
  })

  it('renders the risk-level ladder and evaluation date', () => {
    const text = formatLevels(levelsPayload, currentEnvelope)

    expect(text).toContain('Evaluation date: 2026-06-25')
    expect(text).toContain('risk 0.00: $10,000')
    expect(text).toContain('risk 0.03: $11,000')
  })

  it('reports a missing data key instead of throwing', () => {
    expect(formatCurrentRisk({}, currentEnvelope)).toContain('Response data is missing.')
  })

  it('omits stale diagnostics when all readiness diagnostics are null', () => {
    const text = formatCurrentRisk(latestPayload, {
      ...currentEnvelope,
      dataState: 'stale',
      dataFresh: null,
      dataAgeDays: null,
      maxAgeDays: null,
    })

    expect(text).not.toContain('Readiness reports:')
    expect(text).not.toContain('null')
    expect(text).not.toContain('undefined')
  })

  it('reports an unavailable brief locale and lists available locales without falling back', () => {
    const text = formatBrief({
      ...briefPayload,
      data: { ...briefPayload.data, sections: { en: briefPayload.data.sections.en, ru: briefPayload.data.sections.ru } },
    }, currentEnvelope, 'de')

    expect(text).toContain('Brief locale "de" is not available. Available locales: en, ru.')
    expect(text).not.toContain('English summary')
    expect(text).not.toContain('Russian summary')
  })
})
