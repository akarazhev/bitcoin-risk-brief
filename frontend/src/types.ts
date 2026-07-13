import type { Locale } from './locales'

export type { Locale }
export type RiskState = 'low' | 'neutral' | 'high'

export interface RiskPoint {
  timestamp: string
  price_usd: number
  model_price_usd?: number | null
  low_usd?: number | null
  high_usd?: number | null
  risk: number
  score: number
  risk_state: RiskState
  trend_dev: number
  vol_regime: number
  turnover: number | null
  z_trend_dev: number
  z_vol_regime: number
  z_turnover: number | null
  turnover_enabled: boolean
}

export interface BriefSection {
  summary: string
  what_changed: string
  avoid_now: string
  confirm_next: string
}

export interface BriefPayload {
  snapshot_version: string
  as_of: string
  risk: number
  risk_state: RiskState
  price_usd: number
  delta_risk: number
  sections: Partial<Record<Locale, BriefSection>> & Record<'en', BriefSection>
}

export interface RiskLevel {
  risk: number
  price_usd: number
}

export type ReadinessStatus = 'ready' | 'degraded'

export interface ReadinessChecks {
  risk_data_available: boolean
  validation_available: boolean
  risk_range_ok: boolean
  validation_has_rows: boolean
  latest_matches_validation_end: boolean
  source_is_canonical: boolean
  data_fresh: boolean
}

export interface ReadinessPayload {
  status: ReadinessStatus
  checks: ReadinessChecks
  data: {
    latest_date: string | null
    covered_end: string | null
    data_age_days: number | null
    max_age_days: number
    source: string | null
    row_count: number
    methodology_version: string | null
  }
}

export interface WaitlistRequest {
  contact: string
  locale: Locale
  source: string
}

export interface WaitlistResponse {
  contact_type: 'email' | 'telegram'
  locale: Locale
  created: boolean
}
