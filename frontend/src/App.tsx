import { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import type { EChartsOption } from 'echarts'
import { Bell, CheckCircle2, ExternalLink, Radio, Send, ShieldAlert, TriangleAlert } from 'lucide-react'
import { ApiError, fetchBrief, fetchLatestRisk, fetchReadiness, fetchRiskHistory, fetchRiskLevels, joinWaitlist } from './api'
import { LanguageSelect } from './LanguageSelect'
import { copy, getLocaleOption, localeOptions, stateLabel } from './locales'
import Turnstile from './Turnstile'
import type { TurnstileHandle } from './Turnstile'
import type { BriefPayload, Locale, ReadinessPayload, RiskLevel, RiskLevelsMeta, RiskPoint } from './types'

type ThresholdCallout = { risk: number; label: string; price: string; text: string }
type RiskLevelsChartData = {
  levels: RiskLevel[]
  meta: RiskLevelsMeta | null
}
type CurrentRiskMarker = {
  risk: number
  xAxisLabel: string
}
type CurrentRiskWindowNotice = {
  text: string
}
type DriverStatus = 'raises' | 'neutral' | 'lowers' | 'unavailable'
type ReadinessLabels = {
  freshnessCurrent: string
  staleAge: (days: number | null) => string
}
type ModelDriver = {
  id: 'trend' | 'volatility' | 'activity'
  label: string
  description: string
  status: DriverStatus
  statusLabel: string
}
type ChartLoadState<T> = {
  status: 'idle' | 'loading' | 'loaded' | 'error'
  data: T
  error: string | null
}
const COMPACT_CHART_QUERY = '(max-width: 640px)'
const ACCESSIBLE_HISTORY_POINTS = 6
const DRIVER_NEUTRAL_BAND = 0.25
const RISK_STATE_THRESHOLDS = [0.30, 0.70] as const
const PUBLIC_RISK_LEVEL_WINDOW = { min: 0.20, max: 0.80 } as const
const RISK_LEVEL_WINDOW_EPSILON = 1e-9
const AUTO_CHART_SIZE = { width: 'auto', height: 'auto' } as const
const COINMARKETCAP_HISTORICAL_DATA_URL = 'https://coinmarketcap.com/currencies/bitcoin/historical-data/'
const SUPPORT_EMAIL = 'support@minihub.app'
const SUPPORT_EMAIL_URL = `mailto:${SUPPORT_EMAIL}`
const MINIHUB_URL = 'https://minihub.app'
const COPYRIGHT_YEAR = String(new Date().getFullYear())
const Chart = lazy(() => import('./Chart'))

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}

function formatTooltipPercent(value: unknown) {
  return typeof value === 'number' ? formatPercent(value) : String(value ?? '')
}

function riskLevelAxisLabel(risk: number) {
  return `${Math.round(risk * 100)}%`
}

function formatUsd(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function formatDateLabel(timestamp: string, compact: boolean) {
  return compact ? timestamp.slice(5, 10) : timestamp.slice(0, 10)
}

function addUtcDays(isoDate: string, days: number) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const parsed = new Date(Date.UTC(year, month - 1, day))

  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== isoDate) {
    return null
  }

  parsed.setUTCDate(parsed.getUTCDate() + days)
  return parsed.toISOString().slice(0, 10)
}

function NumericValue({ children }: { children: ReactNode }) {
  return <bdi className="numeric-value" dir="ltr">{children}</bdi>
}

function TrustValue({ label, value, unavailable }: { label: string; value: string | null; unavailable: string }) {
  return (
    <>
      {label}: {value ? <NumericValue>{value}</NumericValue> : unavailable}
    </>
  )
}

function LocalizedPriceText({ text, price }: { text: string; price: string }) {
  return <LocalizedIsolatedText text={text} value={price} />
}

function LocalizedIsolatedText({ text, value }: { text: string; value: string }) {
  const [prefix, ...suffixParts] = text.split(value)
  if (suffixParts.length === 0) return <>{text}</>

  return (
    <>
      {prefix}
      <NumericValue>{value}</NumericValue>
      {suffixParts.join(value)}
    </>
  )
}

function driverStatusFromZScore(value: number | null | undefined): DriverStatus {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'unavailable'
  if (value > DRIVER_NEUTRAL_BAND) return 'raises'
  if (value < -DRIVER_NEUTRAL_BAND) return 'lowers'
  return 'neutral'
}

