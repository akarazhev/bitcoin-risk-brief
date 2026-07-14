import type { BriefPayload, ReadinessPayload, RiskLevelsPayload, RiskPoint, WaitlistRequest, WaitlistResponse } from './types'

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return (await response.json()) as T
}

async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return (await response.json()) as T
}

export async function fetchLatestRisk() {
  return getJson<{ data: RiskPoint }>('/api/risk/latest')
}

export async function fetchRiskHistory() {
  return getJson<{ data: RiskPoint[]; meta: { returned_points: number } }>('/api/risk/history?limit=2000')
}

export async function fetchRiskLevels() {
  return getJson<RiskLevelsPayload>('/api/risk/levels')
}

export async function fetchBrief() {
  return getJson<{ data: BriefPayload }>('/api/brief/latest')
}

export async function fetchReadiness() {
  const response = await fetch('/api/readiness', { cache: 'no-store' })
  const payload = (await response.json()) as ReadinessPayload
  if (!response.ok && response.status !== 503) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return payload
}

export async function joinWaitlist(payload: WaitlistRequest) {
  return postJson<{ data: WaitlistResponse }>('/api/waitlist', payload)
}
