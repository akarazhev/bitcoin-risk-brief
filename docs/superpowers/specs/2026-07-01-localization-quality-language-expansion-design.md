# Localization Quality And Language Expansion Design

> Status: superseded in scope by GitHub issue #28 as of 2026-07-13. The earlier recommendation deferred Arabic and
> Chinese; issue #28 accepts the larger scope and requires Chinese, German, French, Spanish, and Arabic support.

## Goal

Improve trust and reach before active traffic by polishing the existing English and Russian copy, preparing the frontend
for more than two locales, and adding Spanish and German as the first additional languages.

The goal is not broad internationalization. The goal is a focused launch-ready localization pass for the same single BTC
risk product.

## Roadmap Placement

This belongs in Phase 8: Launch Checklist And First Traffic Test.

It should happen before active traffic if time allows, because language quality affects trust, waitlist conversion, and
how clearly users understand the no-advice framing. This historical design kept Arabic, Chinese, country-specific
compliance, and platform localization outside its Phase 8 gate; GitHub issue #28 supersedes that scope for Arabic and
Simplified Chinese while still leaving country-specific compliance and platform localization outside this issue.

## Current Constraints

The current application is not yet structured for many languages:

- frontend copy is embedded directly in `frontend/src/App.tsx`;
- frontend locale types are limited to `en` and `ru`;
- waitlist locale handling and API types currently accept only `en` and `ru`;
- brief payload types expose only English and Russian sections;
- tests cover locale behavior only at the existing two-language level.

Adding more languages without an i18n foundation would make the main app file harder to maintain and would increase the
chance of broken copy, clipped text, and inconsistent waitlist attribution.

## Recommended Scope

Use a balanced scope before active traffic:

1. Polish existing English and Russian copy.
2. Extract UI copy into a dedicated translation structure or module.
3. Extend supported locales to English, Russian, Spanish, and German.
4. Add Spanish and German UI copy for the public product surface.
5. Keep backend-generated brief text compatible with the enabled locale set or provide an explicit fallback until
   localized brief generation is designed.
6. Track locale in waitlist submissions and product analytics using the enabled locale value.
7. Add QA coverage for all enabled locales on desktop and mobile.

## Language Priority

Pre-traffic scope:

- English: polish for clarity, trust, no-advice framing, and concise product value.
- Russian: polish for consistency with the English intent and clearer product copy.
- Spanish: first added language because it is left-to-right and has broad web reach.
- German: second added language because it is left-to-right and useful for higher-intent European audiences.

Deferred scope:

GitHub issue #28 intentionally promotes Arabic and Chinese into implementation scope. Arabic must include RTL QA, and
Chinese is implemented as Simplified Chinese under locale code `zh`.

- Arabic: valuable later, but requires right-to-left layout support, `dir="rtl"`, chart/form QA, and mixed BTC/USD text
  checks.
- Chinese: valuable later, but requires Simplified vs Traditional scope, China-specific distribution/compliance thinking,
  and likely WeChat-related channel research.

Reference inputs:

- W3Techs reported Spanish and German as two of the largest non-English content languages on 2026-07-01:
  https://w3techs.com/technologies/overview/content_language
- MDN documents `dir` for right-to-left languages such as Arabic:
  https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/dir
- W3C internationalization guidance covers structural markup for right-to-left text:
  https://www.w3.org/International/questions/qa-html-dir

## Copy Polish Requirements

The copy pass should improve:

- hero subtitle and product value statement;
- readiness and freshness labels;
- methodology summary;
- no-financial-advice disclaimer;
- threshold and risk-state explanations;
- waitlist call to action;
- loading, empty, degraded, and API-error states.

Copy should stay concise. It must not imply prediction certainty, buy/sell instructions, or personalized financial advice.

## Technical Requirements

Implementation should preserve the current product shape:

- no broad dashboard;
- no account system;
- no country-specific offers;
- no billing or paid localization scope;
- no new backend API solely for localization.

Expected technical changes when implemented:

- define a locale registry that includes label, text direction, and enabled state;
- move frontend UI strings out of the main app component;
- update locale switching from a two-state toggle to a compact selector that can handle four locales;
- update frontend types and tests for the enabled locale set;
- update waitlist locale validation only when the backend is ready to store the new locale values;
- preserve fallback behavior if a localized brief section is unavailable.

## QA Requirements

Before active traffic, verify every enabled locale across:

- desktop and mobile layouts;
- long text wrapping in buttons, badges, panels, and waitlist states;
- loading, empty, degraded readiness, and API-error states;
- risk history and risk levels charts;
- waitlist submission and locale attribution;
- methodology/disclaimer copy;
- no overlapping UI at target viewport widths.

Under GitHub issue #28, Arabic and Chinese are enabled in the product scope. Arabic requires documented right-to-left
layout checks, waitlist locale attribution, and readable chart data, USD prices, percentages, and ISO dates. Chinese is
implemented as Simplified Chinese under locale code `zh`.

## Non-Goals

This design does not include:

- country-specific compliance localization;
- platform-specific localization for channels such as Telegram Mini Apps or browser extensions;
- machine-translating all docs;
- translating operational docs;
- country-specific legal or investment disclaimers;
- localized paid offers;
- SEO landing pages for every language;
- user accounts or language preferences stored server-side.

## Success Criteria

This work is successful when:

- English and Russian launch copy is clearer and more trustworthy;
- Spanish, German, French, Simplified Chinese, and Arabic can be selected in the public UI;
- waitlist submissions can carry the selected enabled locale;
- all enabled locales pass mobile and desktop QA without clipped or overlapping text;
- no-advice and methodology framing remains consistent across locales;
- Arabic passes RTL checks while chart data, USD prices, percentages, and ISO dates remain readable.