function driverStatusLabel(status: DriverStatus, labels: typeof copy[Locale]) {
  if (status === 'raises') return labels.driverRaises
  if (status === 'lowers') return labels.driverLowers
  if (status === 'unavailable') return labels.driverUnavailable
  return labels.driverNeutral
}

function buildModelDrivers(latest: RiskPoint, labels: typeof copy[Locale]): ModelDriver[] {
  const activityAvailable = latest.turnover_enabled
    && typeof latest.turnover === 'number'
    && Number.isFinite(latest.turnover)
    && typeof latest.z_turnover === 'number'
    && Number.isFinite(latest.z_turnover)
  const activityStatus = activityAvailable ? driverStatusFromZScore(latest.z_turnover) : 'unavailable'

  const drivers: Array<Omit<ModelDriver, 'statusLabel'>> = [
    {
      id: 'trend',
      label: labels.driverTrend,
      description: labels.driverTrendDetail,
      status: driverStatusFromZScore(latest.z_trend_dev),
    },
    {
      id: 'volatility',
      label: labels.driverVolatility,
      description: labels.driverVolatilityDetail,
      status: driverStatusFromZScore(latest.z_vol_regime),
    },
    {
      id: 'activity',
      label: labels.driverActivity,
      description: activityAvailable ? labels.driverActivityDetail : labels.driverActivityUnavailableDetail,
      status: activityStatus,
    },
  ]

  return drivers.map((driver) => ({
    ...driver,
    statusLabel: driverStatusLabel(driver.status, labels),
  }))
}

function readinessFreshnessText(readiness: ReadinessPayload, labels: ReadinessLabels) {
  return readiness.checks.data_fresh
    ? labels.freshnessCurrent
    : labels.staleAge(readiness.data.data_age_days)
}

function ReadinessFreshnessValue({ readiness, labels }: { readiness: ReadinessPayload; labels: ReadinessLabels }) {
  if (readiness.checks.data_fresh || readiness.data.data_age_days === null) {
    return <>{readinessFreshnessText(readiness, labels)}</>
  }

  const days = String(readiness.data.data_age_days)
  return <LocalizedIsolatedText text={labels.staleAge(readiness.data.data_age_days)} value={days} />
}

function validationPassed(readiness: ReadinessPayload) {
  return readiness.checks.validation_available
    && readiness.checks.risk_range_ok
    && readiness.checks.validation_has_rows
    && readiness.checks.latest_matches_validation_end
}

function nearestRiskLevel(levels: RiskLevel[], targetRisk: number) {
  return levels.reduce<RiskLevel | null>((nearest, level) => {
    if (!nearest) return level
    return Math.abs(level.risk - targetRisk) < Math.abs(nearest.risk - targetRisk) ? level : nearest
  }, null)
}

function riskInPublicChartWindow(risk: number) {
  return risk >= PUBLIC_RISK_LEVEL_WINDOW.min - RISK_LEVEL_WINDOW_EPSILON
    && risk <= PUBLIC_RISK_LEVEL_WINDOW.max + RISK_LEVEL_WINDOW_EPSILON
}

function riskLevelInPublicChartWindow(level: RiskLevel) {
  return riskInPublicChartWindow(level.risk)
}

function emptyRiskLevelsChartData(): RiskLevelsChartData {
  return { levels: [], meta: null }
}

function isRiskValue(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
}

function currentRiskValue(levelsMeta: RiskLevelsMeta | null, fallbackRisk: number | null | undefined) {
  const metadataRisk = levelsMeta?.current_risk
  const currentRisk = isRiskValue(metadataRisk) ? metadataRisk : fallbackRisk
  return isRiskValue(currentRisk) ? currentRisk : null
}

function buildCurrentRiskMarker(
  levels: RiskLevel[],
  levelsMeta: RiskLevelsMeta | null,
  fallbackRisk: number | null | undefined,
): CurrentRiskMarker | null {
  const currentRisk = currentRiskValue(levelsMeta, fallbackRisk)
  if (currentRisk === null) return null
  if (!riskInPublicChartWindow(currentRisk)) return null

  const nearestLevel = nearestRiskLevel(levels, currentRisk)
  if (!nearestLevel) return null

  return {
    risk: currentRisk,
    xAxisLabel: riskLevelAxisLabel(nearestLevel.risk),
  }
}

