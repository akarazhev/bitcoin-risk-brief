export type RiskState = 'low' | 'neutral' | 'high'

export interface RiskPoint {
  timestamp: string
  price_usd: number
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
  sections: Record<'en' | 'ru', BriefSection>
}

export interface RiskLevel {
  risk: number
  price_usd: number
}

export interface WaitlistRequest {
  contact: string
  locale: 'en' | 'ru'
  source: string
}

export interface WaitlistResponse {
  contact_type: 'email' | 'telegram'
  locale: 'en' | 'ru'
  created: boolean
}
