import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import type { EChartsOption } from 'echarts'
import { Bell, CheckCircle2, ExternalLink, Languages, Radio, Send, ShieldAlert, TriangleAlert } from 'lucide-react'
import { fetchBrief, fetchLatestRisk, fetchReadiness, fetchRiskHistory, fetchRiskLevels, joinWaitlist } from './api'
import type { BriefPayload, ReadinessPayload, RiskLevel, RiskPoint } from './types'

type Locale = 'en' | 'ru'
type ThresholdCallout = { risk: number; label: string; price: string; text: string }
type ChartLoadState<T> = {
  status: 'idle' | 'loading' | 'loaded' | 'error'
  data: T
  error: string | null
}
const COMPACT_CHART_QUERY = '(max-width: 640px)'
const ACCESSIBLE_HISTORY_POINTS = 6
const AUTO_CHART_SIZE = { width: 'auto', height: 'auto' } as const
const Chart = lazy(() => import('./Chart'))

const copy = {
  en: {
    eyebrow: 'Daily BTC Risk Signal',
    title: 'Bitcoin Risk Brief',
    subtitle: 'A focused daily read on whether BTC is overheated, neutral, or washed out.',
    updated: 'Updated',
    currentRisk: 'Current risk',
    price: 'BTC price model input',
    modelPrice: 'Model price',
    low: 'Low',
    high: 'High',
    riskChange: 'Risk change',
    riskChangeContext: 'vs previous observation',
    riskZones: ['Low / Neutral', 'Neutral / High'],
    readinessReady: 'Readiness ready',
    readinessDegraded: 'Readiness degraded',
    validationPassed: 'Validation passed',
    validationNeedsAttention: 'Validation needs attention',
    latestDate: 'Latest date',
    coveredEnd: 'Covered end',
    freshAge: (days: number | null) => (days === null ? 'Freshness unknown' : `Fresh: ${days} ${days === 1 ? 'day' : 'days'} old`),
    staleAge: (days: number | null) => (days === null ? 'Data age unavailable' : `Data is ${days} ${days === 1 ? 'day' : 'days'} old`),
    methodology: 'Methodology',
    methodologyLink: 'View methodology',
    methodologyVersion: 'Methodology version',
    methodologyBody: 'The public signal uses the canonical BTC risk model and the latest validated CoinMarketCap CSV import.',
    disclaimer: 'Risk levels are scenario outputs, not financial advice or trading instructions.',
    thresholdCallouts: 'Nearest threshold prices',
    thresholdNear: (label: string, price: string) => `${label} near ${price}`,
    riskHistoryAlternative: 'Risk history chart data alternative',
    riskLevelsAlternative: 'Risk level chart data alternative',
    chartCurrentSummary: (date: string, risk: string, state: string, modelPrice: string, range: string) => `Latest observation ${date}: current risk is ${risk} (${state}) and model price is ${modelPrice}${range}.`,
    chartCurrentRange: (low: string, high: string) => `, with latest daily low ${low} and high ${high}`,
    riskHistoryAlternativeNote: (count: number) => `The table lists the ${count} most recent risk history observations available to the chart.`,
    riskLevelsAlternativeNote: 'The table lists the key risk threshold prices used with the risk levels chart.',
    dateColumn: 'Date',
    riskColumn: 'Risk',
    priceColumn: 'BTC price',
    stateColumn: 'Risk state',
    thresholdColumn: 'Risk threshold',
    bandColumn: 'Band',
    nearestModelPriceColumn: 'Nearest model price',
    recentRiskHistoryTable: 'Recent risk history table',
    riskThresholdPriceTable: 'Risk threshold price table',
    history: 'Risk history',
    levels: 'Risk levels',
    brief: 'Today brief',
    changed: 'What changed',
    avoid: 'Avoid now',
    confirm: 'Confirm next',
    waitlistTitle: 'Get the daily signal',
    waitlistBody: 'Leave an email or Telegram handle. The first test cohort gets the risk alert free.',
    placeholder: 'email or @telegram',
    join: 'Join waitlist',
    joined: 'Saved. You are on the Bitcoin Risk Brief waitlist.',
    joinError: 'Enter a valid email or Telegram handle.',
    joining: 'Saving...',
    privacyNoteTitle: 'Privacy, terms, and disclaimer',
    privacyNoteIntro: 'Bitcoin Risk Brief is informational research only, not financial advice, investment advice, or a trading recommendation.',
    privacyNoteWaitlist: 'The waitlist stores the contact you submit, a normalized copy, contact type, locale, source, status, and timestamps.',
    privacyNoteLogs: 'Operational logs may include request method, path, status, client key, Cloudflare ray ID, cache status, and timing.',
    privacyNoteLimits: 'Do not enter sensitive information. No buy, sell, portfolio, or trading action is recommended, and no paid support SLA is provided.',
    privacyNoteAnalytics: 'The current app source does not include product analytics or tracking-cookie code.',
    loading: 'Loading risk data...',
    empty: 'No collected data yet. Run the collector backfill to populate TimescaleDB.',
    loadErrorTitle: 'Risk data is temporarily unavailable',
    loadErrorBody: 'The page could not load the latest risk payload. Treat the signal as unavailable until the API recovers.',
    chartLoading: 'Loading chart...',
    historyEmpty: 'Risk history is unavailable until observations are loaded.',
    levelsEmpty: 'Risk levels are unavailable until the latest model input is ready.',
    historyError: 'Risk history is temporarily unavailable.',
    levelsError: 'Risk levels are temporarily unavailable.',
  },
  ru: {
    eyebrow: 'Ежедневный BTC риск-сигнал',
    title: 'Bitcoin Risk Brief',
    subtitle: 'Короткий ежедневный ответ: BTC перегрет, нейтрален или в зоне дисконта.',
    updated: 'Обновлено',
    currentRisk: 'Текущий риск',
    price: 'Цена BTC в модели',
    modelPrice: 'Цена модели',
    low: 'Мин.',
    high: 'Макс.',
    riskChange: 'Изменение риска',
    riskChangeContext: 'к прошлому наблюдению',
    riskZones: ['Низкий / Нейтральный', 'Нейтральный / Высокий'],
    readinessReady: 'Готовность подтверждена',
    readinessDegraded: 'Готовность снижена',
    validationPassed: 'Валидация пройдена',
    validationNeedsAttention: 'Валидация требует внимания',
    latestDate: 'Последняя дата',
    coveredEnd: 'Покрыто до',
    freshAge: (days: number | null) => (days === null ? 'Свежесть неизвестна' : `Свежесть: ${days} дн.`),
    staleAge: (days: number | null) => (days === null ? 'Возраст данных неизвестен' : `Данным ${days} дн.`),
    methodology: 'Методология',
    methodologyLink: 'Методология',
    methodologyVersion: 'Версия методологии',
    methodologyBody: 'Публичный сигнал использует каноническую BTC risk-модель и последний валидированный импорт CoinMarketCap CSV.',
    disclaimer: 'Уровни риска - сценарные расчеты, а не финансовый совет или торговая инструкция.',
    thresholdCallouts: 'Ближайшие пороги цены',
    thresholdNear: (label: string, price: string) => `${label}: около ${price}`,
    riskHistoryAlternative: 'Альтернатива данным графика истории риска',
    riskLevelsAlternative: 'Альтернатива данным графика уровней риска',
    chartCurrentSummary: (date: string, risk: string, state: string, modelPrice: string, range: string) => `Последнее наблюдение ${date}: текущий риск ${risk} (${state}), цена модели ${modelPrice}${range}.`,
    chartCurrentRange: (low: string, high: string) => `, дневной минимум ${low}, максимум ${high}`,
    riskHistoryAlternativeNote: (count: number) => `Таблица показывает ${count} последних наблюдений риска, доступных на графике.`,
    riskLevelsAlternativeNote: 'Таблица показывает ключевые пороговые цены, используемые с графиком уровней риска.',
    dateColumn: 'Дата',
    riskColumn: 'Риск',
    priceColumn: 'Цена BTC',
    stateColumn: 'Состояние риска',
    thresholdColumn: 'Порог риска',
    bandColumn: 'Диапазон',
    nearestModelPriceColumn: 'Ближайшая цена модели',
    recentRiskHistoryTable: 'Таблица недавней истории риска',
    riskThresholdPriceTable: 'Таблица пороговых цен риска',
    history: 'История риска',
    levels: 'Уровни риска',
    brief: 'Сегодняшний бриф',
    changed: 'Что изменилось',
    avoid: 'Чего избегать',
    confirm: 'Что подтвердить',
    waitlistTitle: 'Получать ежедневный сигнал',
    waitlistBody: 'Оставь email или Telegram. Первая тестовая группа получит риск-алерт бесплатно.',
    placeholder: 'email или @telegram',
    join: 'В лист ожидания',
    joined: 'Сохранено. Ты в листе ожидания Bitcoin Risk Brief.',
    joinError: 'Укажи корректный email или Telegram.',
    joining: 'Сохраняю...',
    privacyNoteTitle: 'Приватность, условия и дисклеймер',
    privacyNoteIntro: 'Bitcoin Risk Brief - только информационная аналитика, не финансовый или инвестиционный совет и не торговая рекомендация.',
    privacyNoteWaitlist: 'Лист ожидания хранит введенный контакт, нормализованную копию, тип контакта, язык, источник, статус и временные метки.',
    privacyNoteLogs: 'Операционные логи могут включать метод запроса, путь, статус, client key, Cloudflare ray ID, cache-статус и время выполнения.',
    privacyNoteLimits: 'Не вводи конфиденциальную информацию. Покупка, продажа, портфельное или торговое действие не рекомендуется, платный SLA поддержки не предоставляется.',
    privacyNoteAnalytics: 'В текущем исходном коде приложения нет product analytics или tracking-cookie кода.',
    loading: 'Загружаю risk data...',
    empty: 'Данных пока нет. Запусти collector backfill, чтобы заполнить TimescaleDB.',
    loadErrorTitle: 'Данные о риске временно недоступны',
    loadErrorBody: 'Страница не смогла загрузить последний пакет данных о риске. Считай сигнал недоступным, пока API не восстановится.',
    chartLoading: 'Загружаю график...',
    historyEmpty: 'История риска недоступна, пока наблюдения не загружены.',
    levelsEmpty: 'Уровни риска недоступны, пока нет последнего входа модели.',
    historyError: 'История риска временно недоступна.',
    levelsError: 'Уровни риска временно недоступны.',
  },
} as const

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}