function buildCurrentRiskWindowNotice(
  levelsMeta: RiskLevelsMeta | null,
  fallbackRisk: number | null | undefined,
  labels: typeof copy[Locale],
): CurrentRiskWindowNotice | null {
  const currentRisk = currentRiskValue(levelsMeta, fallbackRisk)
  if (currentRisk === null || riskInPublicChartWindow(currentRisk)) return null

  const riskLabel = formatPercent(currentRisk)
  return {
    text: currentRisk < PUBLIC_RISK_LEVEL_WINDOW.min
      ? labels.riskLevelsBelowWindow(riskLabel)
      : labels.riskLevelsAboveWindow(riskLabel),
  }
}

function getCompactChartPreference() {
  return typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia(COMPACT_CHART_QUERY).matches
    : false
}

function resizeChartWhenReady(chart: { resize: (opts?: typeof AUTO_CHART_SIZE) => void }) {
  const resize = () => chart.resize(AUTO_CHART_SIZE)
  if (typeof window.requestAnimationFrame === 'function') {
    window.requestAnimationFrame(resize)
  } else {
    window.setTimeout(resize, 0)
  }
  window.setTimeout(resize, 80)
  window.setTimeout(resize, 250)
}

export default function App() {
  const [locale, setLocale] = useState<Locale>('en')
  const [latest, setLatest] = useState<RiskPoint | null>(null)
  const [historyState, setHistoryState] = useState<ChartLoadState<RiskPoint[]>>({
    status: 'idle',
    data: [],
    error: null,
  })
  const [levelsState, setLevelsState] = useState<ChartLoadState<RiskLevelsChartData>>({
    status: 'idle',
    data: emptyRiskLevelsChartData(),
    error: null,
  })
  const [brief, setBrief] = useState<BriefPayload | null>(null)
  const [readiness, setReadiness] = useState<ReadinessPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lead, setLead] = useState('')
  const [joined, setJoined] = useState(false)
  const [joinError, setJoinError] = useState<string | null>(null)
  const [joining, setJoining] = useState(false)
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null)
  const turnstileRef = useRef<TurnstileHandle>(null)
  const turnstileErrorRef = useRef(false)
  const [compactCharts, setCompactCharts] = useState(getCompactChartPreference)
  const t = copy[locale]
  const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY
  const history = historyState.data
  const levels = levelsState.data.levels
  const levelsMeta = levelsState.data.meta
  const visibleRiskLevels = useMemo(() => levels.filter(riskLevelInPublicChartWindow), [levels])
  const waitlistStatusId = 'waitlist-status'
  const waitlistErrorId = 'waitlist-error'

  useEffect(() => {
    let active = true
    Promise.all([fetchLatestRisk(), fetchBrief(), fetchReadiness()])
      .then(([latestResponse, briefResponse, readinessResponse]) => {
        if (!active) return
        setLatest(latestResponse.data)
        setBrief(briefResponse.data)
        setReadiness(readinessResponse)
      })
      .catch((err: Error) => {
        if (active) setError(err.message)
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!latest || !brief || !readiness) return
    let active = true

    setHistoryState({ status: 'loading', data: [], error: null })
    fetchRiskHistory()
      .then((historyResponse) => {
        if (!active) return
        setHistoryState({ status: 'loaded', data: historyResponse.data, error: null })
      })
      .catch((err: Error) => {
        if (!active) return
        setHistoryState({ status: 'error', data: [], error: err.message })
      })

    setLevelsState({ status: 'loading', data: emptyRiskLevelsChartData(), error: null })
    fetchRiskLevels()
      .then((levelsResponse) => {
        if (!active) return
        setLevelsState({
          status: 'loaded',
          data: { levels: levelsResponse.data, meta: levelsResponse.meta ?? null },
          error: null,
        })
      })
      .catch((err: Error) => {
        if (!active) return
        setLevelsState({ status: 'error', data: emptyRiskLevelsChartData(), error: err.message })
      })

    return () => {
      active = false
    }
  }, [latest, brief, readiness])

  useEffect(() => {
    if (!window.matchMedia) return
    const query = window.matchMedia(COMPACT_CHART_QUERY)
    const updateCompactCharts = () => setCompactCharts(query.matches)
    updateCompactCharts()
    query.addEventListener('change', updateCompactCharts)
    return () => query.removeEventListener('change', updateCompactCharts)
  }, [])

  useEffect(() => {
    const option = getLocaleOption(locale)
    document.documentElement.lang = option.lang
    document.documentElement.dir = option.dir
  }, [locale])

  const riskOption = useMemo<EChartsOption>(() => ({
    backgroundColor: 'transparent',
    animation: false,
    grid: { left: compactCharts ? 36 : 44, right: compactCharts ? 10 : 28, top: compactCharts ? 14 : 18, bottom: compactCharts ? 30 : 36 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: formatTooltipPercent,
      confine: true,
      axisPointer: {
        type: compactCharts ? 'cross' : 'line',
        label: {
          show: compactCharts,
          backgroundColor: '#151a22',
          color: '#f8fafc',
        },
      },
    },
    xAxis: {
      type: 'category',
      data: history.map((point) => point.timestamp.slice(0, 10)),
      axisLabel: {
        color: '#7e8794',
        formatter: (value: string) => formatDateLabel(value, compactCharts),
        hideOverlap: compactCharts,
      },
      axisLine: { lineStyle: { color: '#2a3441' } },
    },
    yAxis: { type: 'value', min: 0, max: 1, axisLabel: { color: '#7e8794', formatter: (value: number) => `${value * 100}%` }, splitLine: { lineStyle: { color: '#26303b' } } },
    series: [{ name: 'Risk', type: 'line', smooth: true, showSymbol: false, data: history.map((point) => point.risk), lineStyle: { width: 3, color: '#f2b84b' }, areaStyle: { color: 'rgba(242,184,75,0.12)' }, markLine: { symbol: 'none', label: { show: false }, data: RISK_STATE_THRESHOLDS.map((risk) => ({ yAxis: risk })), lineStyle: { color: '#596473', type: 'dashed' } } }],
  }), [compactCharts, history])

  const currentRiskMarker = useMemo(
    () => buildCurrentRiskMarker(visibleRiskLevels, levelsMeta, latest?.risk),
    [visibleRiskLevels, levelsMeta, latest?.risk],
  )
  const currentRiskWindowNotice = useMemo(
    () => buildCurrentRiskWindowNotice(levelsMeta, latest?.risk, t),
    [levelsMeta, latest?.risk, t],
  )

  const levelsOption = useMemo<EChartsOption>(() => ({
    backgroundColor: 'transparent',
    animation: false,
    grid: {
      left: compactCharts ? 46 : 62,
      right: compactCharts ? 8 : 22,
      top: currentRiskMarker ? (compactCharts ? 38 : 34) : (compactCharts ? 14 : 18),
      bottom: compactCharts ? 30 : 36,
    },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: visibleRiskLevels.map((row) => riskLevelAxisLabel(row.risk)), axisLabel: { color: '#7e8794', hideOverlap: compactCharts }, axisLine: { lineStyle: { color: '#2a3441' } } },
    yAxis: { type: 'value', axisLabel: { color: '#7e8794', formatter: (value: number) => `$${Math.round(value / 1000)}k` }, splitLine: { lineStyle: { color: '#26303b' } } },
    series: [{
      name: 'Price',
      type: 'bar',
      barMaxWidth: compactCharts ? 5 : 9,
      data: visibleRiskLevels.map((row) => row.price_usd),
      itemStyle: { color: '#5bd6c6', borderRadius: [4, 4, 0, 0] },
      markLine: currentRiskMarker ? {
        symbol: 'none',
        silent: true,
        label: {
          show: true,
          formatter: `${t.currentRisk}: ${formatPercent(currentRiskMarker.risk)}`,
          position: 'end',
          color: '#f8fafc',
          backgroundColor: 'rgba(8, 13, 22, 0.88)',
          borderRadius: 4,
          padding: [3, 6],
          fontSize: compactCharts ? 10 : 11,
        },
        data: [{ xAxis: currentRiskMarker.xAxisLabel }],
        lineStyle: { color: '#f2b84b', width: 2, type: 'solid' },
      } : undefined,
    }],
  }), [compactCharts, currentRiskMarker, visibleRiskLevels, t.currentRisk])

  const thresholdCallouts = useMemo<ThresholdCallout[]>(() => {
    return RISK_STATE_THRESHOLDS.flatMap((targetRisk, index) => {
      const level = nearestRiskLevel(levels, targetRisk)
      if (!level) return []
      const label = t.riskZones[index]
      const price = formatUsd(level.price_usd)
      return [{
        risk: targetRisk,
        label,
        price,
        text: t.thresholdNear(label, price),
      }]
    })
  }, [levels, t])
  const accessibleHistory = useMemo(() => history.slice(-ACCESSIBLE_HISTORY_POINTS), [history])

  async function submitWaitlist(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = lead.trim()
    if (joining || !turnstileToken) return
    if (!value) {
      setTurnstileToken(null)
      turnstileRef.current?.reset()
      return
    }
    setJoining(true)
    setJoinError(null)
    try {
      await joinWaitlist({ contact: value, locale, source: 'landing', turnstile_token: turnstileToken })
      setLead('')
      setJoined(true)
    } catch (error) {
      setJoined(false)
      if (error instanceof ApiError && error.status === 403) {
        setJoinError(t.turnstileError)
      } else if (error instanceof ApiError && error.status === 503) {
        setJoinError(t.turnstileUnavailable)
      } else {
        setJoinError(t.joinError)
      }
    } finally {
      setTurnstileToken(null)
      turnstileRef.current?.reset()
      setJoining(false)
    }
  }

  if (error && !latest) {
    return (
      <main className="shell centered">
        <section className="empty-state error-state" aria-live="polite">
          <ShieldAlert size={30} />
          <h1>{t.loadErrorTitle}</h1>
          <p>{t.loadErrorBody}</p>
          <p className="error-detail">{error}</p>
        </section>
      </main>
    )
  }

  if (!latest || !brief || !readiness) {
    return <main className="shell centered"><p className="loading">{t.loading}</p></main>
  }

  const briefSection = brief.sections[locale] ?? brief.sections.en
  const state = stateLabel(latest.risk_state, locale)
  const ready = readiness.status === 'ready'
  const validationOk = validationPassed(readiness)
  const methodologyVersion = readiness.data.methodology_version ?? t.unavailable
  const modelPriceUsd = latest.model_price_usd ?? latest.price_usd
  const hasDailyRange = typeof latest.low_usd === 'number' && typeof latest.high_usd === 'number'
  const chartCurrentSummary = t.chartCurrentSummary(
    latest.timestamp.slice(0, 10),
    formatPercent(latest.risk),
    state,
    formatUsd(modelPriceUsd),
    hasDailyRange ? t.chartCurrentRange(formatUsd(latest.low_usd as number), formatUsd(latest.high_usd as number)) : '',
  )
  const riskLevelsSummary = currentRiskMarker
    ? `${t.riskLevelsAlternativeNote} ${t.currentRisk}: ${formatPercent(currentRiskMarker.risk)}.`
    : currentRiskWindowNotice
      ? `${t.riskLevelsAlternativeNote} ${currentRiskWindowNotice.text}`
    : t.riskLevelsAlternativeNote
  const modelDrivers = buildModelDrivers(latest, t)
  const reportDate = ready && readiness.checks.data_fresh && readiness.data.latest_date
    ? addUtcDays(readiness.data.latest_date, 1)
    : null
  const primaryDateLabel = reportDate ? t.reportDate : t.updated
  const primaryDateValue = reportDate ?? latest.timestamp.slice(0, 10)

  return (
    <main className="shell">
      <nav className="topbar" aria-label={t.languageNavigation}>
        <div className="brand"><Radio size={18} /> BTC Risk Brief</div>
        <div className="top-actions">
          <a className="methodology-link" href="#methodology"><ExternalLink size={15} /> {t.methodologyLink}</a>
          <LanguageSelect
            label={t.languageSelector}
            locale={locale}
            options={localeOptions}
            onLocaleChange={(nextLocale) => {
              setTurnstileToken(null)
              setLocale(nextLocale)
            }}
          />
        </div>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">{t.eyebrow}</p>
          <h1>{t.title}</h1>
          <p className="subtitle">{t.subtitle}</p>
        </div>
        <div className={`risk-dial ${latest.risk_state}`}>
          <span>{t.currentRisk}</span>
          <strong><NumericValue>{formatPercent(latest.risk)}</NumericValue></strong>
          <em>{state}</em>
        </div>
      </section>

      <section className="metrics-strip" aria-label={t.currentRisk}>
        <div className="price-metric">
          <span>{t.price}</span>
          <div className={`price-input-grid ${hasDailyRange ? 'with-range' : 'model-only'}`}>
            <div className="price-input-value">
              <em>{t.modelPrice}</em>
              <strong><NumericValue>{formatUsd(modelPriceUsd)}</NumericValue></strong>
            </div>
            {hasDailyRange && (
              <>
                <div className="price-input-value">
                  <em>{t.low}</em>
                  <strong><NumericValue>{formatUsd(latest.low_usd as number)}</NumericValue></strong>
                </div>
                <div className="price-input-value">
                  <em>{t.high}</em>
                  <strong><NumericValue>{formatUsd(latest.high_usd as number)}</NumericValue></strong>
                </div>
              </>
            )}
          </div>
        </div>
        <div className="freshness-metric">
          <span>{primaryDateLabel}</span>
          <strong><NumericValue>{primaryDateValue}</NumericValue></strong>
          <p className={`readiness-badge ${readiness.status}`}>
            {ready ? <CheckCircle2 size={15} /> : <TriangleAlert size={15} />}
            {ready ? t.readinessReady : t.readinessDegraded}
          </p>
          <em>{validationOk ? t.validationPassed : t.validationNeedsAttention}</em>
          <em><TrustValue label={t.latestCompletedDay} value={readiness.data.latest_date} unavailable={t.unavailable} /></em>
          <em><ReadinessFreshnessValue readiness={readiness} labels={t} /></em>
          <em><TrustValue label={t.coverageThrough} value={readiness.data.covered_end} unavailable={t.unavailable} /></em>
        </div>
        <div>
          <span>{t.riskChange}</span>
          <strong className={brief.delta_risk >= 0 ? 'up' : 'down'}>
            <NumericValue>{brief.delta_risk >= 0 ? '+' : ''}{formatPercent(brief.delta_risk)}</NumericValue>
          </strong>
          <em>{t.riskChangeContext}</em>
        </div>
      </section>

      <section className="brief-grid">
        <article className="brief-panel lead-panel">
          <h2>{t.brief}</h2>
          <p>{briefSection.summary}</p>
        </article>
        <article className="brief-panel"><h3>{t.changed}</h3><p>{briefSection.what_changed}</p></article>
        <article className="brief-panel"><h3>{t.avoid}</h3><p>{briefSection.avoid_now}</p></article>
        <article className="brief-panel"><h3>{t.confirm}</h3><p>{briefSection.confirm_next}</p></article>
      </section>

      <section className="model-drivers" aria-labelledby="model-drivers-heading">
        <div className="model-drivers-copy">
          <h2 id="model-drivers-heading">{t.modelDrivers}</h2>
          <p>{t.modelDriversBody}</p>
        </div>
        <div className="driver-list">
          {modelDrivers.map((driver) => (
            <article className={`driver-card ${driver.status}`} key={driver.id}>
              <span>{driver.label}</span>
              <strong>{driver.statusLabel}</strong>
              <p>{driver.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="methodology" className="trust-layer" aria-label={t.methodology}>
        <article className="trust-panel">
          <h2>{t.methodology}</h2>
          <p>{t.methodologyBody}</p>
          <dl>
            <div><dt>{t.methodologyVersion}</dt><dd>{methodologyVersion}</dd></div>
            <div><dt>{t.dataSource}</dt><dd><a className="source-link" href={COINMARKETCAP_HISTORICAL_DATA_URL} target="_blank" rel="noreferrer">CoinMarketCap <ExternalLink size={14} aria-hidden="true" /></a></dd></div>
            <div><dt>{t.latestCompletedDay}</dt><dd>{readiness.data.latest_date ? <NumericValue>{readiness.data.latest_date}</NumericValue> : t.unavailable}</dd></div>
            <div><dt>{t.coverageThrough}</dt><dd>{readiness.data.covered_end ? <NumericValue>{readiness.data.covered_end}</NumericValue> : t.unavailable}</dd></div>
          </dl>
          <p className="disclaimer">{t.disclaimer}</p>
        </article>
      </section>

      <section className="waitlist">
        <div>
          <Bell size={24} />
          <h2>{t.waitlistTitle}</h2>
          <p>{t.waitlistBody}</p>
        </div>
        <form className="lead-form" onSubmit={submitWaitlist}>
          <input
            value={lead}
            onChange={(event) => setLead(event.target.value)}
            placeholder={t.placeholder}
            aria-label={t.placeholder}
            aria-invalid={joinError ? 'true' : undefined}
            aria-describedby={joinError ? waitlistErrorId : undefined}
            dir="ltr"
          />
          <Turnstile
            ref={turnstileRef}
            sitekey={turnstileSiteKey}
            action="waitlist"
            language={getLocaleOption(locale).lang}
            onVerify={(token) => {
              setTurnstileToken(token)
              if (token && turnstileErrorRef.current) {
                turnstileErrorRef.current = false
                setJoinError(null)
              }
            }}
            onError={() => {
              turnstileErrorRef.current = true
              setTurnstileToken(null)
              setJoined(false)
              setJoinError(t.turnstileError)
            }}
          />
          <button type="submit" disabled={joining || !turnstileToken} aria-busy={joining}>
            <Send size={16} /> {joining ? t.joining : t.join}
          </button>
        </form>
        {joining && (
          <p id={waitlistStatusId} className="sr-only" role="status" aria-live="polite">
            {t.joining}
          </p>
        )}
        {joined && !joining && (
          <p id={waitlistStatusId} className="joined" role="status" aria-live="polite">
            {t.joined}
          </p>
        )}
        {joinError && (
          <p id={waitlistErrorId} className="joined error-text" role="alert">
            {joinError}
          </p>
        )}
        <details className="privacy-note">
          <summary><ShieldAlert size={15} /> {t.privacyNoteTitle}</summary>
          <div className="privacy-note-body">
            <p>{t.privacyNoteIntro}</p>
            <p>{t.privacyNoteWaitlist}</p>
            <p>{t.privacyNoteTurnstile}</p>
            <p>{t.privacyNoteLogs}</p>
            <p>{t.privacyNoteLimits}</p>
            <p>{t.privacyNoteAnalytics}</p>
          </div>
        </details>
      </section>

      <section className="charts">
        <article className="chart-panel" aria-labelledby="risk-history-heading">
          <div className="chart-heading">
            <h2 id="risk-history-heading">{t.history}</h2>
            <div className="risk-thresholds" aria-label={t.thresholdColumn}>
              {t.riskZones.map((label) => <span key={label}>{label}</span>)}
            </div>
          </div>
          {thresholdCallouts.length > 0 && (
            <div className="threshold-callouts" aria-label={t.thresholdCallouts}>
              {thresholdCallouts.map((callout) => (
                <span key={callout.risk}>
                  <LocalizedPriceText text={callout.text} price={callout.price} />
                </span>
              ))}
            </div>
          )}
          <section className="sr-only" aria-labelledby="risk-history-alternative-heading">
            <h3 id="risk-history-alternative-heading">{t.riskHistoryAlternative}</h3>
            <p id="risk-history-chart-summary">{chartCurrentSummary}</p>
            {accessibleHistory.length > 0 && (
              <>
                <p id="risk-history-chart-note">{t.riskHistoryAlternativeNote(accessibleHistory.length)}</p>
                <table aria-describedby="risk-history-chart-summary risk-history-chart-note">
                  <caption>{t.recentRiskHistoryTable}</caption>
                  <thead>
                    <tr>
                      <th scope="col">{t.dateColumn}</th>
                      <th scope="col">{t.riskColumn}</th>
                      <th scope="col">{t.priceColumn}</th>
                      <th scope="col">{t.stateColumn}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accessibleHistory.map((point) => (
                      <tr key={point.timestamp}>
                        <td>{point.timestamp.slice(0, 10)}</td>
                        <td>{formatPercent(point.risk)}</td>
                        <td>{formatUsd(point.price_usd)}</td>
                        <td>{stateLabel(point.risk_state, locale)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </section>
          {historyState.status === 'loading' || historyState.status === 'idle' ? (
            <div className="chart-placeholder" role="status">{t.chartLoading}</div>
          ) : historyState.status === 'error' ? (
            <div className="chart-empty chart-error" role="alert">{t.historyError}</div>
          ) : history.length > 0 ? (
            <div className="chart-visual" role="img" aria-labelledby="risk-history-heading" aria-describedby="risk-history-chart-summary risk-history-chart-note">
              <Suspense fallback={<div className="chart-placeholder" role="status">{t.chartLoading}</div>}>
                <Chart option={riskOption} notMerge opts={AUTO_CHART_SIZE} onChartReady={resizeChartWhenReady} style={{ height: 360, width: '100%' }} />
              </Suspense>
            </div>
          ) : (
            <div className="chart-empty" role="status">{t.historyEmpty}</div>
          )}
        </article>
        <article className="chart-panel" aria-labelledby="risk-levels-heading">
          <h2 id="risk-levels-heading">{t.levels}</h2>
          {currentRiskWindowNotice && visibleRiskLevels.length > 0 && (
            <p className="risk-level-window-note">{currentRiskWindowNotice.text}</p>
          )}
          {levels.length > 0 && (
            <section className="sr-only" aria-labelledby="risk-levels-alternative-heading">
              <h3 id="risk-levels-alternative-heading">{t.riskLevelsAlternative}</h3>
              <p id="risk-levels-chart-summary">{riskLevelsSummary}</p>
              {thresholdCallouts.length > 0 && (
                <table aria-describedby="risk-levels-chart-summary">
                  <caption>{t.riskThresholdPriceTable}</caption>
                  <thead>
                    <tr>
                      <th scope="col">{t.thresholdColumn}</th>
                      <th scope="col">{t.bandColumn}</th>
                      <th scope="col">{t.nearestModelPriceColumn}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {thresholdCallouts.map((callout) => (
                      <tr key={callout.risk}>
                        <td>{formatPercent(callout.risk)}</td>
                        <td>{callout.label}</td>
                        <td>{callout.price}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          )}
          {levelsState.status === 'loading' || levelsState.status === 'idle' ? (
            <div className="chart-placeholder" role="status">{t.chartLoading}</div>
          ) : levelsState.status === 'error' ? (
            <div className="chart-empty chart-error" role="alert">{t.levelsError}</div>
          ) : visibleRiskLevels.length > 0 ? (
            <div className="chart-visual" role="img" aria-labelledby="risk-levels-heading" aria-describedby="risk-levels-chart-summary">
              <Suspense fallback={<div className="chart-placeholder" role="status">{t.chartLoading}</div>}>
                <Chart option={levelsOption} notMerge opts={AUTO_CHART_SIZE} onChartReady={resizeChartWhenReady} style={{ height: 360, width: '100%' }} />
              </Suspense>
            </div>
          ) : (
            <div className="chart-empty" role="status">{t.levelsEmpty}</div>
          )}
        </article>
      </section>
      <footer className="bottom-panel" aria-label={t.footerAriaLabel}>
        <a className="bottom-panel-link footer-token" href={SUPPORT_EMAIL_URL} dir="ltr">
          {SUPPORT_EMAIL}
        </a>
        <span className="footer-legal">
          &copy; <NumericValue>{COPYRIGHT_YEAR}</NumericValue> Minihub
        </span>
        <a className="bottom-panel-link footer-token" href={MINIHUB_URL} target="_blank" rel="noreferrer" dir="ltr">
          {MINIHUB_URL}
          <ExternalLink size={14} aria-hidden="true" />
        </a>
        <nav className="footer-dev-links" aria-label={t.developerLinksAriaLabel}>
          <a
            className="bottom-panel-link footer-token"
            href="https://docs.bitcoinriskbrief.minihub.app/"
            target="_blank"
            rel="noreferrer"
            dir="ltr"
          >
            Docs
            <ExternalLink size={14} aria-hidden="true" />
          </a>
          <a
            className="bottom-panel-link footer-token"
            href="https://docs.bitcoinriskbrief.minihub.app/engineering/api-reference/"
            target="_blank"
            rel="noreferrer"
            dir="ltr"
          >
            API
            <ExternalLink size={14} aria-hidden="true" />
          </a>
          <a className="bottom-panel-link footer-token" href="/llms.txt" dir="ltr">
            llms.txt
          </a>
        </nav>
      </footer>
    </main>
  )
}
