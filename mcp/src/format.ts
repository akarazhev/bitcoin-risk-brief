import { renderEnvelope, type Envelope } from './freshness.js'

export const ADVICE_LINE = 'Analytics and research context, not financial advice, not a price forecast, and not a trade signal.'

type PayloadRecord = Record<string, unknown>

function isRecord(value: unknown): value is PayloadRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function responseData(payload: unknown): PayloadRecord | null {
  return isRecord(payload) && isRecord(payload.data) ? payload.data : null
}

function numberText(value: unknown): string {
  return typeof value === 'number' ? value.toFixed(2) : 'unknown'
}

function priceText(value: unknown): string {
  return typeof value === 'number'
    ? `$${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)}`
    : 'unknown'
}

function dateText(value: unknown): string {
  return typeof value === 'string' ? value.slice(0, 10) : 'unknown'
}

function staleDiagnostics(envelope: Envelope): string | null {
  if (envelope.dataFresh === null && envelope.dataAgeDays === null && envelope.maxAgeDays === null) {
    return null
  }

  const dataFresh = envelope.dataFresh === null ? 'unknown' : String(envelope.dataFresh)
  const dataAgeDays = envelope.dataAgeDays === null ? 'unknown' : String(envelope.dataAgeDays)
  const maxAgeDays = envelope.maxAgeDays === null ? 'unknown' : String(envelope.maxAgeDays)
  return `Readiness reports: data_fresh ${dataFresh}, ${dataAgeDays} days old, tolerance ${maxAgeDays} days.`
}

function complete(lines: string[], envelope: Envelope): string {
  if (envelope.dataState === 'stale') {
    const diagnostics = staleDiagnostics(envelope)
    return [
      'DATA IS STALE — do not present these values as current.',
      ...lines,
      ...(diagnostics === null ? [] : [diagnostics]),
      renderEnvelope(envelope),
      ADVICE_LINE,
    ].join('\n')
  }

  return [...lines, renderEnvelope(envelope), ADVICE_LINE].join('\n')
}

function missingData(envelope: Envelope): string {
  return complete(['Response data is missing.'], envelope)
}

export function formatReadiness(payload: unknown, envelope: Envelope): string {
  const data = responseData(payload)
  if (data === null) return missingData(envelope)

  const status = isRecord(payload) && typeof payload.status === 'string' ? payload.status : 'unknown'
  return complete([`Readiness status: ${status}.`], envelope)
}

export function formatCurrentRisk(payload: unknown, envelope: Envelope): string {
  const data = responseData(payload)
  if (data === null) return missingData(envelope)

  const risk = numberText(data.risk)
  const state = typeof data.risk_state === 'string' ? data.risk_state : 'unknown'
  const observation = envelope.dataState === 'stale'
    ? `Last known observation: risk ${risk} (${state}), covered through ${envelope.coveredThrough ?? 'unknown'}.`
    : `Current observation: risk ${risk} (${state}).`
  const price = `Model price: ${priceText(data.model_price_usd ?? data.price_usd)}.`
  const range = `Daily range: ${priceText(data.low_usd)} to ${priceText(data.high_usd)}.`

  return complete([observation, price, range], envelope)
}

export function formatHistory(payload: unknown, envelope: Envelope): string {
  if (!isRecord(payload) || !Array.isArray(payload.data)) return missingData(envelope)

  const points = payload.data.filter(isRecord)
  const lines = [`${points.length} points returned.`]
  for (const point of points) {
    const state = typeof point.risk_state === 'string' ? point.risk_state : 'unknown'
    lines.push(`${dateText(point.timestamp)}: risk ${numberText(point.risk)} (${state})`)
  }
  return complete(lines, envelope)
}

export function formatLevels(payload: unknown, envelope: Envelope): string {
  if (!isRecord(payload) || !Array.isArray(payload.data)) return missingData(envelope)

  const meta = isRecord(payload.meta) ? payload.meta : {}
  const lines = [`Evaluation date: ${dateText(meta.evaluation_date)}`]
  for (const level of payload.data.filter(isRecord)) {
    lines.push(`risk ${numberText(level.risk)}: ${priceText(level.price_usd)}`)
  }
  return complete(lines, envelope)
}

export function formatBrief(payload: unknown, envelope: Envelope, locale: string): string {
  const data = responseData(payload)
  if (data === null || !isRecord(data.sections)) return missingData(envelope)

  const sections = data.sections
  const section = sections[locale]
  if (!isRecord(section)) {
    const locales = Object.keys(sections)
    return complete([`Brief locale "${locale}" is not available. Available locales: ${locales.join(', ')}.`], envelope)
  }

  const lines = [`Brief (${locale}):`]
  for (const key of ['summary', 'what_changed', 'avoid_now', 'confirm_next']) {
    if (typeof section[key] === 'string') lines.push(section[key])
  }
  return complete(lines, envelope)
}
