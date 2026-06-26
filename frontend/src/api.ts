import type { BriefPayload, RiskLevel, RiskPoint } from './types'

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
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
  return getJson<{ data: RiskLevel[]; meta: { base: RiskPoint } }>('/api/risk/levels')
}

export async function fetchBrief() {
  return getJson<{ data: BriefPayload }>('/api/brief/latest')
}
