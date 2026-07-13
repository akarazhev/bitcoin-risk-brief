# Issue 28 Localization Language Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish existing product copy and add selectable Chinese, German, French, Spanish, and Arabic support while preserving English/Russian behavior and waitlist locale attribution.

**Architecture:** Move frontend UI copy and locale metadata out of `frontend/src/App.tsx` into a focused locale module. Keep the backend API shape stable, but expand backend waitlist locale validation and generated brief sections so the selected UI language can be stored and displayed. Arabic is enabled with document-level RTL metadata and targeted layout rules; Chinese uses Simplified Chinese under locale code `zh`.

**Tech Stack:** React/Vite/TypeScript, Vitest + Testing Library, FastAPI/Pydantic, Python `unittest`, existing CSS.

---

## Scope Decisions

- Supported locale codes after this work: `en`, `ru`, `zh`, `de`, `fr`, `es`, `ar`.
- `zh` means Simplified Chinese. Do not introduce `zh-Hans` unless the backend max-length and normalization behavior are redesigned.
- Arabic must set `<html dir="rtl" lang="ar">`; all other supported locales use `dir="ltr"`.
- Keep `/api/brief/latest` response shape unchanged: `sections` remains keyed by locale. Add generated sections for every supported locale.
- The frontend must tolerate old persisted brief snapshots that only contain `en`/`ru`; if `brief.sections[locale]` is missing, display the English brief section while keeping the surrounding UI in the selected locale.
- Do not translate operational docs, methodology docs, chart data, ISO dates, or USD formatting in this issue.

## File Structure

- Create `frontend/src/locales.ts`: locale registry, `Locale` type, UI copy, state labels, and helper functions.
- Create `frontend/src/locales.test.ts`: focused tests for locale registry completeness, RTL metadata, copy key parity, and risk-state labels.
- Modify `frontend/src/types.ts`: export the expanded `Locale` type and permit partial brief sections for backwards compatibility with old snapshots.
- Modify `frontend/src/App.tsx`: import locale data, replace two-language toggle with a selector, set document `lang`/`dir`, use localized unavailable text, and fall back to English brief copy.
- Modify `frontend/src/App.test.tsx`: update locale interaction tests for the selector and add coverage for all issue #28 locales, Arabic RTL metadata, waitlist locale submission, and brief fallback.
- Modify `frontend/src/App.css`: replace `.lang` button styles with compact selector styles and add RTL-safe rules.
- Modify `backend/app/waitlist.py`: expand accepted locale values.
- Modify `backend/tests/test_waitlist.py`: test accepted issue #28 locales and fallback for unsupported values.
- Modify `backend/app/brief.py`: generate brief sections for all supported locales.
- Modify `backend/tests/test_brief.py`: assert generated sections cover all supported locales and retain conservative no-advice language.
- Modify `docs/api-reference.md`, `README.md`, `docs/frontend-qa.md`, `docs/testing-and-quality.md`, `docs/production-readiness.md`, and `docs/superpowers/specs/2026-07-01-localization-quality-language-expansion-design.md`: align documentation with the new accepted language scope.

---

### Task 1: Add Frontend Locale Registry

**Files:**
- Create: `frontend/src/locales.test.ts`
- Create: `frontend/src/locales.ts`

- [ ] **Step 1: Write failing locale registry tests**

Create `frontend/src/locales.test.ts`:

```ts
import { copy, getLocaleOption, localeOptions, stateLabel, supportedLocales } from './locales'

test('defines the issue 28 supported locale set in selector order', () => {
  expect(supportedLocales).toEqual(['en', 'ru', 'zh', 'de', 'fr', 'es', 'ar'])
  expect(localeOptions.map((option) => option.code)).toEqual(supportedLocales)
  expect(localeOptions.map((option) => option.shortLabel)).toEqual(['EN', 'RU', '中文', 'DE', 'FR', 'ES', 'AR'])
})

test('marks Arabic as RTL and all other supported locales as LTR', () => {
  for (const locale of supportedLocales) {
    expect(getLocaleOption(locale).dir).toBe(locale === 'ar' ? 'rtl' : 'ltr')
  }
  expect(getLocaleOption('zh').lang).toBe('zh-CN')
})

test('keeps UI translation keys complete for every locale', () => {
  const expectedKeys = Object.keys(copy.en).sort()

  for (const locale of supportedLocales) {
    expect(Object.keys(copy[locale]).sort()).toEqual(expectedKeys)
  }
})

test('localizes core risk-state labels', () => {
  expect(stateLabel('low', 'en')).toBe('Low')
  expect(stateLabel('high', 'ru')).toBe('Высокий')
  expect(stateLabel('neutral', 'zh')).toBe('中性')
  expect(stateLabel('low', 'de')).toBe('Niedrig')
  expect(stateLabel('high', 'fr')).toBe('Élevé')
  expect(stateLabel('neutral', 'es')).toBe('Neutral')
  expect(stateLabel('low', 'ar')).toBe('منخفض')
})
```

- [ ] **Step 2: Run the focused frontend test and confirm it fails**

Run:

```bash
npm test --prefix frontend -- locales.test.ts
```

Expected: FAIL because `frontend/src/locales.ts` does not exist.

- [ ] **Step 3: Create the locale module**

Create `frontend/src/locales.ts` with this structure and complete copy. Keep all keys present for every locale.

