# Distribution Channel Research Design

> Status: future-facing. Last reviewed 2026-07-01. This is a post-launch distribution research track and does not block
> the production-pilot gate.

## Goal

Evaluate whether Bitcoin Risk Brief should be packaged for additional distribution channels after the public web product
has enough usage evidence to justify channel-specific work.

The goal is not to publish everywhere. The goal is to find the cheapest channels that improve discovery, repeat use, and
paid-intent signals for the single BTC risk product.

## Roadmap Placement

This belongs after Phase 9 as Distribution Channel Research.

It can run independently of Risk Methodology Research. Methodology research asks whether the risk metric should improve.
Distribution research asks whether the existing product should be made easier to discover and revisit in specific
platforms.

## Channel Priority

### 1. PWA And Installable Web App

This is the first distribution candidate.

Reasons:

- the product is already web-first;
- PWA installability is the smallest packaging step;
- it can improve repeat visits without store review;
- it preserves the current backend, API, and public URL;
- it creates a foundation for later notification and shortcut experiments.

The first PWA pass should focus on installability, icons, manifest quality, mobile polish, and source tracking. Push
notifications should remain a later alerts experiment, not part of the first PWA packaging step.

### 2. Telegram Mini App

This is the first social-platform candidate.

Reasons:

- Telegram is a natural channel for crypto audiences;
- Telegram Mini Apps are JavaScript web apps launched inside Telegram;
- Telegram supports direct Mini App launch patterns, home-screen shortcuts, and monetization primitives such as
  subscriptions through Telegram Stars;
- the current product can be adapted as a compact risk surface without creating a new data backend.

The first Telegram experiment should be a thin wrapper around the current risk page or a compact Telegram-specific
landing screen that links to the full product. It should track `source=telegram_mini_app` waitlist leads and repeat
opens.

### 3. Browser Extensions

Browser extension stores are later candidates and should only be pursued when there is a clear utility use case.

Good extension use cases:

- current BTC risk badge in the toolbar;
- popup with latest risk, freshness, and next threshold prices;
- quick link to the full public page;
- opt-in local alert threshold, if alerts become a validated demand signal.

Avoid publishing a browser extension that only opens the website. Chrome Web Store, Edge Add-ons, and Firefox Add-ons
all add packaging, review, privacy, and maintenance overhead. That overhead is only justified if the extension gives
users a small daily utility the website alone does not provide.

### 4. VK Mini Apps

VK Mini Apps are a conditional RU/CIS distribution candidate.

They may fit if waitlist or traffic evidence shows a strong Russian-speaking audience that wants an in-platform app.
This path requires platform-specific review, localization, source tracking, and a Russian-language go-to-market plan.

### 5. WeChat Mini Programs

WeChat Mini Programs are not a near-term fit.

They may be relevant only if the product intentionally targets China or a WeChat-native partner channel. This path is a
separate compliance, localization, platform, and distribution project, not a quick wrapper around the current web app.

### 6. Discord Activities

Discord Activities are a weak fit for the current product.

Discord positions Activities as iframe-hosted web apps for multiplayer games and social experiences. A BTC risk page is
not naturally multiplayer or chat-native. Discord should only be revisited if the product develops a community workflow,
such as shared watchlists, group risk briefings, or creator-led community sessions.

## Experiment Rules

- Do not build more than one new channel at a time.
- Start with the cheapest channel that reuses the current public web product.
- Each channel must have an explicit `source` value for waitlist and analytics attribution.
- Each channel must preserve readiness/freshness display and the no-financial-advice framing.
- Each channel must pass the same mobile layout, API error, and degraded-readiness checks as the public web page.
- Channel-specific authentication, payments, or notifications require a separate design before implementation.

## Demand Signals

Valid demand signals are:

- installs or repeat opens from a channel;
- waitlist leads with channel-specific source values such as `source=pwa`, `source=telegram_mini_app`, or
  `source=browser_extension`;
- users asking for alerts, notification delivery, widgets, or daily brief delivery in that channel;
- conversion from channel users into direct feedback, paid beta interest, or API/integration requests.

Raw impressions, store listing views, or one-time opens are not enough by themselves.

## Monetization Path

Distribution channels are retention and discovery surfaces, not the monetization model.

Potential monetized capabilities remain:

- daily or weekly brief delivery;
- risk-level alerts;
- Telegram or email notifications;
- paid API or agent access;
- premium historical context;
- embeddable creator or analyst widgets.

Telegram may later support channel-native paid experiments through Telegram Stars, but that should follow validated demand
for alerts or recurring briefs.

## Non-Goals

This phase does not include:

- launching all channels at once;
- building native iOS or Android apps;
- building platform-specific auth before demand is proven;
- adding payments before a paid feature is validated;
- adding Discord Activities without a social or multiplayer use case;
- targeting WeChat without a China-specific go-to-market reason;
- publishing browser extensions that only act as website launchers.

## Deliverables

- A channel scorecard comparing PWA, Telegram Mini App, browser extensions, VK Mini Apps, WeChat Mini Programs, and
  Discord Activities.
- A recommendation for the first channel experiment.
- Tracking source names and success metrics for that channel.
- A short implementation design for the chosen channel before any code changes.

## Acceptance Criteria

- PWA is evaluated before higher-overhead platform wrappers.
- Telegram Mini App is the first social-platform candidate unless channel data points elsewhere.
- Browser extensions are pursued only with a real daily utility use case.
- VK, WeChat, and Discord remain conditional until audience or partner evidence justifies them.
- No channel-specific work compromises the public web product, readiness checks, cache behavior, or no-advice positioning.
