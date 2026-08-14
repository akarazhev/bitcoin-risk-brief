import { describe, expect, it } from 'vitest'
import { deriveEnvelope, lastCompletedUtcDay, renderEnvelope } from './freshness.js'

const NOW = new Date('2026-08-13T03:00:00Z')

function readiness(
  status: string,
  coveredEnd: string | null,
  { dataFresh = true, ageDays = 1, maxAgeDays = 2 } = {},
) {
  return {
    status,
    checks: { data_fresh: dataFresh },
    data: {
      covered_end: coveredEnd,
      data_age_days: ageDays,
      max_age_days: maxAgeDays,
      methodology_version: 'crypto-scout-canonical-v1.1',
    },
  }
}

describe('lastCompletedUtcDay', () => {
  it('is yesterday in UTC', () => {
    expect(lastCompletedUtcDay(NOW)).toBe('2026-08-12')
  })

  it('crosses a month boundary correctly', () => {
    expect(lastCompletedUtcDay(new Date('2026-09-01T00:30:00Z'))).toBe('2026-08-31')
  })
})

describe('deriveEnvelope', () => {
  it('is current when the observation covers the last completed day', () => {
    expect(deriveEnvelope(readiness('ready', '2026-08-12'), NOW).dataState).toBe('current')
  })

  it('is behind when readiness is ready but the day is older', () => {
    expect(deriveEnvelope(readiness('ready', '2026-08-11'), NOW).dataState).toBe('behind')
  })

  it('is stale whenever readiness is not ready, however recent the date', () => {
    expect(deriveEnvelope(readiness('degraded', '2026-08-12'), NOW).dataState).toBe('stale')
  })

  it('is stale when readiness cannot be understood at all', () => {
    expect(deriveEnvelope(null, NOW).dataState).toBe('stale')
    expect(deriveEnvelope({ nonsense: true }, NOW).dataState).toBe('stale')
  })

  it('carries the covered date and the methodology through', () => {
    const envelope = deriveEnvelope(readiness('ready', '2026-08-12'), NOW)
    expect(envelope.coveredThrough).toBe('2026-08-12')
    expect(envelope.methodology).toBe('crypto-scout-canonical-v1.1')
  })

  it('carries the readiness diagnostics the stale banner needs', () => {
    const envelope = deriveEnvelope(
      readiness('degraded', '2026-08-09', { dataFresh: false, ageDays: 3, maxAgeDays: 2 }),
      NOW,
    )
    expect(envelope.dataFresh).toBe(false)
    expect(envelope.dataAgeDays).toBe(3)
    expect(envelope.maxAgeDays).toBe(2)
  })

  it('leaves the diagnostics null when readiness cannot be understood', () => {
    const envelope = deriveEnvelope(null, NOW)
    expect(envelope.dataFresh).toBeNull()
    expect(envelope.dataAgeDays).toBeNull()
    expect(envelope.maxAgeDays).toBeNull()
  })
})

describe('renderEnvelope', () => {
  it('names all three fields so a model cannot receive a value without them', () => {
    const text = renderEnvelope(deriveEnvelope(readiness('ready', '2026-08-12'), NOW))
    expect(text).toContain('covered_through: 2026-08-12')
    expect(text).toContain('data_state:      current')
    expect(text).toContain('methodology:     crypto-scout-canonical-v1.1')
  })

  it('prints exactly three lines - diagnostics belong to the stale banner, not the envelope', () => {
    const text = renderEnvelope(deriveEnvelope(readiness('ready', '2026-08-12'), NOW))
    expect(text.split('\n')).toHaveLength(3)
  })
})
