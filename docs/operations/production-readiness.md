# Production Readiness

> **Operational log.** These entries record what was verified and when. They are not claims about product capability.

This document is the current production-pilot status and gate register for Bitcoin Risk Brief. Detailed dated evidence
has been moved to [Production Evidence Log](production-evidence-log.md); the archive preserves older proof summaries,
commit IDs, tags, dates, and historical blockers that may now be superseded.

## Current Status

Verified starting state for this docs synchronization pass: local `main`, `origin/main`, and tag
`first-traffic-pilot-evidence-2026-07-15` all pointed at
`a62216b13ec2e29382407fc8a8e962a23f62ca99` before this cleanup commit.

The public pilot hostname is `https://bitcoinriskbrief.minihub.app/`. The 2026-07-15 watched first-traffic observation
completed for a small operator-watched pilot, with `first_traffic_status=completed` for that run only. This is not a
broad public launch, paid launch, commercial-readiness claim, full WCAG/legal accessibility approval, broader monitoring
claim, or broader direct import provenance claim.

The final launch snapshot was created and validated outside Git before first traffic. The sanitized packet basename was
`launch-snapshot-20260715T121952Z.json`; local tag `final-launch-snapshot-evidence-2026-07-15` points at
`aa2ac6af8d1182e0a7eb63ea8e70f345bb86b86c`. The later first-traffic evidence is separate from that snapshot.

First-traffic public GET evidence recorded on 2026-07-15 showed:

- `GET /api/health` returned HTTP 200 with `status=ok`.
- `GET /api/readiness` returned HTTP 200 with `status=ready`, `latest_date=2026-07-14`, `covered_end=2026-07-14`,
  `data_age_days=1`, `max_age_days=2`, `source=coinmarketcap_csv`, `row_count=5846`,
  `methodology_version=crypto-scout-canonical-v1`, `data_fresh=true`, and `Cache-Control: no-store`.
- `GET /api/risk/latest` returned HTTP 200 for `2026-07-14T00:00:00+00:00`, risk `0.2694028326125623`,
  `risk_state=low`, `model_price_usd=64069.92364076667`, `low_usd=62207.522497`, and `high_usd=65046.1341991`, with
  cache/version headers present.
- The watched homepage observation loaded the public page, showed current risk `27%`, latest completed day
  `2026-07-14`, report date `2026-07-15`, readiness text, and two visible chart canvases.
- No production waitlist POST was performed or claimed during the first-traffic run.

The canonical local BTC CSV in this repository currently tails at `2026-07-14`. Local tag
`btc-csv-through-2026-07-14-evidence-2026-07-15` points at
`e204acc` (`data: update btc csv through 2026-07-14`). Repository CSV evidence supports the small-pilot snapshot but
does not, by itself, prove direct production source/archive provenance for broader launch.

## Current Gate Register