```ts
export type Locale = 'en' | 'ru' | 'zh' | 'de' | 'fr' | 'es' | 'ar'

export type LocaleDirection = 'ltr' | 'rtl'

export type LocaleOption = {
  code: Locale
  label: string
  shortLabel: string
  lang: string
  dir: LocaleDirection
}

type RiskStateLabels = Record<'low' | 'neutral' | 'high', string>

type Copy = {
  languageNavigation: string
  languageSelector: string
  eyebrow: string
  title: string
  subtitle: string
  updated: string
  currentRisk: string
  price: string
  modelPrice: string
  low: string
  high: string
  riskChange: string
  riskChangeContext: string
  modelDrivers: string
  modelDriversBody: string
  driverTrend: string
  driverTrendDetail: string
  driverVolatility: string
  driverVolatilityDetail: string
  driverActivity: string
  driverActivityDetail: string
  driverActivityUnavailableDetail: string
  driverRaises: string
  driverNeutral: string
  driverLowers: string
  driverUnavailable: string
  riskZones: [string, string]
  readinessReady: string
  readinessDegraded: string
  validationPassed: string
  validationNeedsAttention: string
  currentThrough: string
  latestCompletedDay: string
  coverageThrough: string
  freshnessCurrent: string
  staleAge: (days: number | null) => string
  methodology: string
  methodologyLink: string
  methodologyVersion: string
  methodologyBody: string
  disclaimer: string
  thresholdCallouts: string
  thresholdNear: (label: string, price: string) => string
  riskHistoryAlternative: string
  riskLevelsAlternative: string
  chartCurrentSummary: (date: string, risk: string, state: string, modelPrice: string, range: string) => string
  chartCurrentRange: (low: string, high: string) => string
  riskHistoryAlternativeNote: (count: number) => string
  riskLevelsAlternativeNote: string
  dateColumn: string
  riskColumn: string
  priceColumn: string
  stateColumn: string
  thresholdColumn: string
  bandColumn: string
  nearestModelPriceColumn: string
  recentRiskHistoryTable: string
  riskThresholdPriceTable: string
  history: string
  levels: string
  brief: string
  changed: string
  avoid: string
  confirm: string
  waitlistTitle: string
  waitlistBody: string
  placeholder: string
  join: string
  joined: string
  joinError: string
  joining: string
  privacyNoteTitle: string
  privacyNoteIntro: string
  privacyNoteWaitlist: string
  privacyNoteLogs: string
  privacyNoteLimits: string
  privacyNoteAnalytics: string
  loading: string
  empty: string
  loadErrorTitle: string
  loadErrorBody: string
  chartLoading: string
  historyEmpty: string
  levelsEmpty: string
  historyError: string
  levelsError: string
  unavailable: string
}

export const supportedLocales = ['en', 'ru', 'zh', 'de', 'fr', 'es', 'ar'] as const satisfies readonly Locale[]

export const localeOptions: readonly LocaleOption[] = [
  { code: 'en', label: 'English', shortLabel: 'EN', lang: 'en', dir: 'ltr' },
  { code: 'ru', label: 'Русский', shortLabel: 'RU', lang: 'ru', dir: 'ltr' },
  { code: 'zh', label: '简体中文', shortLabel: '中文', lang: 'zh-CN', dir: 'ltr' },
  { code: 'de', label: 'Deutsch', shortLabel: 'DE', lang: 'de', dir: 'ltr' },
  { code: 'fr', label: 'Français', shortLabel: 'FR', lang: 'fr', dir: 'ltr' },
  { code: 'es', label: 'Español', shortLabel: 'ES', lang: 'es', dir: 'ltr' },
  { code: 'ar', label: 'العربية', shortLabel: 'AR', lang: 'ar', dir: 'rtl' },
]

export function getLocaleOption(locale: Locale) {
  return localeOptions.find((option) => option.code === locale) ?? localeOptions[0]
}

export const riskStateLabels: Record<Locale, RiskStateLabels> = {
  en: { low: 'Low', neutral: 'Neutral', high: 'High' },
  ru: { low: 'Низкий', neutral: 'Нейтральный', high: 'Высокий' },
  zh: { low: '低', neutral: '中性', high: '高' },
  de: { low: 'Niedrig', neutral: 'Neutral', high: 'Hoch' },
  fr: { low: 'Faible', neutral: 'Neutre', high: 'Élevé' },
  es: { low: 'Bajo', neutral: 'Neutral', high: 'Alto' },
  ar: { low: 'منخفض', neutral: 'محايد', high: 'مرتفع' },
}

export function stateLabel(state: string, locale: Locale) {
  return riskStateLabels[locale][state as 'low' | 'neutral' | 'high'] ?? state
}

export const copy: Record<Locale, Copy> = {
  en: {
    languageNavigation: 'Language',
    languageSelector: 'Select language',
    eyebrow: 'Daily BTC Risk Signal',
    title: 'Bitcoin Risk Brief',
    subtitle: 'A concise daily read on whether BTC risk looks elevated, balanced, or washed out.',
    updated: 'Updated',
    currentRisk: 'Current risk',
    price: 'BTC model price input',
    modelPrice: 'Model price',
    low: 'Low',
    high: 'High',
    riskChange: 'Risk change',
    riskChangeContext: 'vs previous observation',
    modelDrivers: 'Model drivers',
    modelDriversBody: 'Plain-language direction of each model component from the latest validated daily data.',
    driverTrend: 'Trend',
    driverTrendDetail: 'Price vs long-term baseline',
    driverVolatility: 'Volatility',
    driverVolatilityDetail: 'Recent price swings',
    driverActivity: 'Activity',
    driverActivityDetail: 'Trading activity adjusted for market size',
    driverActivityUnavailableDetail: 'Market-adjusted activity unavailable',
    driverRaises: 'Raises risk',
    driverNeutral: 'Neutral',
    driverLowers: 'Lowers risk',
    driverUnavailable: 'Unavailable',
    riskZones: ['Low / Neutral', 'Neutral / High'],
    readinessReady: 'Readiness ready',
    readinessDegraded: 'Readiness degraded',
    validationPassed: 'Validation passed',
    validationNeedsAttention: 'Validation needs attention',
    currentThrough: 'Current through',
    latestCompletedDay: 'Latest completed day',
    coverageThrough: 'Coverage through',
    freshnessCurrent: 'Freshness: current',
    staleAge: (days) => (days === null ? 'Staleness unavailable' : `Stale: ${days} ${days === 1 ? 'day' : 'days'} behind`),
    methodology: 'Methodology',
    methodologyLink: 'View methodology',
    methodologyVersion: 'Methodology version',
    methodologyBody: 'The public signal uses the canonical BTC risk model and the latest validated CoinMarketCap CSV import.',
    disclaimer: 'Risk levels are scenario outputs for research. They are not financial advice or trading instructions.',
    thresholdCallouts: 'Nearest threshold prices',
    thresholdNear: (label, price) => `${label} near ${price}`,
    riskHistoryAlternative: 'Risk history chart data alternative',
    riskLevelsAlternative: 'Risk level chart data alternative',
    chartCurrentSummary: (date, risk, state, modelPrice, range) => `Latest observation ${date}: current risk is ${risk} (${state}) and model price is ${modelPrice}${range}.`,
    chartCurrentRange: (low, high) => `, with latest daily low ${low} and high ${high}`,
    riskHistoryAlternativeNote: (count) => `The table lists the ${count} most recent risk history observations available to the chart.`,
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
    unavailable: 'unavailable',
  },
  ru: {
    languageNavigation: 'Язык',
    languageSelector: 'Выберите язык',
    eyebrow: 'Ежедневный BTC риск-сигнал',
    title: 'Bitcoin Risk Brief',
    subtitle: 'Короткий ежедневный обзор: риск BTC повышен, сбалансирован или близок к зоне дисконта.',
    updated: 'Обновлено',
    currentRisk: 'Текущий риск',
    price: 'Цена BTC в модели',
    modelPrice: 'Цена модели',
    low: 'Мин.',
    high: 'Макс.',
    riskChange: 'Изменение риска',
    riskChangeContext: 'к прошлому наблюдению',
    modelDrivers: 'Драйверы модели',
    modelDriversBody: 'Понятное направление каждого компонента модели по последним валидированным дневным данным.',
    driverTrend: 'Тренд',
    driverTrendDetail: 'Цена относительно долгосрочной базы',
    driverVolatility: 'Волатильность',
    driverVolatilityDetail: 'Недавние колебания цены',
    driverActivity: 'Активность',
    driverActivityDetail: 'Торговая активность с учетом размера рынка',
    driverActivityUnavailableDetail: 'Активность с учетом размера рынка недоступна',
    driverRaises: 'Повышает риск',
    driverNeutral: 'Нейтрально',
    driverLowers: 'Снижает риск',
    driverUnavailable: 'Недоступно',
    riskZones: ['Низкий / Нейтральный', 'Нейтральный / Высокий'],
    readinessReady: 'Готовность подтверждена',
    readinessDegraded: 'Готовность снижена',
    validationPassed: 'Валидация пройдена',
    validationNeedsAttention: 'Валидация требует внимания',
    currentThrough: 'Актуально по',
    latestCompletedDay: 'Последний завершенный день',
    coverageThrough: 'Покрытие по',
    freshnessCurrent: 'Свежесть: актуально',
    staleAge: (days) => (days === null ? 'Отставание данных неизвестно' : `Отставание: ${days} дн.`),
    methodology: 'Методология',
    methodologyLink: 'Методология',
    methodologyVersion: 'Версия методологии',
    methodologyBody: 'Публичный сигнал использует каноническую BTC risk-модель и последний валидированный импорт CoinMarketCap CSV.',
    disclaimer: 'Уровни риска - сценарные расчеты для исследования, а не финансовый совет или торговая инструкция.',
    thresholdCallouts: 'Ближайшие пороги цены',
    thresholdNear: (label, price) => `${label}: около ${price}`,
    riskHistoryAlternative: 'Текстовая альтернатива графику истории риска',
    riskLevelsAlternative: 'Текстовая альтернатива графику уровней риска',
    chartCurrentSummary: (date, risk, state, modelPrice, range) => `Последнее наблюдение ${date}: текущий риск ${risk} (${state}), цена модели ${modelPrice}${range}.`,
    chartCurrentRange: (low, high) => `, дневной минимум ${low}, максимум ${high}`,
    riskHistoryAlternativeNote: (count) => `Таблица показывает ${count} последних наблюдений риска, доступных на графике.`,
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
    waitlistBody: 'Оставьте email или Telegram. Первая тестовая группа получит риск-алерт бесплатно.',
    placeholder: 'email или @telegram',
    join: 'В лист ожидания',
    joined: 'Сохранено. Вы в листе ожидания Bitcoin Risk Brief.',
    joinError: 'Укажите корректный email или Telegram.',
    joining: 'Сохранение...',
    privacyNoteTitle: 'Приватность, условия и дисклеймер',
    privacyNoteIntro: 'Bitcoin Risk Brief - только информационная аналитика, не финансовый или инвестиционный совет и не торговая рекомендация.',
    privacyNoteWaitlist: 'Лист ожидания хранит введенный контакт, нормализованную копию, тип контакта, язык, источник, статус и временные метки.',
    privacyNoteLogs: 'Операционные логи могут включать метод запроса, путь, статус, client key, Cloudflare ray ID, cache-статус и время выполнения.',
    privacyNoteLimits: 'Не вводите конфиденциальную информацию. Покупка, продажа, портфельное или торговое действие не рекомендуется, платный SLA поддержки не предоставляется.',
    privacyNoteAnalytics: 'В текущем исходном коде приложения нет product analytics или tracking-cookie кода.',
    loading: 'Загрузка данных риска...',
    empty: 'Данных пока нет. Запустите collector backfill, чтобы заполнить TimescaleDB.',
    loadErrorTitle: 'Данные о риске временно недоступны',
    loadErrorBody: 'Страница не смогла загрузить последний пакет данных о риске. Считайте сигнал недоступным, пока API не восстановится.',
    chartLoading: 'Загрузка графика...',
    historyEmpty: 'История риска недоступна, пока наблюдения не загружены.',
    levelsEmpty: 'Уровни риска недоступны, пока нет последнего входа модели.',
    historyError: 'История риска временно недоступна.',
    levelsError: 'Уровни риска временно недоступны.',
    unavailable: 'недоступно',
  },
  zh: {
    languageNavigation: '语言',
    languageSelector: '选择语言',
    eyebrow: '每日 BTC 风险信号',
    title: 'Bitcoin Risk Brief',
    subtitle: '每日简明判断 BTC 风险处于偏高、均衡，还是接近折价区域。',
    updated: '已更新',
    currentRisk: '当前风险',
    price: 'BTC 模型价格输入',
    modelPrice: '模型价格',
    low: '低点',
    high: '高点',
    riskChange: '风险变化',
    riskChangeContext: '相对上一条观测',
    modelDrivers: '模型驱动因素',
    modelDriversBody: '基于最新验证日度数据，对每个模型组件方向的简明说明。',
    driverTrend: '趋势',
    driverTrendDetail: '价格相对长期基准',
    driverVolatility: '波动率',
    driverVolatilityDetail: '近期价格波动',
    driverActivity: '活跃度',
    driverActivityDetail: '按市场规模调整后的交易活跃度',
    driverActivityUnavailableDetail: '按市场规模调整的活跃度不可用',
    driverRaises: '提高风险',
    driverNeutral: '中性',
    driverLowers: '降低风险',
    driverUnavailable: '不可用',
    riskZones: ['低 / 中性', '中性 / 高'],
    readinessReady: '就绪状态正常',
    readinessDegraded: '就绪状态下降',
    validationPassed: '验证通过',
    validationNeedsAttention: '验证需要关注',
    currentThrough: '数据截至',
    latestCompletedDay: '最近完整日期',
    coverageThrough: '覆盖截至',
    freshnessCurrent: '新鲜度：当前',
    staleAge: (days) => (days === null ? '滞后状态不可用' : `滞后：${days} 天`),
    methodology: '方法论',
    methodologyLink: '查看方法论',
    methodologyVersion: '方法论版本',
    methodologyBody: '公开信号使用标准 BTC 风险模型和最新通过验证的 CoinMarketCap CSV 导入数据。',
    disclaimer: '风险等级是研究用场景输出，不构成财务建议或交易指令。',
    thresholdCallouts: '最近阈值价格',
    thresholdNear: (label, price) => `${label} 接近 ${price}`,
    riskHistoryAlternative: '风险历史图表的数据替代说明',
    riskLevelsAlternative: '风险等级图表的数据替代说明',
    chartCurrentSummary: (date, risk, state, modelPrice, range) => `最新观测 ${date}：当前风险为 ${risk}（${state}），模型价格为 ${modelPrice}${range}。`,
    chartCurrentRange: (low, high) => `，最新日内低点 ${low}，高点 ${high}`,
    riskHistoryAlternativeNote: (count) => `表格列出图表中最近 ${count} 条风险历史观测。`,
    riskLevelsAlternativeNote: '表格列出风险等级图表使用的关键风险阈值价格。',
    dateColumn: '日期',
    riskColumn: '风险',
    priceColumn: 'BTC 价格',
    stateColumn: '风险状态',
    thresholdColumn: '风险阈值',
    bandColumn: '区间',
    nearestModelPriceColumn: '最近模型价格',
    recentRiskHistoryTable: '近期风险历史表',
    riskThresholdPriceTable: '风险阈值价格表',
    history: '风险历史',
    levels: '风险等级',
    brief: '今日简报',
    changed: '变化内容',
    avoid: '当前避免',
    confirm: '下一步确认',
    waitlistTitle: '获取每日信号',
    waitlistBody: '留下邮箱或 Telegram 用户名。首批测试用户可免费收到风险提醒。',
    placeholder: 'email 或 @telegram',
    join: '加入候补名单',
    joined: '已保存。您已加入 Bitcoin Risk Brief 候补名单。',
    joinError: '请输入有效邮箱或 Telegram 用户名。',
    joining: '保存中...',
    privacyNoteTitle: '隐私、条款和免责声明',
    privacyNoteIntro: 'Bitcoin Risk Brief 仅用于信息研究，不是财务建议、投资建议或交易推荐。',
    privacyNoteWaitlist: '候补名单会存储您提交的联系方式、规范化副本、联系方式类型、语言、来源、状态和时间戳。',
    privacyNoteLogs: '运营日志可能包含请求方法、路径、状态、client key、Cloudflare ray ID、缓存状态和耗时。',
    privacyNoteLimits: '请勿输入敏感信息。我们不建议任何买入、卖出、组合或交易操作，也不提供付费支持 SLA。',
    privacyNoteAnalytics: '当前应用源码不包含产品分析或跟踪 cookie 代码。',
    loading: '正在加载风险数据...',
    empty: '尚无采集数据。请运行 collector backfill 以填充 TimescaleDB。',
    loadErrorTitle: '风险数据暂时不可用',
    loadErrorBody: '页面无法加载最新风险数据包。在 API 恢复前，请将该信号视为不可用。',
    chartLoading: '正在加载图表...',
    historyEmpty: '观测数据加载前，风险历史不可用。',
    levelsEmpty: '最新模型输入准备好之前，风险等级不可用。',
    historyError: '风险历史暂时不可用。',
    levelsError: '风险等级暂时不可用。',
    unavailable: '不可用',
  },
  de: {
    languageNavigation: 'Sprache',
    languageSelector: 'Sprache auswählen',
    eyebrow: 'Tägliches BTC-Risikosignal',
    title: 'Bitcoin Risk Brief',
    subtitle: 'Ein kurzer täglicher Blick darauf, ob das BTC-Risiko erhöht, ausgeglichen oder ausgewaschen wirkt.',
    updated: 'Aktualisiert',
    currentRisk: 'Aktuelles Risiko',
    price: 'BTC-Modellpreis-Eingabe',
    modelPrice: 'Modellpreis',
    low: 'Tief',
    high: 'Hoch',
    riskChange: 'Risikoänderung',
    riskChangeContext: 'gegenüber der vorherigen Beobachtung',
    modelDrivers: 'Modelltreiber',
    modelDriversBody: 'Verständliche Richtung jedes Modellbausteins auf Basis der neuesten validierten Tagesdaten.',
    driverTrend: 'Trend',
    driverTrendDetail: 'Preis gegenüber der langfristigen Basislinie',
    driverVolatility: 'Volatilität',
    driverVolatilityDetail: 'Jüngste Preisschwankungen',
    driverActivity: 'Aktivität',
    driverActivityDetail: 'An Marktgröße angepasste Handelsaktivität',
    driverActivityUnavailableDetail: 'An Marktgröße angepasste Aktivität nicht verfügbar',
    driverRaises: 'Erhöht Risiko',
    driverNeutral: 'Neutral',
    driverLowers: 'Senkt Risiko',
    driverUnavailable: 'Nicht verfügbar',
    riskZones: ['Niedrig / Neutral', 'Neutral / Hoch'],
    readinessReady: 'Bereitschaft bereit',
    readinessDegraded: 'Bereitschaft eingeschränkt',
    validationPassed: 'Validierung bestanden',
    validationNeedsAttention: 'Validierung braucht Aufmerksamkeit',
    currentThrough: 'Aktuell bis',
    latestCompletedDay: 'Letzter abgeschlossener Tag',
    coverageThrough: 'Abdeckung bis',
    freshnessCurrent: 'Aktualität: aktuell',
    staleAge: (days) => (days === null ? 'Alter der Daten nicht verfügbar' : `Veraltet: ${days} ${days === 1 ? 'Tag' : 'Tage'} zurück`),
    methodology: 'Methodik',
    methodologyLink: 'Methodik ansehen',
    methodologyVersion: 'Methodikversion',
    methodologyBody: 'Das öffentliche Signal nutzt das kanonische BTC-Risikomodell und den neuesten validierten CoinMarketCap-CSV-Import.',
    disclaimer: 'Risikostufen sind Szenarioausgaben für Research. Sie sind keine Finanzberatung und keine Handelsanweisung.',
    thresholdCallouts: 'Nächste Schwellenpreise',
    thresholdNear: (label, price) => `${label} nahe ${price}`,
    riskHistoryAlternative: 'Datenalternative zum Risikohistorie-Chart',
    riskLevelsAlternative: 'Datenalternative zum Risikostufen-Chart',
    chartCurrentSummary: (date, risk, state, modelPrice, range) => `Neueste Beobachtung ${date}: aktuelles Risiko ${risk} (${state}) und Modellpreis ${modelPrice}${range}.`,
    chartCurrentRange: (low, high) => `, mit letztem Tagestief ${low} und Tageshoch ${high}`,
    riskHistoryAlternativeNote: (count) => `Die Tabelle zeigt die ${count} neuesten Risikobeobachtungen, die im Chart verfügbar sind.`,
    riskLevelsAlternativeNote: 'Die Tabelle zeigt die wichtigsten Risiko-Schwellenpreise, die im Risikostufen-Chart verwendet werden.',
    dateColumn: 'Datum',
    riskColumn: 'Risiko',
    priceColumn: 'BTC-Preis',
    stateColumn: 'Risikozustand',
    thresholdColumn: 'Risikoschwelle',
    bandColumn: 'Band',
    nearestModelPriceColumn: 'Nächster Modellpreis',
    recentRiskHistoryTable: 'Tabelle der jüngsten Risikohistorie',
    riskThresholdPriceTable: 'Tabelle der Risiko-Schwellenpreise',
    history: 'Risikohistorie',
    levels: 'Risikostufen',
    brief: 'Heutiger Brief',
    changed: 'Was sich geändert hat',
    avoid: 'Jetzt vermeiden',
    confirm: 'Als Nächstes prüfen',
    waitlistTitle: 'Tägliches Signal erhalten',
    waitlistBody: 'Hinterlassen Sie eine E-Mail oder einen Telegram-Handle. Die erste Testkohorte erhält den Risikoalarm kostenlos.',
    placeholder: 'E-Mail oder @telegram',
    join: 'Auf Warteliste setzen',
    joined: 'Gespeichert. Sie sind auf der Bitcoin Risk Brief Warteliste.',
    joinError: 'Geben Sie eine gültige E-Mail oder einen Telegram-Handle ein.',
    joining: 'Speichern...',
    privacyNoteTitle: 'Datenschutz, Bedingungen und Hinweis',
    privacyNoteIntro: 'Bitcoin Risk Brief ist nur informationsbezogenes Research, keine Finanzberatung, Anlageberatung oder Handelsempfehlung.',
    privacyNoteWaitlist: 'Die Warteliste speichert den eingereichten Kontakt, eine normalisierte Kopie, Kontakttyp, Sprache, Quelle, Status und Zeitstempel.',
    privacyNoteLogs: 'Betriebslogs können Anfragemethode, Pfad, Status, client key, Cloudflare ray ID, Cache-Status und Laufzeit enthalten.',
    privacyNoteLimits: 'Geben Sie keine sensiblen Informationen ein. Es wird keine Kauf-, Verkaufs-, Portfolio- oder Handelsaktion empfohlen, und es gibt kein bezahltes Support-SLA.',
    privacyNoteAnalytics: 'Der aktuelle App-Quellcode enthält keine Produktanalyse- oder Tracking-Cookie-Logik.',
    loading: 'Risikodaten werden geladen...',
    empty: 'Noch keine gesammelten Daten. Führen Sie collector backfill aus, um TimescaleDB zu füllen.',
    loadErrorTitle: 'Risikodaten sind vorübergehend nicht verfügbar',
    loadErrorBody: 'Die Seite konnte das neueste Risikopaket nicht laden. Behandeln Sie das Signal als nicht verfügbar, bis die API wiederhergestellt ist.',
    chartLoading: 'Chart wird geladen...',
    historyEmpty: 'Die Risikohistorie ist nicht verfügbar, bis Beobachtungen geladen sind.',
    levelsEmpty: 'Risikostufen sind nicht verfügbar, bis die neueste Modelleingabe bereit ist.',
    historyError: 'Die Risikohistorie ist vorübergehend nicht verfügbar.',
    levelsError: 'Die Risikostufen sind vorübergehend nicht verfügbar.',
    unavailable: 'nicht verfügbar',
  },
  fr: {
    languageNavigation: 'Langue',
    languageSelector: 'Choisir la langue',
    eyebrow: 'Signal de risque BTC quotidien',
    title: 'Bitcoin Risk Brief',
    subtitle: 'Une lecture quotidienne concise pour savoir si le risque BTC paraît élevé, équilibré ou décoté.',
    updated: 'Mis à jour',
    currentRisk: 'Risque actuel',
    price: 'Entrée de prix BTC du modèle',
    modelPrice: 'Prix du modèle',
    low: 'Bas',
    high: 'Haut',
    riskChange: 'Variation du risque',
    riskChangeContext: 'vs observation précédente',
    modelDrivers: 'Moteurs du modèle',
    modelDriversBody: 'Direction lisible de chaque composant du modèle à partir des dernières données quotidiennes validées.',
    driverTrend: 'Tendance',
    driverTrendDetail: 'Prix par rapport à la base de long terme',
    driverVolatility: 'Volatilité',
    driverVolatilityDetail: 'Variations récentes du prix',
    driverActivity: 'Activité',
    driverActivityDetail: 'Activité de marché ajustée à la taille du marché',
    driverActivityUnavailableDetail: 'Activité ajustée à la taille du marché indisponible',
    driverRaises: 'Augmente le risque',
    driverNeutral: 'Neutre',
    driverLowers: 'Réduit le risque',
    driverUnavailable: 'Indisponible',
    riskZones: ['Faible / Neutre', 'Neutre / Élevé'],
    readinessReady: 'Disponibilité prête',
    readinessDegraded: 'Disponibilité dégradée',
    validationPassed: 'Validation réussie',
    validationNeedsAttention: 'Validation à vérifier',
    currentThrough: 'À jour jusqu’au',
    latestCompletedDay: 'Dernier jour complet',
    coverageThrough: 'Couverture jusqu’au',
    freshnessCurrent: 'Fraîcheur : actuelle',
    staleAge: (days) => (days === null ? 'Retard des données indisponible' : `En retard : ${days} ${days === 1 ? 'jour' : 'jours'}`),
    methodology: 'Méthodologie',
    methodologyLink: 'Voir la méthodologie',
    methodologyVersion: 'Version de la méthodologie',
    methodologyBody: 'Le signal public utilise le modèle de risque BTC canonique et le dernier import CSV CoinMarketCap validé.',
    disclaimer: 'Les niveaux de risque sont des sorties de scénario pour la recherche. Ils ne constituent pas un conseil financier ni une instruction de trading.',
    thresholdCallouts: 'Prix de seuil les plus proches',
    thresholdNear: (label, price) => `${label} près de ${price}`,
    riskHistoryAlternative: 'Alternative textuelle aux données du graphique d’historique du risque',
    riskLevelsAlternative: 'Alternative textuelle aux données du graphique des niveaux de risque',
    chartCurrentSummary: (date, risk, state, modelPrice, range) => `Dernière observation ${date} : le risque actuel est ${risk} (${state}) et le prix du modèle est ${modelPrice}${range}.`,
    chartCurrentRange: (low, high) => `, avec un plus bas quotidien récent à ${low} et un plus haut à ${high}`,
    riskHistoryAlternativeNote: (count) => `Le tableau liste les ${count} observations de risque les plus récentes disponibles dans le graphique.`,
    riskLevelsAlternativeNote: 'Le tableau liste les principaux prix de seuil utilisés avec le graphique des niveaux de risque.',
    dateColumn: 'Date',
    riskColumn: 'Risque',
    priceColumn: 'Prix BTC',
    stateColumn: 'État du risque',
    thresholdColumn: 'Seuil de risque',
    bandColumn: 'Bande',
    nearestModelPriceColumn: 'Prix du modèle le plus proche',
    recentRiskHistoryTable: 'Tableau de l’historique récent du risque',
    riskThresholdPriceTable: 'Tableau des prix de seuil de risque',
    history: 'Historique du risque',
    levels: 'Niveaux de risque',
    brief: 'Brief du jour',
    changed: 'Ce qui a changé',
    avoid: 'À éviter maintenant',
    confirm: 'À confirmer ensuite',
    waitlistTitle: 'Recevoir le signal quotidien',
    waitlistBody: 'Laissez une adresse e-mail ou un identifiant Telegram. La première cohorte de test reçoit l’alerte de risque gratuitement.',
    placeholder: 'email ou @telegram',
    join: 'Rejoindre la liste',
    joined: 'Enregistré. Vous êtes sur la liste d’attente Bitcoin Risk Brief.',
    joinError: 'Saisissez une adresse e-mail ou un identifiant Telegram valide.',
    joining: 'Enregistrement...',
    privacyNoteTitle: 'Confidentialité, conditions et avertissement',
    privacyNoteIntro: 'Bitcoin Risk Brief est une recherche informative uniquement, pas un conseil financier, un conseil en investissement ni une recommandation de trading.',
    privacyNoteWaitlist: 'La liste d’attente stocke le contact soumis, une copie normalisée, le type de contact, la langue, la source, le statut et les horodatages.',
    privacyNoteLogs: 'Les journaux opérationnels peuvent inclure méthode de requête, chemin, statut, client key, Cloudflare ray ID, statut de cache et durée.',
    privacyNoteLimits: 'Ne saisissez pas d’informations sensibles. Aucune action d’achat, de vente, de portefeuille ou de trading n’est recommandée, et aucun SLA de support payant n’est fourni.',
    privacyNoteAnalytics: 'Le code source actuel de l’application ne contient pas d’analyse produit ni de code de cookie de suivi.',
    loading: 'Chargement des données de risque...',
    empty: 'Aucune donnée collectée pour le moment. Exécutez collector backfill pour alimenter TimescaleDB.',
    loadErrorTitle: 'Les données de risque sont temporairement indisponibles',
    loadErrorBody: 'La page n’a pas pu charger le dernier paquet de risque. Considérez le signal comme indisponible jusqu’au rétablissement de l’API.',
    chartLoading: 'Chargement du graphique...',
    historyEmpty: 'L’historique du risque est indisponible tant que les observations ne sont pas chargées.',
    levelsEmpty: 'Les niveaux de risque sont indisponibles tant que la dernière entrée du modèle n’est pas prête.',
    historyError: 'L’historique du risque est temporairement indisponible.',
    levelsError: 'Les niveaux de risque sont temporairement indisponibles.',
    unavailable: 'indisponible',
  },
  es: {
    languageNavigation: 'Idioma',
    languageSelector: 'Seleccionar idioma',
    eyebrow: 'Señal diaria de riesgo BTC',
    title: 'Bitcoin Risk Brief',
    subtitle: 'Una lectura diaria breve sobre si el riesgo de BTC parece elevado, equilibrado o descontado.',
    updated: 'Actualizado',
    currentRisk: 'Riesgo actual',
    price: 'Entrada de precio BTC del modelo',
    modelPrice: 'Precio del modelo',
    low: 'Mínimo',
    high: 'Máximo',
    riskChange: 'Cambio de riesgo',
    riskChangeContext: 'vs observación anterior',
    modelDrivers: 'Impulsores del modelo',
    modelDriversBody: 'Dirección clara de cada componente del modelo según los últimos datos diarios validados.',
    driverTrend: 'Tendencia',
    driverTrendDetail: 'Precio frente a la base de largo plazo',
    driverVolatility: 'Volatilidad',
    driverVolatilityDetail: 'Movimientos recientes del precio',
    driverActivity: 'Actividad',
    driverActivityDetail: 'Actividad de negociación ajustada por tamaño de mercado',
    driverActivityUnavailableDetail: 'Actividad ajustada por tamaño de mercado no disponible',
    driverRaises: 'Eleva el riesgo',
    driverNeutral: 'Neutral',
    driverLowers: 'Reduce el riesgo',
    driverUnavailable: 'No disponible',
    riskZones: ['Bajo / Neutral', 'Neutral / Alto'],
    readinessReady: 'Preparación lista',
    readinessDegraded: 'Preparación degradada',
    validationPassed: 'Validación aprobada',
    validationNeedsAttention: 'Validación requiere atención',
    currentThrough: 'Actual hasta',
    latestCompletedDay: 'Último día completo',
    coverageThrough: 'Cobertura hasta',
    freshnessCurrent: 'Actualidad: vigente',
    staleAge: (days) => (days === null ? 'Antigüedad no disponible' : `Desactualizado: ${days} ${days === 1 ? 'día' : 'días'} de atraso`),
    methodology: 'Metodología',
    methodologyLink: 'Ver metodología',
    methodologyVersion: 'Versión de metodología',
    methodologyBody: 'La señal pública usa el modelo canónico de riesgo BTC y la última importación CSV validada de CoinMarketCap.',
    disclaimer: 'Los niveles de riesgo son resultados de escenarios para investigación. No son asesoramiento financiero ni instrucciones de trading.',
    thresholdCallouts: 'Precios de umbral más cercanos',
    thresholdNear: (label, price) => `${label} cerca de ${price}`,
    riskHistoryAlternative: 'Alternativa de datos del gráfico de historial de riesgo',
    riskLevelsAlternative: 'Alternativa de datos del gráfico de niveles de riesgo',
    chartCurrentSummary: (date, risk, state, modelPrice, range) => `Última observación ${date}: el riesgo actual es ${risk} (${state}) y el precio del modelo es ${modelPrice}${range}.`,
    chartCurrentRange: (low, high) => `, con mínimo diario reciente ${low} y máximo ${high}`,
    riskHistoryAlternativeNote: (count) => `La tabla muestra las ${count} observaciones más recientes de historial de riesgo disponibles para el gráfico.`,
    riskLevelsAlternativeNote: 'La tabla muestra los precios clave de umbral usados con el gráfico de niveles de riesgo.',
    dateColumn: 'Fecha',
    riskColumn: 'Riesgo',
    priceColumn: 'Precio BTC',
    stateColumn: 'Estado de riesgo',
    thresholdColumn: 'Umbral de riesgo',
    bandColumn: 'Banda',
    nearestModelPriceColumn: 'Precio de modelo más cercano',
    recentRiskHistoryTable: 'Tabla de historial de riesgo reciente',
    riskThresholdPriceTable: 'Tabla de precios de umbral de riesgo',
    history: 'Historial de riesgo',
    levels: 'Niveles de riesgo',
    brief: 'Resumen de hoy',
    changed: 'Qué cambió',
    avoid: 'Evitar ahora',
    confirm: 'Confirmar después',
    waitlistTitle: 'Recibe la señal diaria',
    waitlistBody: 'Deja un correo o usuario de Telegram. La primera cohorte de prueba recibe la alerta de riesgo gratis.',
    placeholder: 'email o @telegram',
    join: 'Unirme a la lista',
    joined: 'Guardado. Estás en la lista de espera de Bitcoin Risk Brief.',
    joinError: 'Introduce un email o usuario de Telegram válido.',
    joining: 'Guardando...',
    privacyNoteTitle: 'Privacidad, términos y aviso legal',
    privacyNoteIntro: 'Bitcoin Risk Brief es solo investigación informativa, no asesoramiento financiero, asesoramiento de inversión ni recomendación de trading.',
    privacyNoteWaitlist: 'La lista de espera almacena el contacto enviado, una copia normalizada, tipo de contacto, idioma, fuente, estado y marcas de tiempo.',
    privacyNoteLogs: 'Los registros operativos pueden incluir método de solicitud, ruta, estado, client key, Cloudflare ray ID, estado de caché y tiempos.',
    privacyNoteLimits: 'No introduzcas información sensible. No se recomienda ninguna acción de compra, venta, cartera o trading, y no se ofrece SLA de soporte pagado.',
    privacyNoteAnalytics: 'El código fuente actual de la app no incluye analítica de producto ni código de cookies de seguimiento.',
    loading: 'Cargando datos de riesgo...',
    empty: 'Aún no hay datos recopilados. Ejecuta collector backfill para poblar TimescaleDB.',
    loadErrorTitle: 'Los datos de riesgo no están disponibles temporalmente',
    loadErrorBody: 'La página no pudo cargar el último paquete de riesgo. Trata la señal como no disponible hasta que la API se recupere.',
    chartLoading: 'Cargando gráfico...',
    historyEmpty: 'El historial de riesgo no está disponible hasta que se carguen observaciones.',
    levelsEmpty: 'Los niveles de riesgo no están disponibles hasta que la última entrada del modelo esté lista.',
    historyError: 'El historial de riesgo no está disponible temporalmente.',
    levelsError: 'Los niveles de riesgo no están disponibles temporalmente.',
    unavailable: 'no disponible',
  },
  ar: {
    languageNavigation: 'اللغة',
    languageSelector: 'اختر اللغة',
    eyebrow: 'إشارة مخاطر BTC اليومية',
    title: 'Bitcoin Risk Brief',
    subtitle: 'قراءة يومية موجزة لما إذا كانت مخاطر BTC مرتفعة أو متوازنة أو قريبة من منطقة خصم.',
    updated: 'آخر تحديث',
    currentRisk: 'المخاطر الحالية',
    price: 'مدخل سعر BTC في النموذج',
    modelPrice: 'سعر النموذج',
    low: 'الأدنى',
    high: 'الأعلى',
    riskChange: 'تغير المخاطر',
    riskChangeContext: 'مقارنة بالملاحظة السابقة',
    modelDrivers: 'محركات النموذج',
    modelDriversBody: 'اتجاه واضح لكل مكون في النموذج بناء على أحدث بيانات يومية تم التحقق منها.',
    driverTrend: 'الاتجاه',
    driverTrendDetail: 'السعر مقارنة بخط الأساس طويل الأجل',
    driverVolatility: 'التقلب',
    driverVolatilityDetail: 'تحركات السعر الأخيرة',
    driverActivity: 'النشاط',
    driverActivityDetail: 'نشاط التداول المعدل حسب حجم السوق',
    driverActivityUnavailableDetail: 'النشاط المعدل حسب حجم السوق غير متاح',
    driverRaises: 'يرفع المخاطر',
    driverNeutral: 'محايد',
    driverLowers: 'يخفض المخاطر',
    driverUnavailable: 'غير متاح',
    riskZones: ['منخفض / محايد', 'محايد / مرتفع'],
    readinessReady: 'الجاهزية مكتملة',
    readinessDegraded: 'الجاهزية متراجعة',
    validationPassed: 'تم اجتياز التحقق',
    validationNeedsAttention: 'التحقق يحتاج إلى مراجعة',
    currentThrough: 'محدث حتى',
    latestCompletedDay: 'آخر يوم مكتمل',
    coverageThrough: 'التغطية حتى',
    freshnessCurrent: 'حداثة البيانات: محدثة',
    staleAge: (days) => (days === null ? 'تأخر البيانات غير متاح' : `متأخرة: ${days} ${days === 1 ? 'يوم' : 'أيام'}`),
    methodology: 'المنهجية',
    methodologyLink: 'عرض المنهجية',
    methodologyVersion: 'إصدار المنهجية',
    methodologyBody: 'تستخدم الإشارة العامة نموذج مخاطر BTC المعتمد وآخر استيراد CoinMarketCap CSV تم التحقق منه.',
    disclaimer: 'مستويات المخاطر هي مخرجات سيناريوهات لأغراض البحث. ليست نصيحة مالية ولا تعليمات تداول.',
    thresholdCallouts: 'أقرب أسعار العتبات',
    thresholdNear: (label, price) => `${label} قرب ${price}`,
    riskHistoryAlternative: 'بديل بيانات مخطط تاريخ المخاطر',
    riskLevelsAlternative: 'بديل بيانات مخطط مستويات المخاطر',
    chartCurrentSummary: (date, risk, state, modelPrice, range) => `أحدث ملاحظة ${date}: المخاطر الحالية ${risk} (${state}) وسعر النموذج ${modelPrice}${range}.`,
    chartCurrentRange: (low, high) => `، مع أدنى سعر يومي حديث ${low} وأعلى سعر ${high}`,
    riskHistoryAlternativeNote: (count) => `يعرض الجدول أحدث ${count} ملاحظات مخاطر متاحة للمخطط.`,
    riskLevelsAlternativeNote: 'يعرض الجدول أسعار عتبات المخاطر الرئيسية المستخدمة مع مخطط مستويات المخاطر.',
    dateColumn: 'التاريخ',
    riskColumn: 'المخاطر',
    priceColumn: 'سعر BTC',
    stateColumn: 'حالة المخاطر',
    thresholdColumn: 'عتبة المخاطر',
    bandColumn: 'النطاق',
    nearestModelPriceColumn: 'أقرب سعر نموذج',
    recentRiskHistoryTable: 'جدول تاريخ المخاطر الأخير',
    riskThresholdPriceTable: 'جدول أسعار عتبات المخاطر',
    history: 'تاريخ المخاطر',
    levels: 'مستويات المخاطر',
    brief: 'ملخص اليوم',
    changed: 'ما الذي تغير',
    avoid: 'ما يجب تجنبه الآن',
    confirm: 'ما يجب تأكيده لاحقا',
    waitlistTitle: 'احصل على الإشارة اليومية',
    waitlistBody: 'اترك بريدا إلكترونيا أو معرف Telegram. ستحصل أول مجموعة اختبار على تنبيه المخاطر مجانا.',
    placeholder: 'email أو @telegram',
    join: 'انضم إلى قائمة الانتظار',
    joined: 'تم الحفظ. أنت الآن في قائمة انتظار Bitcoin Risk Brief.',
    joinError: 'أدخل بريدا إلكترونيا صالحا أو معرف Telegram.',
    joining: 'جار الحفظ...',
    privacyNoteTitle: 'الخصوصية والشروط وإخلاء المسؤولية',
    privacyNoteIntro: 'Bitcoin Risk Brief هو بحث معلوماتي فقط، وليس نصيحة مالية أو استثمارية أو توصية تداول.',
    privacyNoteWaitlist: 'تخزن قائمة الانتظار جهة الاتصال التي ترسلها، ونسخة موحدة منها، ونوع جهة الاتصال، واللغة، والمصدر، والحالة، والطوابع الزمنية.',
    privacyNoteLogs: 'قد تتضمن سجلات التشغيل طريقة الطلب، والمسار، والحالة، وclient key، وCloudflare ray ID، وحالة التخزين المؤقت، والتوقيت.',
    privacyNoteLimits: 'لا تدخل معلومات حساسة. لا يوصى بأي شراء أو بيع أو إجراء محفظة أو تداول، ولا يتم تقديم اتفاقية مستوى خدمة مدفوعة.',
    privacyNoteAnalytics: 'لا يتضمن مصدر التطبيق الحالي تحليلات منتج أو كود ملفات تعريف ارتباط للتتبع.',
    loading: 'جار تحميل بيانات المخاطر...',
    empty: 'لا توجد بيانات مجمعة بعد. شغل collector backfill لملء TimescaleDB.',
    loadErrorTitle: 'بيانات المخاطر غير متاحة مؤقتا',
    loadErrorBody: 'تعذر على الصفحة تحميل أحدث حزمة مخاطر. تعامل مع الإشارة على أنها غير متاحة حتى تتعافى API.',
    chartLoading: 'جار تحميل المخطط...',
    historyEmpty: 'تاريخ المخاطر غير متاح حتى يتم تحميل الملاحظات.',
    levelsEmpty: 'مستويات المخاطر غير متاحة حتى يصبح أحدث مدخل للنموذج جاهزا.',
    historyError: 'تاريخ المخاطر غير متاح مؤقتا.',
    levelsError: 'مستويات المخاطر غير متاحة مؤقتا.',
    unavailable: 'غير متاح',
  },
}
```