function formatTooltipPercent(value: unknown) {
  return typeof value === 'number' ? formatPercent(value) : String(value ?? '')
}

function formatUsd(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function formatDateLabel(timestamp: string, compact: boolean) {
  return compact ? timestamp.slice(5, 10) : timestamp.slice(0, 10)
}

function stateLabel(state: string, locale: Locale) {
  const labels = {
    en: { low: 'Low', neutral: 'Neutral', high: 'High' },
    ru: { low: 'Низкий', neutral: 'Нейтральный', high: 'Высокий' },
  }
  return labels[locale][state as 'low' | 'neutral' | 'high'] ?? state
}

function formatTrustValue(label: string, value: string | null) {
  return `${label}: ${value ?? 'unavailable'}`
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
  const [levelsState, setLevelsState] = useState<ChartLoadState<RiskLevel[]>>({
    status: 'idle',
    data: [],
    error: null,
  })
  const [brief, setBrief] = useState<BriefPayload | null>(null)
  const [readiness, setReadiness] = useState<ReadinessPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lead, setLead] = useState('')
  const [joined, setJoined] = useState(false)
  const [joinError, setJoinError] = useState<string | null>(null)
  const [joining, setJoining] = useState(false)
  const [compactCharts, setCompactCharts] = useState(getCompactChartPreference)
  const t = copy[locale]
  const history = historyState.data
  const levels = levelsState.data
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

    setLevelsState({ status: 'loading', data: [], error: null })
    fetchRiskLevels()
      .then((levelsResponse) => {
        if (!active) return
        setLevelsState({ status: 'loaded', data: levelsResponse.data, error: null })
      })
      .catch((err: Error) => {
        if (!active) return
        setLevelsState({ status: 'error', data: [], error: err.message })
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

  const riskOption = useMemo<EChartsOption>(() => ({
    backgroundColor: 'transparent',
    animation: false,
    grid: { left: compactCharts ? 36 : 44, right: compactCharts ? 10 : 28, top: compactCharts ? 14 : 18, bottom: compactCharts ? 30 : 36 },
    tooltip: { trigger: 'axis', valueFormatter: formatTooltipPercent },
    xAxis: { type: 'category', data: history.map((point) => formatDateLabel(point.timestamp, compactCharts)), axisLabel: { color: '#7e8794', hideOverlap: compactCharts }, axisLine: { lineStyle: { color: '#2a3441' } } },
    yAxis: { type: 'value', min: 0, max: 1, axisLabel: { color: '#7e8794', formatter: (value: number) => `${value * 100}%` }, splitLine: { lineStyle: { color: '#26303b' } } },
    series: [{ name: 'Risk', type: 'line', smooth: true, showSymbol: false, data: history.map((point) => point.risk), lineStyle: { width: 3, color: '#f2b84b' }, areaStyle: { color: 'rgba(242,184,75,0.12)' }, markLine: { symbol: 'none', label: { show: false }, data: [{ yAxis: 0.35 }, { yAxis: 0.65 }], lineStyle: { color: '#596473', type: 'dashed' } } }],
  }), [compactCharts, history])

  const levelsOption = useMemo<EChartsOption>(() => ({
    backgroundColor: 'transparent',
    animation: false,
    grid: { left: compactCharts ? 46 : 62, right: compactCharts ? 8 : 22, top: compactCharts ? 14 : 18, bottom: compactCharts ? 30 : 36 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: levels.map((row) => `${Math.round(row.risk * 100)}%`), axisLabel: { color: '#7e8794', hideOverlap: compactCharts }, axisLine: { lineStyle: { color: '#2a3441' } } },
    yAxis: { type: 'value', axisLabel: { color: '#7e8794', formatter: (value: number) => `$${Math.round(value / 1000)}k` }, splitLine: { lineStyle: { color: '#26303b' } } },
    series: [{ name: 'Price', type: 'bar', barMaxWidth: compactCharts ? 5 : 9, data: levels.map((row) => row.price_usd), itemStyle: { color: '#5bd6c6', borderRadius: [4, 4, 0, 0] } }],
  }), [compactCharts, levels])

  const thresholdCallouts = useMemo<ThresholdCallout[]>(() => {
    return [0.35, 0.65].flatMap((targetRisk, index) => {
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

  async function submitWaitlist(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = lead.trim()
    if (!value || joining) return
    setJoining(true)
    setJoinError(null)
    try {
      await joinWaitlist({ contact: value, locale, source: 'landing' })
      setJoined(true)
    } catch {
      setJoined(false)
      setJoinError(t.joinError)
    } finally {
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

  const briefSection = brief.sections[locale]
  const state = stateLabel(latest.risk_state, locale)
  const ready = readiness.status === 'ready'
  const validationOk = validationPassed(readiness)
  const methodologyVersion = readiness.data.methodology_version ?? 'unknown'
  const modelPriceUsd = latest.model_price_usd ?? latest.price_usd
  const hasDailyRange = typeof latest.low_usd === 'number' && typeof latest.high_usd === 'number'
  const chartCurrentSummary = t.chartCurrentSummary(
    latest.timestamp.slice(0, 10),
    formatPercent(latest.risk),
    state,
    formatUsd(modelPriceUsd),
    hasDailyRange ? t.chartCurrentRange(formatUsd(latest.low_usd as number), formatUsd(latest.high_usd as number)) : '',
  )

  return (
    <main className="shell">
      <nav className="topbar" aria-label="Language">
        <div className="brand"><Radio size={18} /> BTC Risk Brief</div>
        <div className="top-actions">
          <a className="methodology-link" href="#methodology"><ExternalLink size={15} /> {t.methodologyLink}</a>
          <button className="lang" onClick={() => setLocale(locale === 'en' ? 'ru' : 'en')}><Languages size={16} /> {locale === 'en' ? 'RU' : 'EN'}</button>
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
          <strong>{formatPercent(latest.risk)}</strong>
          <em>{state}</em>
        </div>
      </section>

      <section className="metrics-strip" aria-label="Current state">
        <div className="price-metric">
          <span>{t.price}</span>
          <div className={`price-input-grid ${hasDailyRange ? 'with-range' : 'model-only'}`}>
            <div className="price-input-value">
              <em>{t.modelPrice}</em>
              <strong>{formatUsd(modelPriceUsd)}</strong>
            </div>
            {hasDailyRange && (
              <>
                <div className="price-input-value">
                  <em>{t.low}</em>
                  <strong>{formatUsd(latest.low_usd as number)}</strong>
                </div>
                <div className="price-input-value">
                  <em>{t.high}</em>
                  <strong>{formatUsd(latest.high_usd as number)}</strong>
                </div>
              </>
            )}
          </div>
        </div>
        <div className="freshness-metric">
          <span>{t.updated}</span>
          <strong>{latest.timestamp.slice(0, 10)}</strong>
          <p className={`readiness-badge ${readiness.status}`}>
            {ready ? <CheckCircle2 size={15} /> : <TriangleAlert size={15} />}
            {ready ? t.readinessReady : t.readinessDegraded}
          </p>
          <em>{validationOk ? t.validationPassed : t.validationNeedsAttention}</em>
          <em>{formatTrustValue(t.latestDate, readiness.data.latest_date)}</em>
          <em>{ready && readiness.checks.data_fresh ? t.freshAge(readiness.data.data_age_days) : t.staleAge(readiness.data.data_age_days)}</em>
          <em>{formatTrustValue(t.coveredEnd, readiness.data.covered_end)}</em>
        </div>
        <div><span>{t.riskChange}</span><strong className={brief.delta_risk >= 0 ? 'up' : 'down'}>{brief.delta_risk >= 0 ? '+' : ''}{formatPercent(brief.delta_risk)}</strong><em>{t.riskChangeContext}</em></div>
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

      <section id="methodology" className="trust-layer" aria-label={t.methodology}>
        <article className="trust-panel">
          <h2>{t.methodology}</h2>
          <p>{t.methodologyBody}</p>
          <dl>
            <div><dt>{t.methodologyVersion}</dt><dd>{methodologyVersion}</dd></div>
            <div><dt>{t.latestDate}</dt><dd>{readiness.data.latest_date ?? 'unavailable'}</dd></div>
            <div><dt>{t.coveredEnd}</dt><dd>{readiness.data.covered_end ?? 'unavailable'}</dd></div>
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
          />
          <button type="submit" disabled={joining} aria-busy={joining}>
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
            <div className="risk-thresholds" aria-label="Risk thresholds">
              {t.riskZones.map((label) => <span key={label}>{label}</span>)}
            </div>
          </div>
          {thresholdCallouts.length > 0 && (
            <div className="threshold-callouts" aria-label={t.thresholdCallouts}>
              {thresholdCallouts.map((callout) => <span key={callout.risk}>{callout.text}</span>)}
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
          {thresholdCallouts.length > 0 && (
            <section className="sr-only" aria-labelledby="risk-levels-alternative-heading">
              <h3 id="risk-levels-alternative-heading">{t.riskLevelsAlternative}</h3>
              <p id="risk-levels-chart-summary">{t.riskLevelsAlternativeNote}</p>
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
            </section>
          )}
          {levelsState.status === 'loading' || levelsState.status === 'idle' ? (
            <div className="chart-placeholder" role="status">{t.chartLoading}</div>
          ) : levelsState.status === 'error' ? (
            <div className="chart-empty chart-error" role="alert">{t.levelsError}</div>
          ) : levels.length > 0 ? (
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
    </main>
  )
}
