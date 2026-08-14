export type DataState = 'current' | 'behind' | 'stale'

export interface Envelope {
  coveredThrough: string | null
  dataState: DataState
  methodology: string | null
  // Readiness diagnostics consumed by the stale banner, not rendered here.
  dataFresh: boolean | null
  dataAgeDays: number | null
  maxAgeDays: number | null
}

export function lastCompletedUtcDay(now: Date = new Date()): string {
  const utcMidnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())
  return new Date(utcMidnight - 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
}

export function deriveEnvelope(readiness: unknown, now: Date = new Date()): Envelope {
  if (typeof readiness !== 'object' || readiness === null || Array.isArray(readiness)) {
    return {
      coveredThrough: null,
      dataState: 'stale',
      methodology: null,
      dataFresh: null,
      dataAgeDays: null,
      maxAgeDays: null,
    }
  }

  const payload = readiness as { status?: unknown; checks?: unknown; data?: unknown }
  const checks = typeof payload.checks === 'object' && payload.checks !== null && !Array.isArray(payload.checks)
    ? payload.checks as { data_fresh?: unknown }
    : {}
  const data = typeof payload.data === 'object' && payload.data !== null && !Array.isArray(payload.data)
    ? payload.data as { covered_end?: unknown; data_age_days?: unknown; max_age_days?: unknown; methodology_version?: unknown }
    : {}
  const coveredThrough = typeof data.covered_end === 'string' ? data.covered_end : null
  const methodology = typeof data.methodology_version === 'string' ? data.methodology_version : null
  const dataFresh = typeof checks.data_fresh === 'boolean' ? checks.data_fresh : null
  const dataAgeDays = typeof data.data_age_days === 'number' ? data.data_age_days : null
  const maxAgeDays = typeof data.max_age_days === 'number' ? data.max_age_days : null

  if (payload.status !== 'ready') {
    return { coveredThrough, dataState: 'stale', methodology, dataFresh, dataAgeDays, maxAgeDays }
  }

  return {
    coveredThrough,
    dataState: coveredThrough === lastCompletedUtcDay(now) ? 'current' : 'behind',
    methodology,
    dataFresh,
    dataAgeDays,
    maxAgeDays,
  }
}

export function renderEnvelope(envelope: Envelope): string {
  return [
    `covered_through: ${envelope.coveredThrough ?? 'unknown'}`,
    `data_state:      ${envelope.dataState}`,
    `methodology:     ${envelope.methodology ?? 'unknown'}`,
  ].join('\n')
}
