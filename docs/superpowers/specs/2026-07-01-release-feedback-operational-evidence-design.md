# Release Feedback And Operational Evidence

> Status: future-facing. Last reviewed 2026-07-01. This is a Phase 8 launch-completeness add-on, not a new product
> phase.

## Context

The roadmap now covers the major production-pilot risks: data refresh, caching, deployment, backups, governance,
privacy, waitlist handling, localization, portfolio documentation, agent/API demand tests, and later methodology
research.

The remaining gaps are smaller but still useful before the project is shown to real users or as a professional
portfolio project. They are mostly about evidence, communication, and decision memory:

- how first-user questions and feedback are captured;
- how release notes, product decisions, and methodology changes are recorded;
- how support or deletion requests reach the operator;
- how dependency licenses are reviewed;
- how launch, backup, and restore evidence is preserved.

## Goal

Add a lightweight release and feedback checklist to Phase 8 so the product can move from "technically deployed" to
"operationally explainable" without creating a large new implementation track.

## Non-Goals

- Do not build a public support portal.
- Do not add a public status page for the first traffic test unless active users require it.
- Do not add a full ticketing system, CRM, or interview database.
- Do not redesign analytics or waitlist storage.
- Do not create an open-source compliance program while the repository remains private or portfolio-oriented.

## Recommended Approach

Use one small Phase 8 checklist with five parts:

1. Release and decision log.
2. First-user feedback loop.
3. Support and contact identity.
4. Dependency license review.
5. Launch and operations evidence.

This is better than a new phase because these items are launch hygiene. They should support the first public test and
the final documentation pass, not delay the product behind process work.

## Release And Decision Log

Before active traffic, create a short project decision log or changelog entry that records:

- launch commit and public hostname;
- methodology version shipped at launch;
- supported data refresh path;
- known accepted limitations;
- important product decisions, such as daily-only risk calculation, no 1h/4h risk metric, Fear & Greed as context rather
  than core input, open-data-first methodology research, and agent/API demand testing before building paid
  infrastructure.

The log does not need a formal format at first. A dated section in the final documentation pass is enough if it is easy
to scan and update.

## First-User Feedback Loop

Phase 8 should define how first traffic is reviewed after the initial test window:

- waitlist conversion;
- repeat visits or returning-user estimate;
- direct questions from users;
- requests for alerts, daily briefs, API access, agent usage, embeddings, widgets, or commercial reuse;
- confusion around methodology, price labels, no-advice framing, freshness, or risk states.

Feedback should be summarized into decisions for Phase 9. Raw waitlist contacts should not be copied into general
feedback notes unless there is a clear operational reason.

## Support And Contact Identity

Before broader exposure, define one operator-owned contact path for:

- waitlist deletion or unsubscribe requests;
- product questions;
- bug reports;
- professional/API/license interest.

For the first traffic test this can be a simple email address or controlled direct-contact channel. It does not need a
public help center or service-level promise.

## Dependency License Review

Data-source terms are covered elsewhere. This checklist adds a lightweight dependency-license pass for the private or
portfolio repository:

- review Python and npm production dependencies for obvious license conflicts;
- record whether the repository is private/proprietary, unlicensed, or later intended for public release;
- avoid claiming open-source status unless a license is intentionally chosen;
- keep third-party attribution notes aligned with the portfolio README if the repository is shown externally.

This review should be evidence-based but lightweight. It should not block the production pilot unless a dependency
license clearly conflicts with the intended use.

## Launch And Operations Evidence

The launch snapshot should become a small evidence packet rather than a memory of commands that were run. Capture:

- git commit;
- public hostname;
- latest BTC data date and CSV tail date;
- readiness payload;
- cache headers for a standard public endpoint;
- waitlist smoke result without exposing the contact value;
- browser/device QA result;
- selected data refresh path;
- selected deployment path;
- last successful backup date;
- last restore drill date and outcome;
- known accepted limitations.

Evidence can live in the production-readiness notes, an operations log, or the final documentation pass. The important
part is that the operator can later answer what was launched, with which data, and what was verified.

## Error Handling

If a checklist item cannot be completed before the first traffic test, record it as an accepted limitation with an owner
and a review date. Do not silently omit it.

For example:

- no public status page: accepted for first traffic because the product has no paid users;
- no full dependency-license report: accepted if the repo is private and production dependencies have no obvious
  conflicts;
- no restore drill evidence: not accepted for broader traffic, because backup confidence is part of Phase 7 readiness.

## Testing And Verification

This checklist is verified by documentation and operational evidence:

- roadmap names the release/feedback/evidence checklist in Phase 8;
- production readiness includes the checklist in pre-launch gates;
- final documentation pass can reference the decision log and launch evidence;
- first-traffic review can convert feedback into Phase 9 decisions without exposing private contacts.

## Acceptance Criteria

- Phase 8 includes release notes, decision memory, first-user feedback, contact path, dependency-license review, and
  launch/restore evidence.
- The work remains a small launch-completeness add-on, not a new product phase.
- No public support, SLA, status page, CRM, or open-source compliance commitment is implied before demand exists.
- The operator can explain what version launched, what data it used, what was verified, and what feedback was received.