- [ ] **Step 4: Run focused locale tests**

Run:

```bash
npm test --prefix frontend -- locales.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/locales.ts frontend/src/locales.test.ts
git commit -m "feat: add frontend locale registry"
```

---

### Task 2: Refactor Frontend App To Use Locale Registry

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css`
- Modify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Update frontend types**

In `frontend/src/types.ts`, add the expanded `Locale` type and adjust brief/waitlist types:

```ts
export type Locale = 'en' | 'ru' | 'zh' | 'de' | 'fr' | 'es' | 'ar'
export type RiskState = 'low' | 'neutral' | 'high'
```

Replace `BriefPayload.sections`:

```ts
  sections: Partial<Record<Locale, BriefSection>> & Record<'en', BriefSection>
```

Replace the waitlist locale fields:

```ts
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
```

- [ ] **Step 2: Update App imports and remove embedded locale objects**

In `frontend/src/App.tsx`, change imports:

```ts
import { copy, getLocaleOption, localeOptions, stateLabel } from './locales'
import type { BriefPayload, Locale, ReadinessPayload, RiskLevel, RiskPoint } from './types'
```

Then delete these existing local definitions from `App.tsx`: the local `type Locale = 'en' | 'ru'` alias, the entire
embedded `const copy` object, and the local `stateLabel(state: string, locale: Locale)` function. Those definitions now
come from `frontend/src/locales.ts`.

- [ ] **Step 3: Make trust values localizable**

Replace `formatTrustValue` with:

```ts
function formatTrustValue(label: string, value: string | null, unavailable: string) {
  return `${label}: ${value ?? unavailable}`
}
```

Update all calls:

```tsx
<em>{formatTrustValue(t.latestCompletedDay, readiness.data.latest_date, t.unavailable)}</em>
<em>{formatTrustValue(t.coverageThrough, readiness.data.covered_end, t.unavailable)}</em>
```

In the methodology `dl`, replace hardcoded unavailable:

```tsx
<div><dt>{t.latestCompletedDay}</dt><dd>{readiness.data.latest_date ?? t.unavailable}</dd></div>
<div><dt>{t.coverageThrough}</dt><dd>{readiness.data.covered_end ?? t.unavailable}</dd></div>
```

- [ ] **Step 4: Set document language and direction from selected locale**

Inside `App`, after the chart media-query effect, add:

```ts
  useEffect(() => {
    const option = getLocaleOption(locale)
    document.documentElement.lang = option.lang
    document.documentElement.dir = option.dir
  }, [locale])
