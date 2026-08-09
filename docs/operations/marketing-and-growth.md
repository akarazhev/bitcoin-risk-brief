# Marketing And Growth

> **Operational log.** These entries record what was verified and when. They are not claims about product capability.

This playbook turns the current Bitcoin Risk Brief web product into a focused four-week founder-led demand test. It is
for the small operator-watched pilot, not a broad public launch, an automated lifecycle campaign, or a claim that the
product has found product-market fit.

The public product is [bitcoinriskbrief.minihub.app](https://bitcoinriskbrief.minihub.app/). The operating companion is
the [Pilot Learning Loop](pilot-learning-loop.md).

## Launch Hypothesis

Self-directed, long-horizon Bitcoin holders will return to a one-minute daily risk brief when it answers four questions
without requiring them to interpret a chart terminal:

1. Is modelled Bitcoin risk low, neutral, or high?
2. What changed in the model?
3. Is the input data fresh and the product ready?
4. Which hypothetical price levels would move the score into another risk band?

The four-week pilot should test the existing page before adding another product surface. The initial success signal is
not reach alone. It is a combination of qualified visits, alert-interest leads, confirmed repeat use, useful feedback,
and explicit willingness to consider a small paid recurring product.

## Audience

### Primary ICP

The primary audience is an English-speaking Bitcoin holder who:

- reviews a BTC allocation, DCA plan, or rebalance decision weekly or monthly;
- holds for months or years rather than trades intraday;
- already checks charts, sentiment, cycle indicators, newsletters, or social feeds;
- wants one consistent risk context instead of another multi-chart terminal;
- cares about methodology, data freshness, and what would change the current signal;
- understands that a model is a research input, not a price forecast or trade instruction.

### Secondary ICP

The secondary audience is a Russian-speaking holder with the same long-horizon workflow, reachable through direct
founder relationships and permission-based Telegram communities. Russian is the second campaign language because the
product already supports it and the channel can produce high-context feedback. The other supported locales remain
available in the product but are not active acquisition markets during this test.

### Non-Target Users

Do not optimize the pilot for:

- intraday traders looking for live entries, exits, or leverage signals;
- people asking for guaranteed returns, a price prediction, or an automated portfolio decision;
- professional analysts who require a full on-chain terminal, raw data export, or many configurable indicators;
- institutions that require an SLA, compliance review, redistribution rights, or white-label delivery;
- audiences reached through scraped lists, unsolicited bulk messages, or promotion that violates community rules.

## Job To Be Done

> When I review Bitcoin, help me understand the current modelled risk state and what would materially change it, so I
> can add consistent context to my own decision process without spending time across several dashboards.

## Positioning

**Category:** a daily Bitcoin risk research brief.

**Positioning statement:** Bitcoin Risk Brief is a one-minute daily research brief that shows whether modelled BTC risk
is low, neutral, or high, how the score changed, whether the data is trustworthy, and which price scenarios would move
the signal into another band.

The product should not be marketed as merely another Bitcoin risk score. Its strongest current combination is:

- one deterministic daily signal instead of a chart catalogue;
- visible readiness, latest covered date, and data freshness;
- a concise explanation grounded in the model inputs;
- a price-scenario ladder that shows what could change the risk state;
- a public methodology version and interpretation limits;
- the same focused workflow in seven product locales.

### Competitive Alternatives

These public alternatives were reviewed on 2026-07-31. The comparison is directional; re-check it before publishing a
named comparison because packaging and pricing can change.

| Alternative | What it is good at | Bitcoin Risk Brief angle | Do not claim |
| --- | --- | --- | --- |
| [Glassnode Market Compass](https://glassnode.com/products/studio/market-compass) and [Bitcoin Vector](https://glassnode.com/pricing/vector) | Broad professional market intelligence and packaged Bitcoin market context. | A narrower, more focused daily brief for a holder who does not need a professional terminal. | That Bitcoin Risk Brief has broader data, institutional validation, or superior predictive accuracy. |
| [CryptoQuant](https://cryptoquant.com/en/pricing) | On-chain and market analytics, dashboards, and alerts across paid tiers. | One opinionated daily model with a visible readiness state and explainable price scenarios. | That one risk score replaces a professional analytics workflow. |
| [BitcoinRisk.net](https://bitcoinrisk.net/) | A direct free Bitcoin-risk alternative with a public methodology, historical score, alerts, and API packaging. | Compete on the clarity of the daily brief, published model inputs, operational freshness, and scenario ladder. | Exclusivity, category novelty, or feature breadth. |
| Manual charts, newsletters, and social feeds | Flexible and familiar sources with many viewpoints. | Reduce daily synthesis time and keep the same interpretation frame from one day to the next. | That the brief removes uncertainty or makes the user's decision. |

## Message Hierarchy

Use the layers in order. A post does not need every layer, but it should not lead with a secondary feature.

1. **Outcome:** understand Bitcoin's current modelled risk in under a minute.
2. **Change:** see how the score moved and what price scenarios would change the band.
3. **Trust:** verify freshness, readiness, covered date, and methodology version.
4. **Boundary:** use it as research context, not financial or investment advice.
5. **Invitation:** join the small pilot if a band-change alert or weekly context would be useful.

### Proof Points Available Today

- Daily BTC risk state with low (`< 0.30`), neutral (`0.30` to `< 0.70`), and high (`>= 0.70`) bands.
- Model price identified as HLC3 rather than presented as a live spot price.
- Latest covered date, readiness, freshness, row count, and methodology version.
- Two-year history view and a practical `0.20` to `0.80` risk-level scenario window.
- English, Russian, Chinese, German, French, Spanish, and Arabic product locales.
- Waitlist capture for email or Telegram interest; notifications are not sent yet.

### Main Objections

| Objection | Honest response | Evidence or next question |
| --- | --- | --- |
| “Is this a price prediction or buy/sell signal?” | No. It is a modelled-risk output and hypothetical scenario ladder. It does not estimate future returns or choose an action. | Point to the interpretation limits and ask whether this boundary is clear before discussing usefulness. |
| “Why should I trust one number?” | Do not ask for blind trust. Show the methodology version, inputs, bands, latest covered date, readiness, freshness, and the information the model omits. | Ask which assumption or missing input prevents recurring use. Route repeated gaps to issue #42. |
| “Why not use a free risk-score site?” | Free direct alternatives exist. Bitcoin Risk Brief is testing whether a shorter daily explanation, visible operational state, and scenario ladder make the workflow more useful. | Ask the user to compare the time and clarity of both workflows; do not claim superior accuracy. |
| “Why not use Glassnode or CryptoQuant?” | Those products cover much broader professional analysis. This product is intentionally for a narrower one-minute daily check. | Qualify whether the person wants focus or a research terminal; terminal users are not the initial ICP. |
| “Is that the current spot price?” | No. The displayed model price is HLC3 from the completed daily candle. Scenario prices are hypothetical model inputs. | Ask whether the labels prevent confusion; record repeated model-price questions. |
| “Will I receive an alert after joining?” | Not yet. The current form stores pilot interest for manual founder follow-up; automated email and Telegram delivery are not implemented. | Ask which band-change or digest delivery would be useful. Route CTA confusion to issue #43. |
| “Why would I pay for something available on the web?” | There is no paid product today. The test asks whether reliable alerts and recurring context could save enough review time to justify a small founding pilot. | Ask the paid-intent question only after repeat use; do not accept payment from this playbook. |

## Landing-Page Copy Variants

These are candidates for issue [#43](https://github.com/akarazhev/bitcoin-risk-brief/issues/43), not current page copy.
After that issue is implemented, use one variant for a complete weekly cycle before changing it. Preserve the readiness,
lead-storage, notification-status, and no-advice copy already in the product.

### English A: Clarity

**Headline:** Bitcoin risk, explained in under a minute.

**Subheadline:** See whether modelled BTC risk is low, neutral, or high, how the score changed, and the price scenarios
that would move the signal.

**CTA:** Join the first risk-band alert test

### English B: Focus

**Headline:** One daily Bitcoin risk signal. No chart maze.

**Subheadline:** A concise, methodology-backed brief with freshness, current model-input directions, and risk-band price
scenarios.

**CTA:** Join the alert pilot

### English C: Scenario

**Headline:** See what would change Bitcoin's risk state.

**Subheadline:** Start with today's modelled risk, then explore the hypothetical price levels associated with lower or
higher risk bands.

**CTA:** Follow future band changes

### Russian A: Clarity

**Headline:** Риск Bitcoin — понятно и меньше чем за минуту.

**Subheadline:** Посмотрите текущий модельный риск BTC, изменение оценки и ценовые сценарии перехода в другой диапазон.

**CTA:** Записаться в первый тест уведомлений о смене диапазона

### Russian B: Focus

**Headline:** Один ежедневный сигнал риска Bitcoin. Без лабиринта графиков.

**Subheadline:** Краткий отчёт с методологией, свежестью данных, факторами модели и ценовыми сценариями риска.

**CTA:** Присоединиться к пилоту уведомлений

### Russian C: Scenario

**Headline:** Узнайте, что изменит текущий риск Bitcoin.

**Subheadline:** Начните с сегодняшнего модельного риска и изучите гипотетические цены для соседних диапазонов.

**CTA:** Следить за изменениями риска

## Initial Acquisition Channels

### 1. Founder Outreach

Send five to ten individual messages per week to people the founder already knows or has a legitimate reason to
contact. Explain why the product may fit that person's workflow, ask for one specific action, and make follow-up
optional. Do not paste the same pitch into unrelated conversations or export private replies into Git.

This channel fits the pilot because it produces high-context conversations before reliable first-party attribution
exists.

Best action: open the brief on two different days, then answer one question about clarity or alert usefulness.

### 2. X Organic

Publish up to three English posts per week from an account with an authentic connection to the product:

- one current-state post after a readiness check;
- one scenario or methodology explainer;
- one founder-learning or weekly-summary post.

This channel fits the English ICP because Bitcoin research conversations and time-stamped market context are already
shared publicly there, while the post itself can demonstrate value before asking for a click.

Prefer a useful observation that stands on its own. Avoid repetitive link-only posts, engagement bait, predictions,
artificial urgency, and reply spam.

### 3. Permission-Based Telegram Communities

Use Russian or English according to the community. Ask an administrator when promotion rules are not explicit. Publish
at most one original post per community per week and one substantive reply if members ask questions. Disclose the
founder relationship. Do not use scraped member lists or unsolicited direct messages.

This channel fits the secondary ICP because permission-based communities support discussion in Russian and can surface
methodology or trust objections that a click metric cannot explain.

## Campaign Vocabulary

Use consistent labels in links, operator notes, and future analytics:

| Field | Value or allowlist |
| --- | --- |
| campaign | `pilot_2026q3` |
| active source | `founder_outreach`, `x_organic`, `telegram_community` |
| active medium | `direct`, `social`, `community` |
| reserved for a later approved test | source: `creator_referral`, `weekly_digest`; medium: `referral`, `digest` |
| content | `risk_state`, `price_ladder`, `methodology`, `weekly_digest`, `alert_pilot` |

Example campaign link:

```text
https://bitcoinriskbrief.minihub.app/?utm_campaign=pilot_2026q3&utm_source=x_organic&utm_medium=social&utm_content=risk_state
```

These names are a controlled vocabulary, not a claim that attribution exists today. The current frontend submits the
waitlist source as `landing`, and the app does not yet provide first-party campaign or repeat-use analytics. Until issue
[#45](https://github.com/akarazhev/bitcoin-risk-brief/issues/45) is implemented, use the best available bot-filtered
aggregate traffic view plus a sanitized manual campaign log. Do not infer repeat users from IP addresses. Issue
[#43](https://github.com/akarazhev/bitcoin-risk-brief/issues/43) is the dependency for a clearer alert-specific demand
test and source propagation.

## Funnel And Evidence Definitions

| Stage | Evidence | Current limitation |
| --- | --- | --- |
| Qualified visit | A bot-filtered landing-page visit during a deliberate campaign window from an allowlisted source or the best available aggregate traffic view. | Source-level attribution is incomplete before issue #45. |
| Engaged visit | Methodology, history, scenario, or brief interaction measured by privacy-preserving events. | Treat as unavailable until issue #45; do not substitute raw logs or IP tracking. |
| Alert-interest lead | A new waitlist lead during the campaign. It is the conversion numerator and a weaker proxy for alert interest until issue #43 makes that intent explicit. | Current waitlist is a lead store and sends no notifications. |
| Direct alert confirmation | A voluntary answer that a band-change alert would be useful. Treat it as supporting interview evidence, never as a visit-to-lead conversion numerator. | Store only a sanitized answer category and theme. |
| Confirmed repeat user | A person who voluntarily says they opened the brief on at least two different days, or a privacy-preserving return estimate after issue #45. | Do not reconstruct identity from infrastructure data. |
| Feedback conversation | A two-way conversation that produces at least one sanitized product, trust, or workflow theme. | Counts and themes only go into evidence notes. |
| Paid intent | An explicit `yes` or `probably` to considering a defined `EUR 9-19/month` founding pilot after the value and limits are explained. | No payment, entitlement, or paid launch is authorized by this playbook. |

For conversion, use new leads divided by qualified visits in the same campaign window. Report both the count and the
rate. Exclude known operator checks and obvious bots. If fewer than 100 qualified visits are observable, label the cycle
distribution-inconclusive rather than treating a conversion percentage as decisive.

## Four-Week Experiment

### Week 0: Readiness And Baseline

- Confirm public readiness is HTTP 200, data is fresh, and the latest covered date is the expected completed UTC day.
- Save only the sanitized readiness fields allowed by the Pilot Learning Loop.
- Record aggregate baseline traffic and active waitlist total outside Git.
- Confirm the public methodology, privacy note, and no-advice disclaimer are accessible.
- Prepare the campaign log with the vocabulary above.
- Pause if readiness, waitlist health, privacy handling, or support ownership is uncertain.

### Week 1: The One-Minute Risk Context

Hypothesis: the clearest entry point is one concise daily signal, not a feature list.

- Publish two current-state posts and one founder-learning post on X.
- Publish one permission-based Telegram introduction per selected community.
- Send five to ten individual founder messages.
- Ask users to return on a second day and name the one part they still had to interpret.

### Week 2: The Price-Scenario Ladder

Hypothesis: showing what would move the model into another band is more useful than showing the score alone.

- Publish one time-stamped scenario example and one short explanation of hypothetical levels.
- Ask whether the scenario ladder changes what the user checks next.
- Record repeated confusion about model price, spot price, prediction, or risk thresholds as separate themes.

### Week 3: Methodology And Trust

Hypothesis: visible freshness, readiness, and a compact methodology explanation increase trust enough to support repeat
use.

- Publish the methodology explainer below.
- Show the model version, latest covered date, risk bands, and interpretation limits.
- Ask users what evidence they need before relying on the brief as recurring research context.
- Route repeated explanation gaps to issues
  [#41](https://github.com/akarazhev/bitcoin-risk-brief/issues/41) and
  [#42](https://github.com/akarazhev/bitcoin-risk-brief/issues/42).

### Week 4: Recurring Value And Paid Intent

Hypothesis: users who return want a band-change alert or a weekly context summary enough to consider a modest founding
pilot.

- Publish the weekly digest using the template below.
- Ask confirmed repeat users which delivery format they would prefer: email, Telegram, or web only.
- Ask the paid-intent question only after the user understands what exists and what does not.
- Produce a sanitized end-of-cycle evidence packet and make the smallest supported decision.

## Weekly Cadence

| Activity | Cadence | Owner check |
| --- | --- | --- |
| Public readiness | Before every deliberate traffic window and once per active pilot day | Fresh, ready, expected covered date |
| X | Up to three posts per week | Useful standalone content, report date if current values appear |
| Telegram community | Up to one original post per community per week | Permission/rules checked, founder relationship disclosed |
| Founder outreach | Five to ten individual messages per week | Legitimate relationship or context, no bulk send |
| Feedback review | Same day after a promotion window; otherwise twice weekly | Counts and sanitized themes only |
| Cumulative scorecard progress | End of each weekly cycle | Counts, denominators, limitations; no final classification before Week 4 |

## Four-Week Scorecard

Record cumulative progress each week, but classify the complete test only after Week 4 because paid intent is introduced
in the final cycle. Pause remains an immediate override at any time. Evaluate the final test across all five signal
groups: a single strong vanity metric does not override missing retention, trust, or safety evidence. These numbers are
operating thresholds for this pilot, not external industry benchmarks; revise them only between complete four-week
tests and record why.

| Decision | Qualified visits | Alert-interest | Repeat use | Conversations | Paid intent |
| --- | ---: | --- | --- | ---: | ---: |
| **Strong** | `>= 200` | `>= 20` new leads and `>= 10%` visit-to-lead conversion | `>= 10` confirmed repeat users, or `>= 20%` privacy-preserving seven-day return estimate after issue #45 | `>= 8` | `>= 3` explicit `yes` or `probably` responses |
| **Continue** | `>= 100` | `>= 10` new leads and `>= 5%` conversion | `>= 5` confirmed repeat users, or `>= 10%` return estimate after issue #45 | `>= 4` | `>= 1` explicit positive response |
| **Adjust** | `>= 200` but lead conversion is `< 5%`, or one repeated clarity/trust objection appears in `>= 3` conversations | Change one message, audience, or page element; do not change all three in one cycle. | Use direct confirmation until privacy-preserving analytics exist. | Interview the objection, not the desired feature. | Re-test only after the value proposition is understood. |
| **Stop current message/channel combination** | `>= 200` | `< 5` new leads (`< 2.5%`) | `0` confirmed repeat users | No recurring problem or workflow theme | `0` positive responses after four cycles |

Apply the rows in this order:

1. **Pause** immediately if any readiness, freshness, privacy, support, or data-correction gate fails.
2. **Distribution-inconclusive** if fewer than 100 qualified visits can be observed.
3. **Strong** only when every Strong threshold is met.
4. **Stop current message/channel combination** only when every Stop condition is met.
5. **Continue** when every Continue minimum is met but the Strong row is not complete.
6. **Adjust** when its explicit trigger appears or when a test with at least 100 visits produces mixed signals that do
   not satisfy another row.

After issue #45, calculate the seven-day return estimate from the eligible campaign cohort: distinct bot-filtered,
non-operator visitors whose first observed qualifying visit is at least seven full days before the test ends. The
numerator is eligible visitors who return on a different UTC day within seven days of that first visit; the denominator
is all eligible first-observed visitors. Use only the documented privacy-preserving visitor key and never join it to
waitlist contacts.

If fewer than 100 qualified visits can be observed, the result is **distribution-inconclusive**. Improve access to the
same ICP before making a product decision. Pause promotion immediately, regardless of counts, if data is stale, public
readiness fails, waitlist behavior is uncertain, a privacy/support request is unresolved, or a current-value post cannot
be verified.

## Ready-To-Use Assets

All current-value examples must be filled from a same-day verified report. Never schedule a post with a previously
captured risk value as if it were current.

### X Posts: English

**Current state**

> Bitcoin's modelled risk for [report date] is [risk value] — [risk band]. The useful part isn't the number alone: the
> brief shows how the score changed and the hypothetical price levels associated with another risk band. Data: [ready/fresh
> status]. Methodology [version]. Scenario levels are model estimates, not predictions. Research context, not financial
> advice. [campaign link]

**Scenario ladder**

> A Bitcoin risk score without context is hard to use. Bitcoin Risk Brief starts with today's modelled state, then shows
> the hypothetical price scenarios associated with lower and higher risk bands. They are model scenarios, not price
> predictions. [campaign link]

**Methodology**

> What is inside the Bitcoin Risk Brief score? Trend deviation versus a 365-day EMA, a 30-day volatility regime, and
> turnover when valid market-cap data is available. Robust rolling normalization, fixed weights, public version. The
> limits matter too. Research context, not a trade signal. [campaign link]

**Founder learning**

> I'm testing a simpler daily Bitcoin workflow: one risk state, current model-input directions, the score change, visible
> data freshness, and a scenario ladder. If you review BTC weekly rather than trade intraday, try it on two different
> days and tell me what still needs explanation. It is analytics, not a trading recommendation. [campaign link]

### Short Social Posts: Russian

**Current state**

> Модельный риск Bitcoin на [report date]: [risk value], диапазон [risk band]. В отчёте есть изменение сигнала и
> гипотетические цены перехода в другой диапазон. Статус данных: [ready/fresh status]. Методология [version]. Уровни
> — сценарии модели, а не прогноз цены. Это аналитический контекст, не финансовый совет. [campaign link]

**Scenario ladder**

> Одного числа риска мало. Bitcoin Risk Brief показывает текущий модельный диапазон и гипотетические цены для более
> низкого или высокого риска. Это сценарии модели, а не прогноз цены. [campaign link]

**Founder learning**

> Тестирую простой ежедневный формат для долгосрочных держателей BTC: один диапазон риска, изменение сигнала, свежесть
> данных и ценовые сценарии. Это аналитика, не торговый сигнал. Откройте отчёт в два разных дня и скажите, что осталось
> непонятным. [campaign link]

### Community Post: English

> Disclosure: I am building Bitcoin Risk Brief. It is a small pilot for long-horizon BTC holders who want one daily risk
> context rather than another chart terminal. It shows the current modelled risk band, data freshness, a short brief,
> and hypothetical price levels for other bands. It does not predict price or tell you what to buy or sell. If promotion
> is welcome here, I would value feedback from people willing to open it on two different days: [campaign link]

### Community Post: Russian

> Дисклеймер: я создаю Bitcoin Risk Brief. Это небольшой пилот для долгосрочных держателей BTC, которым нужен один
> ежедневный контекст риска вместо ещё одного терминала с десятками графиков. Сервис показывает текущий модельный
> диапазон риска, свежесть данных, краткое объяснение и гипотетические цены для других диапазонов. Это не прогноз цены и
> не совет покупать или продавать. Если публикации проектов здесь разрешены, буду благодарен за обратную связь после
> двух посещений в разные дни: [campaign link]

### Founder Outreach: English

> I built a small daily Bitcoin risk brief for people who review BTC weekly or monthly. It shows one modelled risk state,
> how the score changed, whether the data is fresh, and what price scenarios would move the model into another band.
> Would you be willing to open it on two different days and tell me the one thing that is unclear or missing? It is
> research context, not a trading recommendation, and there is no need to sign up:
> [campaign link]

Optional single follow-up after the person agrees:

> Thanks for looking. Did the brief save you any synthesis time, and would a notification only when the risk band changes
> be useful? A short yes/no plus why is enough.

### Founder Outreach: Russian

> Я сделал короткий ежедневный отчёт о модельном риске Bitcoin для тех, кто проверяет BTC раз в неделю или месяц. В нём
> один диапазон риска, направления факторов модели, изменение оценки, свежесть данных и ценовые сценарии перехода в
> другой диапазон. Сможешь открыть его в два разных дня и сказать, что осталось непонятным или чего не хватило? Это
> аналитический контекст, не торговая рекомендация. Регистрироваться необязательно:
> [campaign link]

Optional single follow-up after the person agrees:

> Спасибо! Сэкономил ли отчёт время на сбор контекста и было бы полезно уведомление только при смене диапазона риска?
> Достаточно короткого «да/нет» и причины.

### Weekly Digest Template

```text
Subject: Bitcoin Risk Brief — week ending [week-ending date]

Report date: [report date]
Current modelled risk: [risk value] — [risk band]
Latest covered date: [latest covered date]
Data status: [ready/fresh status]
Methodology: [methodology version]

What changed this week:
- [verified current model-driver direction]
- [verified risk-band or score change]

Scenario context:
- [lower target risk]: [hypothetical model price]
- [higher target risk]: [hypothetical model price]

What this means:
[two factual sentences that describe the model output without predicting price or prescribing action]

Open the brief: [campaign link]

Bitcoin Risk Brief is analytics and research context, not financial or investment advice. Scenario levels are
hypothetical model estimates, not predictions.
```

This is a copy template only. Recurring email or Telegram delivery remains gated by opt-in, sender ownership,
unsubscribe/stop handling, support, privacy, and recovery requirements.

### Weekly Digest Template: Russian

```text
Тема: Bitcoin Risk Brief — неделя по [week-ending date]

Дата отчёта: [report date]
Текущий модельный риск: [risk value] — [risk band]
Последняя дата данных: [latest covered date]
Статус данных: [ready/fresh status]
Методология: [methodology version]

Что изменилось за неделю:
- [verified current model-driver direction]
- [verified risk-band or score change]

Сценарный контекст:
- [lower target risk]: [hypothetical model price]
- [higher target risk]: [hypothetical model price]

Как это интерпретировать:
[two factual Russian sentences that describe the model output without predicting price or prescribing action]

Открыть отчёт: [campaign link]

Bitcoin Risk Brief — аналитический контекст, а не финансовый или инвестиционный совет. Сценарные уровни —
гипотетические оценки модели, а не прогнозы.
```

The same recurring-delivery gates apply to this Russian copy template.

### Short Methodology Explainer Outline

1. **What the number is:** a deterministic `0.0` to `1.0` modelled-risk value, mapped to low, neutral, and high bands.
2. **Model price:** HLC3 from the completed daily candle, not a live spot quote.
3. **Inputs:** trend deviation versus EMA365, 30-day volatility regime, and turnover when valid market-cap data exists.
4. **Normalization:** 1,460-day robust rolling z-scores with a 365-day minimum and clipped extremes.
5. **Weights:** published fixed weights for the turnover-enabled and turnover-disabled cases.
6. **Scenario ladder:** hypothetical prices solved while non-price components are held fixed for the latest day.
7. **Limits:** a model can omit relevant information; output quality depends on input data and methodology assumptions;
   nothing in the score predicts returns or determines a suitable action.

Use [Risk Methodology](../product/risk-methodology.md) as the source of truth. Issue
[#42](https://github.com/akarazhev/bitcoin-risk-brief/issues/42) tracks a more accessible public interpretation guide.

### Paid-Intent Question

Ask only after the person has used the brief and understands that alerts and paid access are not live:

> If a risk-band-change alert and a weekly context summary reliably saved you review time, would you consider joining a
> founding pilot at EUR 9-19 per month? What would need to be true for your answer to be yes?

Russian:

> Если уведомление о смене диапазона риска и еженедельный контекст действительно экономили бы вам время, рассмотрели бы
> вы участие в пилоте для первых пользователей за EUR 9-19 в месяц? Какие условия должны быть выполнены, чтобы ваш ответ
> был «да»?

Record only `yes`, `probably`, `not now`, or `no`, plus a sanitized reason theme. Do not collect payment or promise a
launch date. Payment, tax, cancellation, entitlement, support, and recurring-delivery gates must be completed first.

## Current-Value Publishing Checklist

Before a post includes a risk value, band, covered date, model price, or scenario level:

- verify `/api/readiness` is ready and fresh;
- verify the report date is the latest completed UTC day expected by operations;
- copy the value from the same verified report, not an old draft or screenshot;
- label model price and scenario levels accurately;
- include report date, readiness state, freshness state, and methodology version in the published asset;
- state that scenarios are hypothetical and the output is not financial or investment advice;
- avoid `buy`, `sell`, `cheap`, `expensive`, `bottom`, `top`, `safe`, `guaranteed`, or return language;
- cancel the post if readiness or freshness changes before publication.

## Promotion Rules

Always:

- disclose the founder relationship in communities;
- follow channel and community promotion rules;
- answer methodology and limitation questions directly;
- separate current product behavior from planned alerts, analytics, or payments;
- preserve timestamps and context for any current model value;
- ask for feedback that can falsify the hypothesis, not testimonials alone.

Never:

- present the score as financial advice, investment advice, a trade signal, or a price forecast;
- claim audited accuracy, superior returns, adoption, customer outcomes, or product-market fit without evidence;
- manufacture scarcity, urgency, social proof, or endorsements;
- target vulnerable users or imply that the product reduces the risk of leverage;
- scrape contacts, send unsolicited bulk messages, or evade community moderation;
- publish raw contacts, private messages, IP addresses, analytics exports, dashboard links, or support identities;
- buy ads during the four-week pilot; direct evidence is more valuable than scaled low-context traffic at this stage.

## Operator Workflow

### Before A Traffic Window

1. Run the public readiness checks from the Pilot Learning Loop.
2. Select one audience, one message, one source, and one content tag.
3. Prepare the post from an approved asset and complete the current-value checklist if applicable.
4. Record the start time and campaign labels in an operator-controlled log outside Git.
5. Confirm that support, deletion, and privacy requests can be handled manually.

### After A Traffic Window

1. Record the best available bot-filtered aggregate visit count and its limitation.
2. Record only aggregate new leads, source/locale/contact-type totals when safely available, and upsert count.
3. Summarize feedback as themes and counts; never paste private messages.
4. Record confirmed repeat-use and paid-intent categories without identities.
5. During Weeks 0-3, record `progress-only` or `pause`; after Week 4, choose `strong`, `continue`, `adjust`, `pause`,
   `stop current combination`, or `distribution-inconclusive`.
6. Set the next review date or trigger.

### Sanitized Weekly Record

```text
Week: [cycle number and date range]
Audience/message/source/content: [controlled campaign labels]
Readiness: [ready/fresh status, latest covered date, methodology version]
Qualified visits: [count and measurement limitation]
New leads: [count]
Visit-to-lead conversion: [rate or unavailable]
Confirmed repeat users: [count or privacy-preserving estimate]
Feedback conversations: [count]
Top themes: [theme and count]
Paid intent: [yes/probably/not now/no counts]
Safety or support issues: [sanitized count/status]
Decision: [progress-only/pause during Weeks 0-3; strong/continue/adjust/pause/stop current
combination/distribution-inconclusive after Week 4]
Next test: [one controlled change]
```

Keep the working record outside Git. Add only a final sanitized summary to repository evidence when it changes a gate,
roadmap decision, or launch boundary.

## Dependencies And Follow-Up

| Issue | Why it matters to this playbook | Current handling |
| --- | --- | --- |
| [#41](https://github.com/akarazhev/bitcoin-risk-brief/issues/41) | Make the daily brief explain material changes with concrete model context. | Collect repeated explanation gaps; do not invent drivers in campaign copy. |
| [#42](https://github.com/akarazhev/bitcoin-risk-brief/issues/42) | Publish a public methodology and interpretation guide. | Link the current methodology and use the short outline above. |
| [#43](https://github.com/akarazhev/bitcoin-risk-brief/issues/43) | Reframe the waitlist as an explicit risk-band alert demand test. | Treat current leads as a weaker proxy and ask alert interest directly. |
| [#44](https://github.com/akarazhev/bitcoin-risk-brief/issues/44) | Document the focused go-to-market test and campaign asset kit. | Implemented by this playbook after local verification; keep the issue open until the commit is pushed and reviewed. |
| [#45](https://github.com/akarazhev/bitcoin-risk-brief/issues/45) | Add privacy-preserving attribution and repeat-use analytics. | Report measurement limitations; never reconstruct users from raw infrastructure data. |

After four weeks, choose the smallest next move:

- **Strong:** prepare the alert-specific pilot and complete its trust/operations gates.
- **Continue:** run one more four-week cycle with one controlled message or audience change.
- **Adjust:** resolve the repeated clarity or trust problem before acquiring more traffic.
- **Stop current combination:** archive the message/channel pairing and interview the few engaged users before building.
- **Distribution-inconclusive:** improve qualified reach to the same ICP; do not label the product hypothesis disproven.
- **Pause:** resolve readiness, freshness, privacy, support, or data-correction risk before any further promotion.

Do not broaden into a general crypto dashboard, new wrapper, automated notification system, or paid product based only on
traffic. Recurring use and explicit demand should earn the next implementation step.