| Gate area | Current status | Current evidence | Remaining limitation or next action |
| --- | --- | --- | --- |
| Public first traffic | Completed for the small operator-watched pilot. | 2026-07-15 GET-only endpoint checks and browser observation; tag `first-traffic-pilot-evidence-2026-07-15` at `a62216b`. | Keep this scoped to the small pilot. Do not claim broad launch, paid launch, full accessibility/legal approval, broader monitoring completion, or broader provenance completion. |
| Final launch snapshot | Created and validated before first traffic. | Outside-Git packet basename `launch-snapshot-20260715T121952Z.json`; tag `final-launch-snapshot-evidence-2026-07-15` at `aa2ac6a`. | Preserve snapshot evidence separately from first-traffic evidence. Recheck public readiness/latest-risk for future pilot windows and after production updates. |
| Public freshness/latest risk | Current for the first-traffic window. | Public readiness/latest-risk evidence through `latest_date=2026-07-14`, `row_count=5846`, `risk_state=low`, and readiness `no-store`. | Freshness is time-sensitive; rerun GET-only checks during future pilot windows and after updates. |
| Waitlist smoke | Historical browser-like production smoke passed; first-traffic run did not POST. | 2026-07-08 browser-like smoke returned HTTP 201 with no-store/no-cache headers and aggregate-only storage verification. | Rerun only with an operator-approved test contact when a future launch/update snapshot needs fresh waitlist evidence. Keep raw contacts out of Git. |
| Support/contact and account recovery | Completed for first-traffic readiness. | 2026-07-12 sanitized support/contact and account recovery readiness evidence. | Keep exact addresses, account IDs, holders, recovery paths, private URLs, and provider details outside Git. |
| Backup/off-server copy | Completed for the current first-traffic evidence set. | 2026-07-15 copied backup timestamp basename `20260715T082457Z`; PostgreSQL dump, BTC CSV, manifest, and checksum categories present; copied-backup SHA-256 verification passed. | Recurring backup automation, recurring off-server copy, backup freshness monitoring, and backup alert delivery remain pending before broader launch or later operations. |
| Restore drill | Accepted limitation for the small pilot. | Current setup has only the live production server; no safe staging or intentionally empty restore target is recorded. | Run a restore drill only after a safe target exists. Do not test restores against live production. |
| Monitoring | Endpoint monitoring closed 2026-08-19; collector and backup alerting still pending. | 2026-07-14 sanitized acceptance for Cloudflare Tunnel Health Alert and homepage availability. 2026-08-19: ten external uptime monitors covering `/api/readiness`, `/api/health`, data freshness, the homepage, `/api/risk/latest`, `/api/risk/levels`, `/api/brief/latest`, and the agent surface on both origins, each asserting a response keyword as well as a status code; set checked in at [`uptime-monitors.csv`](uptime-monitors.csv) and explained in [Uptime monitoring](uptime-monitoring.md). Maintenance window, alert delivery test, and private alert routing confirmed by the operator. | Collector-failure alerts and backup freshness alerts remain pending before broader launch. Endpoint monitoring cannot see which stage of a collector run failed, a partially successful run, or delivery of the daily Telegram post. |
| Accessibility/browser QA | Completed for small-pilot manual/native plus proxy scope only. | 2026-07-15 manual/native browser QA passed for notebook/native desktop and mobile/native categories; 2026-07-15 local assistive-tech proxy QA passed. | No true VoiceOver, NVDA, TalkBack, switch-control, screen-magnifier, or manual assistive-tech pass was performed. Do not claim full WCAG/legal accessibility approval. |
| Direct production import provenance | Accepted limitation for small-pilot snapshot; broader direct proof pending. | Public readiness/latest-risk, row count, latest date, cache evidence, and BTC CSV evidence through `2026-07-14`. | Before broader launch or broader provenance claims, record direct source/archive provenance, retrieval/import timestamp, row count/range, readiness/latest-risk output, and checksum if available. |
| Data-source terms and commercial readiness | Accepted limitation only for unpaid/non-commercial pilot. | 2026-07-12 operator decision records founder/operator source-terms owner and unpaid/non-commercial pilot status. | Complete CoinMarketCap/source-terms review or paid-plan decision before commercial claims, paid beta, broader distribution, or legal/commercial readiness claims. |
| Dependency/license review | Partial local engineering evidence; scoped project licence recorded. | [Dependency and License Review](dependency-license-review.md) records Apache-2.0 for owned source code, documentation, and configuration, plus local npm lockfile metadata, Python manifest gaps, container references, CI references, and local Dependabot configuration. Third-party BTC/USD market data remains outside the project licence. | Confirm GitHub-hosted Dependabot execution/first PR evidence, Python/container/OS/CI license posture, vulnerability/advisory status, data-source terms, and legal compatibility before broader commercial claims. |
| Cloudflare edge posture | Accepted limitation for small operator-watched pilot only. | Current Free-plan-compatible subset is documented and accepted for the small pilot. | Managed WAF, broader `/api/*` burst limiting, multiple rate-limit rules, or equivalent controls remain deferred until broader traffic or observed abuse risk. |
| Post-traffic learning | Active next phase; feedback evidence not yet recorded here. | First traffic has completed; [Production Roadmap](production-roadmap.md) now treats Phase 9 as the active learning loop, with the operator runbook in [Pilot Learning Loop](pilot-learning-loop.md). | Record only sanitized aggregate waitlist/source/locale/repeat-use/request evidence and direct-question themes. Do not copy raw contacts, raw analytics, or private message text into Git. |

## Future Pilot Window Checklist

Before future pilot traffic windows, production updates, or a new public snapshot:

- Verify local repo state and intended production revision.
- Recheck public `GET /api/health`, `GET /api/readiness`, and `GET /api/risk/latest`.
- Confirm readiness still returns `Cache-Control: no-store` and latest-risk returns expected cache/version headers.
- Confirm the selected production refresh path and latest BTC CSV coverage are current for the window.
- Preserve or refresh backup/off-server evidence when a production update or data-change window requires it.
- Keep accepted limitations visible in any launch/update summary.
- Use the [Pilot Learning Loop](pilot-learning-loop.md) for post-traffic observation cadence, aggregate waitlist review,
  sanitized feedback summaries, and continue/adjust/pause/broaden decisions.
- Do not run production waitlist POSTs, deploys, data refresh/imports, Cloudflare changes, monitor changes, or backup
  operations unless the operator explicitly requests that production mutation.

## Broader-Launch Limitations

The following remain pending before broader public launch, broader readiness/freshness claims, paid/commercial launch, or
professional/commercial reuse:

- Collector-failure alerts and backup freshness alerts. Dedicated `/api/health` and `/api/readiness` monitoring,
  stale-data alerting, and sanitized alert delivery evidence were closed on 2026-08-19.
- Recurring backup automation, recurring off-server copy, production backup freshness monitoring, and backup alert
  delivery.
- Restore drill on a staging project or intentionally empty restore target.
- True manual screen-reader/assistive-tech pass and broader accessibility evidence; full WCAG/legal accessibility
  approval is not claimed.
- Direct production import provenance and source/archive proof for broader launch.
- Commercial/source-terms readiness, paid-plan decision, legal approval, dependency/license external confirmation, and
  third-party market-data redistribution review if paid or broader distribution happens.
- Any broader Cloudflare/WAF/API burst-rate-limit controls required by traffic or abuse risk beyond the current
  small-pilot accepted subset.

## Release Gates

For code, deployment, or operational changes, use the command set in [Operations](operations.md) and the relevant
behavior-specific docs. Documentation-only changes require targeted diff/read review; runtime tests are not required
unless application code or runtime configuration changes.

## Related Docs

- [Production Evidence Log](production-evidence-log.md)
- [Production Roadmap](production-roadmap.md)
- [Pilot Learning Loop](pilot-learning-loop.md)
- [Operations](operations.md)
- [Security and Privacy](../engineering/security-and-privacy.md)
- [Frontend QA](../engineering/frontend-qa.md)
- [Dependency and License Review](dependency-license-review.md)