```

- [ ] **Step 5: Replace the two-language button with a compact selector**

Replace the current topbar language button:

```tsx
<button className="lang" onClick={() => setLocale(locale === 'en' ? 'ru' : 'en')}><Languages size={16} /> {locale === 'en' ? 'RU' : 'EN'}</button>
```

with:

```tsx
<label className="language-select">
  <Languages size={16} aria-hidden="true" />
  <span className="sr-only">{t.languageSelector}</span>
  <select
    value={locale}
    onChange={(event) => setLocale(event.target.value as Locale)}
    aria-label={t.languageSelector}
  >
    {localeOptions.map((option) => (
      <option key={option.code} value={option.code}>
        {option.shortLabel}
      </option>
    ))}
  </select>
</label>
```

Change the nav label:

```tsx
<nav className="topbar" aria-label={t.languageNavigation}>
```

- [ ] **Step 6: Add safe brief-section fallback**

Replace:

```ts
  const briefSection = brief.sections[locale]
```

with:

```ts
  const briefSection = brief.sections[locale] ?? brief.sections.en
```

- [ ] **Step 7: Update CSS selector and RTL rules**

In `frontend/src/App.css`, replace `.lang` references with `.language-select` styles:

```css
.brand, .language-select, .methodology-link { display: inline-flex; gap: 8px; align-items: center; color: #c8c4bd; }
.language-select { border: 1px solid #30343b; background: #15171b; color: #f4f0e8; padding: 0 10px; border-radius: 8px; }
.language-select svg { color: #c8c4bd; }
.language-select select { min-height: 38px; border: 0; background: transparent; color: #f4f0e8; font: inherit; font-weight: 800; cursor: pointer; }
.language-select select:focus-visible, .methodology-link:focus-visible, .lead-form input:focus-visible, .lead-form button:focus-visible, .privacy-note summary:focus-visible { outline: 2px solid #f2b84b; outline-offset: 3px; }
[dir="rtl"] .topbar,
[dir="rtl"] .hero,
[dir="rtl"] .metrics-strip,
[dir="rtl"] .brief-grid,
[dir="rtl"] .model-drivers,
[dir="rtl"] .trust-panel,
[dir="rtl"] .waitlist,
[dir="rtl"] .charts {
  direction: rtl;
}
[dir="rtl"] .top-actions,
[dir="rtl"] .brand,
[dir="rtl"] .methodology-link,
[dir="rtl"] .language-select,
[dir="rtl"] .readiness-badge,
[dir="rtl"] .lead-form button,
[dir="rtl"] .privacy-note summary {
  flex-direction: row-reverse;
}
[dir="rtl"] .chart-visual,
[dir="rtl"] .sr-only table {
  direction: ltr;
}
```

In the `@media (max-width: 560px)` block, replace:

```css
.methodology-link, .lang { min-height: 40px; justify-content: center; }
```

with:

```css
.methodology-link, .language-select { min-height: 40px; justify-content: center; }
```

- [ ] **Step 8: Update existing App locale tests for the selector**

In `frontend/src/App.test.tsx`, replace interactions like:

```ts
fireEvent.click(screen.getByRole('button', { name: /ru/i }))
```

with:

```ts
fireEvent.change(screen.getByRole('combobox', { name: /select language/i }), { target: { value: 'ru' } })
```

For tests that run after the language has already changed and the selector accessible name has localized, keep a reference before changing:

```ts
const languageSelector = screen.getByRole('combobox', { name: /select language/i })
fireEvent.change(languageSelector, { target: { value: 'ru' } })
```

- [ ] **Step 9: Add App tests for all new locales and RTL metadata**

Append to `frontend/src/App.test.tsx`:

```ts
test('offers all issue 28 languages and applies document language metadata', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  expect(within(selector).getAllByRole('option').map((option) => option.getAttribute('value'))).toEqual([
    'en',
    'ru',
    'zh',
    'de',
    'fr',
    'es',
    'ar',
  ])

  fireEvent.change(selector, { target: { value: 'de' } })
  expect(await screen.findByText('Aktuelles Risiko')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'de')
  expect(document.documentElement).toHaveAttribute('dir', 'ltr')

  fireEvent.change(selector, { target: { value: 'fr' } })
  expect(await screen.findByText('Risque actuel')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'fr')

  fireEvent.change(selector, { target: { value: 'es' } })
  expect(await screen.findByText('Riesgo actual')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'es')

  fireEvent.change(selector, { target: { value: 'zh' } })
  expect(await screen.findByText('当前风险')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'zh-CN')

  fireEvent.change(selector, { target: { value: 'ar' } })
  expect(await screen.findByText('المخاطر الحالية')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ar')
  expect(document.documentElement).toHaveAttribute('dir', 'rtl')
})

test('submits the selected expanded locale to the waitlist API', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(selector, { target: { value: 'fr' } })
  fireEvent.change(await screen.findByPlaceholderText('email ou @telegram'), { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /rejoindre la liste/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'fr', source: 'landing' })
  })
})

test('falls back to the English generated brief when selected locale is absent from an old snapshot', async () => {
  render(<App />)

  const selector = await screen.findByRole('combobox', { name: /select language/i })
  fireEvent.change(selector, { target: { value: 'de' } })

  expect(await screen.findByText('Heutiger Brief')).toBeInTheDocument()
  expect(screen.getByText('Risk elevated')).toBeInTheDocument()
})
```

- [ ] **Step 10: Update CSS tests**

In the focus-state CSS test, replace:

```ts
expect(css).toContain('.lang:focus-visible')
```

with:

```ts
expect(css).toContain('.language-select select:focus-visible')
```

Add an RTL CSS test:

```ts
test('defines RTL layout rules for Arabic locale', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('[dir="rtl"] .topbar')
  expect(css).toContain('[dir="rtl"] .top-actions')
  expect(css).toContain('[dir="rtl"] .chart-visual')
})
```

- [ ] **Step 11: Run frontend tests**

Run:

```bash
npm test --prefix frontend
```

Expected: PASS.

- [ ] **Step 12: Commit**

```bash
git add frontend/src/types.ts frontend/src/App.tsx frontend/src/App.css frontend/src/App.test.tsx
git commit -m "feat: support expanded frontend locales"
```

---

### Task 3: Expand Backend Waitlist Locale Validation

**Files:**
- Modify: `backend/app/waitlist.py`
- Modify: `backend/tests/test_waitlist.py`

- [ ] **Step 1: Write failing waitlist locale tests**

In `backend/tests/test_waitlist.py`, update imports:

```py
from app.waitlist import InvalidWaitlistContact, normalize_locale, normalize_waitlist_contact
```

Add tests:

```py
    def test_accepts_issue_28_locales(self) -> None:
        for locale in ("en", "ru", "zh", "de", "fr", "es", "ar"):
            with self.subTest(locale=locale):
                self.assertEqual(normalize_locale(locale), locale)

    def test_unknown_locale_falls_back_to_english(self) -> None:
        self.assertEqual(normalize_locale("it"), "en")
        self.assertEqual(normalize_locale(""), "en")
        self.assertEqual(normalize_locale(None), "en")
```

Update the repository test to use one new locale:

```py
        result = await upsert_waitlist_lead(pool, contact="USER@Example.COM", locale="ar", source="landing")
        self.assertEqual(result["locale"], "ar")
        self.assertEqual(args[:5], ("USER@Example.COM", "user@example.com", "email", "ar", "landing"))
```

- [ ] **Step 2: Run focused backend test and confirm it fails**

Run:

```bash
PYTHONPATH=backend:collector python -m unittest backend.tests.test_waitlist
```

Expected: FAIL because `zh`, `de`, `fr`, `es`, and `ar` are not accepted yet.

- [ ] **Step 3: Expand valid locale values**

In `backend/app/waitlist.py`, replace:

```py
VALID_LOCALES = {"en", "ru"}
```

with:

```py
VALID_LOCALES = {"en", "ru", "zh", "de", "fr", "es", "ar"}
```

Keep `normalize_locale()` lowercasing behavior. The chosen Chinese code is lowercase `zh`.

- [ ] **Step 4: Run focused backend test**

Run:

```bash
PYTHONPATH=backend:collector python -m unittest backend.tests.test_waitlist
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/waitlist.py backend/tests/test_waitlist.py
git commit -m "feat: accept expanded waitlist locales"
```

---

### Task 4: Generate Localized Backend Brief Sections

**Files:**
- Modify: `backend/tests/test_brief.py`
- Modify: `backend/app/brief.py`

- [ ] **Step 1: Write failing brief coverage tests**

Replace `backend/tests/test_brief.py` with:

```py
from __future__ import annotations

import unittest

from app.brief import build_brief


SUPPORTED_LOCALES = {"en", "ru", "zh", "de", "fr", "es", "ar"}


class BriefTest(unittest.TestCase):
    def test_brief_mentions_risk_state_and_change(self) -> None:
        latest = {"risk": 0.72, "risk_state": "high", "price_usd": 100000, "timestamp": "2026-06-26T00:00:00Z"}
        previous = {"risk": 0.61, "risk_state": "neutral", "price_usd": 92000, "timestamp": "2026-06-25T00:00:00Z"}
        brief = build_brief(latest, previous)
        self.assertEqual(brief["risk_state"], "high")
        self.assertEqual(set(brief["sections"].keys()), SUPPORTED_LOCALES)
        self.assertTrue(brief["delta_risk"] > 0)

    def test_brief_sections_are_conservative_in_every_locale(self) -> None:
        latest = {"risk": 0.28, "risk_state": "low", "price_usd": 62000, "timestamp": "2026-06-26T00:00:00Z"}
        previous = {"risk": 0.35, "risk_state": "neutral", "price_usd": 64000, "timestamp": "2026-06-25T00:00:00Z"}
        brief = build_brief(latest, previous)

        for locale in SUPPORTED_LOCALES:
            with self.subTest(locale=locale):
                section = brief["sections"][locale]
                self.assertTrue(section["summary"])
                self.assertTrue(section["what_changed"])
                self.assertTrue(section["avoid_now"])
                self.assertTrue(section["confirm_next"])
                self.assertNotIn("buy now", section["summary"].lower())
                self.assertNotIn("sell now", section["summary"].lower())

        self.assertIn("Risk cooled", brief["sections"]["en"]["what_changed"])
        self.assertIn("Риск снизился", brief["sections"]["ru"]["what_changed"])
        self.assertIn("风险下降", brief["sections"]["zh"]["what_changed"])
        self.assertIn("Risiko ging zurück", brief["sections"]["de"]["what_changed"])
        self.assertIn("Le risque a reculé", brief["sections"]["fr"]["what_changed"])
        self.assertIn("El riesgo bajó", brief["sections"]["es"]["what_changed"])
        self.assertIn("انخفضت المخاطر", brief["sections"]["ar"]["what_changed"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run focused brief test and confirm it fails**

Run:

```bash
PYTHONPATH=backend:collector python -m unittest backend.tests.test_brief
```

Expected: FAIL because `build_brief()` only returns `en` and `ru`.

- [ ] **Step 3: Refactor backend brief copy into locale dictionaries**

In `backend/app/brief.py`, keep the public `build_brief(latest, previous=None)` signature. Replace `_risk_copy_en`, `_risk_copy_ru`, and the hardcoded `sections` assembly with dictionary-driven copy.

Use this structure:

```py
from __future__ import annotations

from typing import Any


SUPPORTED_BRIEF_LOCALES = ("en", "ru", "zh", "de", "fr", "es", "ar")

RISK_COPY: dict[str, dict[str, tuple[str, str, str]]] = {
    "en": {
        "high": (
            "Risk is elevated. The model is flagging a stretched BTC regime.",
            "Avoid treating upside momentum as a fresh low-risk entry without confirmation.",
            "Confirm with liquidity, trend quality, and whether risk cools while price holds structure.",
        ),
        "low": (
            "Risk is low. BTC is closer to a discounted or washed-out regime.",
            "Avoid treating the low-risk zone as an immediate reversal signal.",
            "Confirm with improving trend, liquidity, and reduced forced-selling pressure.",
        ),
        "neutral": (
            "Risk is neutral. BTC is not showing an extreme risk reading right now.",
            "Avoid forcing a directional conclusion from the risk score alone.",
            "Confirm with trend, liquidity, and market rotation before changing exposure.",
        ),
    },
    "ru": {
        "high": (
            "Риск повышен. Модель видит перегретый режим BTC.",
            "Не стоит считать импульс вверх новой низкорисковой точкой входа без подтверждения.",
            "Проверьте ликвидность, качество тренда и снижается ли риск при удержании структуры цены.",
        ),
        "low": (
            "Риск низкий. BTC ближе к зоне дисконта или капитуляции.",
            "Не стоит считать низкий риск мгновенным сигналом разворота.",
            "Проверьте восстановление тренда, ликвидность и снижение давления продавцов.",
        ),
        "neutral": (
            "Риск нейтральный. Сейчас нет экстремального риск-сигнала по BTC.",
            "Не стоит делать направленный вывод только по риск-метрике.",
            "Проверьте тренд, ликвидность и рыночную ротацию перед изменением экспозиции.",
        ),
    },
    "zh": {
        "high": (
            "风险偏高。模型正在标记 BTC 处于偏拉伸的状态。",
            "避免在没有确认的情况下，把上涨动能视为新的低风险入场点。",
            "请结合流动性、趋势质量，以及价格保持结构时风险是否降温来确认。",
        ),
        "low": (
            "风险偏低。BTC 更接近折价或被充分释放压力的状态。",
            "避免把低风险区域直接理解为立即反转信号。",
            "请结合趋势改善、流动性和强制卖压下降来确认。",
        ),
        "neutral": (
            "风险中性。BTC 当前没有显示极端风险读数。",
            "避免仅凭风险分数得出方向性结论。",
            "在改变敞口前，请结合趋势、流动性和市场轮动确认。",
        ),
    },
    "de": {
        "high": (
            "Das Risiko ist erhöht. Das Modell markiert ein überdehntes BTC-Regime.",
            "Behandeln Sie Aufwärtsmomentum ohne Bestätigung nicht als neuen risikoarmen Einstieg.",
            "Prüfen Sie Liquidität, Trendqualität und ob das Risiko abkühlt, während der Preis seine Struktur hält.",
        ),
        "low": (
            "Das Risiko ist niedrig. BTC liegt näher an einem rabattierten oder ausgewaschenen Regime.",
            "Behandeln Sie die Niedrigrisiko-Zone nicht als sofortiges Umkehrsignal.",
            "Prüfen Sie eine Verbesserung des Trends, Liquidität und nachlassenden Verkaufsdruck.",
        ),
        "neutral": (
            "Das Risiko ist neutral. BTC zeigt derzeit keinen extremen Risikowert.",
            "Leiten Sie aus dem Risikoscore allein keine Richtungsaussage ab.",
            "Prüfen Sie Trend, Liquidität und Marktrotation, bevor Sie die Exponierung ändern.",
        ),
    },
    "fr": {
        "high": (
            "Le risque est élevé. Le modèle signale un régime BTC étiré.",
            "Évitez de traiter la dynamique haussière comme une nouvelle entrée à faible risque sans confirmation.",
            "Confirmez avec la liquidité, la qualité de la tendance et le refroidissement du risque si le prix tient sa structure.",
        ),
        "low": (
            "Le risque est faible. BTC est plus proche d’un régime décoté ou purgé.",
            "Évitez de considérer la zone de faible risque comme un signal de retournement immédiat.",
            "Confirmez avec une amélioration de la tendance, la liquidité et une baisse de la pression vendeuse forcée.",
        ),
        "neutral": (
            "Le risque est neutre. BTC ne montre pas de lecture de risque extrême pour le moment.",
            "Évitez de tirer une conclusion directionnelle du seul score de risque.",
            "Confirmez avec la tendance, la liquidité et la rotation de marché avant de modifier l’exposition.",
        ),
    },
    "es": {
        "high": (
            "El riesgo es elevado. El modelo marca un régimen de BTC extendido.",
            "Evita tratar el impulso alcista como una nueva entrada de bajo riesgo sin confirmación.",
            "Confirma con liquidez, calidad de tendencia y si el riesgo se enfría mientras el precio mantiene estructura.",
        ),
        "low": (
            "El riesgo es bajo. BTC está más cerca de un régimen descontado o depurado.",
            "Evita interpretar la zona de bajo riesgo como una señal inmediata de reversión.",
            "Confirma con mejora de tendencia, liquidez y menor presión de venta forzada.",
        ),
        "neutral": (
            "El riesgo es neutral. BTC no muestra ahora una lectura de riesgo extrema.",
            "Evita forzar una conclusión direccional solo a partir de la puntuación de riesgo.",
            "Confirma con tendencia, liquidez y rotación de mercado antes de cambiar exposición.",
        ),
    },
    "ar": {
        "high": (
            "المخاطر مرتفعة. يشير النموذج إلى أن وضع BTC ممتد.",
            "تجنب اعتبار الزخم الصاعد نقطة دخول منخفضة المخاطر من دون تأكيد.",
            "أكد ذلك عبر السيولة وجودة الاتجاه وما إذا كانت المخاطر تهدأ بينما يحافظ السعر على هيكله.",
        ),
        "low": (
            "المخاطر منخفضة. BTC أقرب إلى حالة خصم أو ضغط بيعي مستنفد.",
            "تجنب اعتبار منطقة المخاطر المنخفضة إشارة انعكاس فورية.",
            "أكد ذلك عبر تحسن الاتجاه والسيولة وتراجع ضغط البيع القسري.",
        ),
        "neutral": (
            "المخاطر محايدة. لا يظهر BTC قراءة مخاطر متطرفة الآن.",
            "تجنب استخلاص نتيجة اتجاهية من درجة المخاطر وحدها.",
            "أكد ذلك عبر الاتجاه والسيولة ودوران السوق قبل تغيير التعرض.",
        ),
    },
}
```

Add dynamic change helpers below the dictionaries:

```py
def _risk_copy(locale: str, state: str) -> tuple[str, str, str]:
    locale_copy = RISK_COPY.get(locale, RISK_COPY["en"])
    return locale_copy.get(state, locale_copy["neutral"])


def _change_copy(locale: str, delta_risk: float) -> str:
    if abs(delta_risk) < 0.01:
        return {
            "en": "Risk is broadly unchanged from the previous observation.",
            "ru": "Риск почти не изменился относительно предыдущего наблюдения.",
            "zh": "风险与上一条观测基本持平。",
            "de": "Das Risiko ist gegenüber der vorherigen Beobachtung weitgehend unverändert.",
            "fr": "Le risque est globalement inchangé par rapport à l’observation précédente.",
            "es": "El riesgo se mantiene prácticamente sin cambios frente a la observación anterior.",
            "ar": "المخاطر شبه مستقرة مقارنة بالملاحظة السابقة.",
        }[locale]
    if delta_risk > 0:
        return {
            "en": f"Risk increased by {delta_risk:.2f} points.",
            "ru": f"Риск вырос на {delta_risk:.2f} пункта.",
            "zh": f"风险上升 {delta_risk:.2f} 点。",
            "de": f"Das Risiko stieg um {delta_risk:.2f} Punkte.",
            "fr": f"Le risque a augmenté de {delta_risk:.2f} point.",
            "es": f"El riesgo subió {delta_risk:.2f} puntos.",
            "ar": f"ارتفعت المخاطر بمقدار {delta_risk:.2f} نقطة.",
        }[locale]
    cooled = abs(delta_risk)
    return {
        "en": f"Risk cooled by {cooled:.2f} points.",
        "ru": f"Риск снизился на {cooled:.2f} пункта.",
        "zh": f"风险下降 {cooled:.2f} 点。",
        "de": f"Risiko ging zurück um {cooled:.2f} Punkte.",
        "fr": f"Le risque a reculé de {cooled:.2f} point.",
        "es": f"El riesgo bajó {cooled:.2f} puntos.",
        "ar": f"انخفضت المخاطر بمقدار {cooled:.2f} نقطة.",
    }[locale]
```

Replace the `sections` portion of `build_brief()` with:

```py
    sections = {}
    for locale in SUPPORTED_BRIEF_LOCALES:
        summary, avoid, confirm = _risk_copy(locale, state)
        sections[locale] = {
            "summary": summary,
            "what_changed": _change_copy(locale, delta_risk),
            "avoid_now": avoid,
            "confirm_next": confirm,
        }
```

and return:

```py
        "sections": sections,
```

- [ ] **Step 4: Run focused brief test**

Run:

```bash
PYTHONPATH=backend:collector python -m unittest backend.tests.test_brief
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/brief.py backend/tests/test_brief.py
git commit -m "feat: localize generated brief sections"
```

---

### Task 5: Update API And Product Documentation

**Files:**
- Modify: `docs/api-reference.md`
- Modify: `README.md`
- Modify: `docs/frontend-qa.md`
- Modify: `docs/testing-and-quality.md`
- Modify: `docs/production-readiness.md`
- Modify: `docs/superpowers/specs/2026-07-01-localization-quality-language-expansion-design.md`

- [ ] **Step 1: Update API reference for brief locales**

In `docs/api-reference.md`, in the `/api/brief/latest` section after the JSON block, add:

```md
Brief `sections` are generated for `en`, `ru`, `zh`, `de`, `fr`, `es`, and `ar`. `zh` is Simplified Chinese.
Older persisted local snapshots may contain only `en` and `ru` until the collector writes a fresh brief snapshot.
```

- [ ] **Step 2: Update API reference for waitlist locale values**

In `docs/api-reference.md`, below the waitlist request JSON, add:

```md
Accepted locale values are `en`, `ru`, `zh`, `de`, `fr`, `es`, and `ar`. Unsupported values are normalized to `en`
before storage.
```

- [ ] **Step 3: Update README language statement**

In `README.md`, replace:

```md
- Daily brief payload in English and Russian.
```

with:

```md
- Daily brief payload in English, Russian, Simplified Chinese, German, French, Spanish, and Arabic.
```

- [ ] **Step 4: Update QA docs that currently defer Arabic and Chinese**

In `docs/frontend-qa.md`, replace the Phase 8 localization paragraph that says Arabic and Chinese remain disabled with:

```md
If issue #28 localization expansion is enabled before active traffic, repeat the launch pass for English, Russian,
Simplified Chinese (`zh`), German, French, Spanish, and Arabic. Check long localized labels in buttons, badges, chart
labels, waitlist states, degraded/error states, and mobile layouts. Arabic requires explicit `dir="rtl"` verification;
charts and numeric data should remain readable and not be visually reversed.
```

In `docs/testing-and-quality.md`, replace the matching localization paragraph with the same scope and QA requirement.

In `docs/production-readiness.md`, replace the paragraph around the localization browser/device pass with:

```md
If issue #28 localization expansion is implemented before active traffic, include English, Russian, Simplified Chinese,
German, French, Spanish, and Arabic in the browser/device pass. Arabic must include right-to-left layout verification,
waitlist locale attribution, and checks that chart data, USD prices, and ISO dates remain readable.
```

- [ ] **Step 5: Mark the older localization spec as superseded by issue 28**

At the top of `docs/superpowers/specs/2026-07-01-localization-quality-language-expansion-design.md`, update the status note to:

```md
> Status: superseded in scope by GitHub issue #28 as of 2026-07-13. The earlier recommendation deferred Arabic and
> Chinese; issue #28 accepts the larger scope and requires Chinese, German, French, Spanish, and Arabic support.
```

In the same spec, add a short note under "Deferred scope":

```md
GitHub issue #28 intentionally promotes Arabic and Chinese into implementation scope. Arabic must include RTL QA, and
Chinese is implemented as Simplified Chinese under locale code `zh`.
```

- [ ] **Step 6: Review documentation diff**

Run:

```bash
git diff -- docs/api-reference.md README.md docs/frontend-qa.md docs/testing-and-quality.md docs/production-readiness.md docs/superpowers/specs/2026-07-01-localization-quality-language-expansion-design.md
```

Expected: the diff only updates language-scope statements and does not rewrite unrelated launch-readiness content.

- [ ] **Step 7: Commit**

```bash
git add docs/api-reference.md README.md docs/frontend-qa.md docs/testing-and-quality.md docs/production-readiness.md docs/superpowers/specs/2026-07-01-localization-quality-language-expansion-design.md
git commit -m "docs: align localization scope with issue 28"
```

---

### Task 6: Full Verification And Final Review

**Files:**
- No new files expected.

- [ ] **Step 1: Run all frontend tests**

Run:

```bash
npm test --prefix frontend
```

Expected: PASS.

- [ ] **Step 2: Run frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected: PASS.

- [ ] **Step 3: Run Python tests**

Run:

```bash
./scripts/manage.sh test-python
```

Expected: PASS.

- [ ] **Step 4: Run Playwright smoke if local browsers are installed**

Run:

```bash
npm run smoke --prefix frontend
```

Expected: PASS. If this cannot run because browsers are not installed in the environment, record the exact failure and rely on Vitest/build plus a manual browser check.

- [ ] **Step 5: Manual/browser QA checklist**

Start the app using the repo's normal local flow or an existing dev server. Verify these states at desktop width and a mobile width around `390px`:

```md
- [ ] Language selector lists EN, RU, 中文, DE, FR, ES, AR.
- [ ] Selecting each locale updates the hero/current-risk/waitlist/methodology copy.
- [ ] Selecting Arabic sets `<html lang="ar" dir="rtl">`.
- [ ] Arabic layout does not overlap cards, buttons, waitlist input, chart panels, or threshold labels.
- [ ] Chart data, USD prices, percentages, and ISO dates remain readable in Arabic.
- [ ] Waitlist submission sends the selected locale code.
- [ ] Old brief snapshots without a selected locale display English generated brief text instead of crashing.
```

- [ ] **Step 6: Final self-review**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors. `git status --short` should only show intentional uncommitted changes if the worker did not commit each task.

Review:

```bash
git diff HEAD~5..HEAD --stat
git diff HEAD~5..HEAD -- frontend/src/App.tsx frontend/src/locales.ts backend/app/brief.py backend/app/waitlist.py
```

Confirm:

- no financial-advice wording was introduced;
- all supported locale lists match exactly: `en`, `ru`, `zh`, `de`, `fr`, `es`, `ar`;
- Arabic is the only RTL locale;
- frontend brief fallback remains in place;
- docs no longer say Arabic/Chinese are disabled for issue #28 scope.

- [ ] **Step 7: Final commit if any verification fixes were needed**

```bash
git add frontend backend docs README.md
git commit -m "fix: finalize localization expansion verification"
```

Skip this commit if there were no changes after Task 5.

## Handoff Acceptance Criteria

The implementing agent is done when:

- `npm test --prefix frontend` passes.
- `npm run build --prefix frontend` passes.
- `./scripts/manage.sh test-python` passes.
- The UI selector supports `en`, `ru`, `zh`, `de`, `fr`, `es`, and `ar`.
- Arabic sets document RTL direction and passes desktop/mobile layout review.
- Waitlist submissions store the selected expanded locale.
- Backend brief generation includes all supported locales.
- Docs agree with the new issue #28 scope.
