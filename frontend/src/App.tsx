import { useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Bell, Languages, Radio, Send, ShieldAlert } from 'lucide-react'
import { fetchBrief, fetchLatestRisk, fetchRiskHistory, fetchRiskLevels, joinWaitlist } from './api'
import type { BriefPayload, RiskLevel, RiskPoint } from './types'

type Locale = 'en' | 'ru'

const copy = {
  en: {
    eyebrow: 'Daily BTC Risk Signal',
    title: 'Bitcoin Risk Brief',
    subtitle: 'A focused daily read on whether BTC is overheated, neutral, or washed out.',
    updated: 'Updated',
    currentRisk: 'Current risk',
    price: 'BTC price model input',
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
    loading: 'Loading risk data...',
    empty: 'No collected data yet. Run the collector backfill to populate TimescaleDB.',
  },
  ru: {
    eyebrow: 'Ежедневный BTC риск-сигнал',
    title: 'Bitcoin Risk Brief',
    subtitle: 'Короткий ежедневный ответ: BTC перегрет, нейтрален или в зоне дисконта.',
    updated: 'Обновлено',
    currentRisk: 'Текущий риск',
    price: 'Цена BTC в модели',
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
    loading: 'Загружаю risk data...',
    empty: 'Данных пока нет. Запусти collector backfill, чтобы заполнить TimescaleDB.',
  },
} as const

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}

function formatUsd(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function stateLabel(state: string, locale: Locale) {
  const labels = {
    en: { low: 'Low', neutral: 'Neutral', high: 'High' },
    ru: { low: 'Низкий', neutral: 'Нейтральный', high: 'Высокий' },
  }
  return labels[locale][state as 'low' | 'neutral' | 'high'] ?? state
}

export default function App() {
  const [locale, setLocale] = useState<Locale>('en')
  const [latest, setLatest] = useState<RiskPoint | null>(null)
  const [history, setHistory] = useState<RiskPoint[]>([])
  const [levels, setLevels] = useState<RiskLevel[]>([])
  const [brief, setBrief] = useState<BriefPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lead, setLead] = useState('')
  const [joined, setJoined] = useState(false)
  const [joinError, setJoinError] = useState<string | null>(null)
  const [joining, setJoining] = useState(false)
  const t = copy[locale]

  useEffect(() => {
    let active = true
    Promise.all([fetchLatestRisk(), fetchRiskHistory(), fetchRiskLevels(), fetchBrief()])
      .then(([latestResponse, historyResponse, levelsResponse, briefResponse]) => {
        if (!active) return
        setLatest(latestResponse.data)
        setHistory(historyResponse.data)
        setLevels(levelsResponse.data)
        setBrief(briefResponse.data)
      })
      .catch((err: Error) => {
        if (active) setError(err.message)
      })
    return () => {
      active = false
    }
  }, [])

  const riskOption = useMemo(() => ({
    backgroundColor: 'transparent',
    grid: { left: 44, right: 22, top: 18, bottom: 36 },
    tooltip: { trigger: 'axis', valueFormatter: (value: number) => formatPercent(value) },
    xAxis: { type: 'category', data: history.map((point) => point.timestamp.slice(0, 10)), axisLabel: { color: '#7e8794' }, axisLine: { lineStyle: { color: '#2a3441' } } },
    yAxis: { type: 'value', min: 0, max: 1, axisLabel: { color: '#7e8794', formatter: (value: number) => `${value * 100}%` }, splitLine: { lineStyle: { color: '#26303b' } } },
    series: [{ name: 'Risk', type: 'line', smooth: true, showSymbol: false, data: history.map((point) => point.risk), lineStyle: { width: 3, color: '#f2b84b' }, areaStyle: { color: 'rgba(242,184,75,0.12)' }, markLine: { symbol: 'none', data: [{ yAxis: 0.35 }, { yAxis: 0.65 }], lineStyle: { color: '#596473', type: 'dashed' } } }],
  }), [history])

  const levelsOption = useMemo(() => ({
    backgroundColor: 'transparent',
    grid: { left: 62, right: 22, top: 18, bottom: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: levels.map((row) => `${Math.round(row.risk * 100)}%`), axisLabel: { color: '#7e8794' }, axisLine: { lineStyle: { color: '#2a3441' } } },
    yAxis: { type: 'value', axisLabel: { color: '#7e8794', formatter: (value: number) => `$${Math.round(value / 1000)}k` }, splitLine: { lineStyle: { color: '#26303b' } } },
    series: [{ name: 'Price', type: 'bar', data: levels.map((row) => row.price_usd), itemStyle: { color: '#5bd6c6', borderRadius: [4, 4, 0, 0] } }],
  }), [levels])

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
        <section className="empty-state">
          <ShieldAlert size={30} />
          <h1>{t.empty}</h1>
          <p>{error}</p>
        </section>
      </main>
    )
  }

  if (!latest || !brief) {
    return <main className="shell centered"><p className="loading">{t.loading}</p></main>
  }

  const briefSection = brief.sections[locale]
  const state = stateLabel(latest.risk_state, locale)

  return (
    <main className="shell">
      <nav className="topbar" aria-label="Language">
        <div className="brand"><Radio size={18} /> BTC Risk Brief</div>
        <button className="lang" onClick={() => setLocale(locale === 'en' ? 'ru' : 'en')}><Languages size={16} /> {locale === 'en' ? 'RU' : 'EN'}</button>
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
        <div><span>{t.price}</span><strong>{formatUsd(latest.price_usd)}</strong></div>
        <div><span>{t.updated}</span><strong>{latest.timestamp.slice(0, 10)}</strong></div>
        <div><span>Delta</span><strong className={brief.delta_risk >= 0 ? 'up' : 'down'}>{brief.delta_risk >= 0 ? '+' : ''}{formatPercent(brief.delta_risk)}</strong></div>
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

      <section className="charts">
        <article className="chart-panel"><h2>{t.history}</h2><ReactECharts option={riskOption} style={{ height: 360, width: '100%' }} /></article>
        <article className="chart-panel"><h2>{t.levels}</h2><ReactECharts option={levelsOption} style={{ height: 360, width: '100%' }} /></article>
      </section>

      <section className="waitlist">
        <div>
          <Bell size={24} />
          <h2>{t.waitlistTitle}</h2>
          <p>{t.waitlistBody}</p>
        </div>
        <form className="lead-form" onSubmit={submitWaitlist}>
          <input value={lead} onChange={(event) => setLead(event.target.value)} placeholder={t.placeholder} aria-label={t.placeholder} />
          <button type="submit" disabled={joining}><Send size={16} /> {joining ? t.joining : t.join}</button>
        </form>
        {joined && <p className="joined">{t.joined}</p>}
        {joinError && <p className="joined error-text">{joinError}</p>}
      </section>
    </main>
  )
}
