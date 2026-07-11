# Launch Snapshot Evidence Packet Template

This file is a template, not completed evidence. It does not prove that the final launch snapshot exists, that any launch
gate has passed, that first traffic is allowed, or that first traffic has run. Do not treat example wording as launch
evidence.

Use this packet to collect the final sanitized pre-traffic launch snapshot for Bitcoin Risk Brief. Fill a working copy
outside Git first in an operator-controlled evidence location. After review and redaction, copy only sanitized final
evidence summaries into launch docs such as [Production Readiness](production-readiness.md) or a final launch snapshot
note.

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

## Purpose And Safety Rules

Purpose:

- Collect the final pre-traffic launch state in one reviewable packet.
- Link already collected sanitized evidence without copying raw private artifacts into Git.
- Keep the launch status conservative when evidence is stale, partial, missing, or explicitly accepted as a limitation.
- Keep first traffic at `not_run` until all required gates are passed or explicitly accepted and the traffic window
  actually runs.

Safety rules:

- Do not invent launch evidence.
- Do not use this template as evidence by itself.
- Fill a copy outside Git first, then copy only sanitized final evidence into launch docs.
- Record only status values, UTC timestamps, commit hashes, public hostname facts, endpoint paths, evidence basenames,
  timestamp basenames, row/date summaries, rounded risk values, assertion summaries, and accepted limitations.
- Keep private operational details outside Git.
- Do not record private paths, raw logs, raw JSON payloads, raw response headers, raw source files, raw backup contents,
  raw waitlist contacts, dashboard URLs, account IDs, tokens, `.env` values, operator names, contact details, recipient
  details, screenshots with private data, private approval threads, or secret locations.
- Keep status language conservative when evidence is incomplete.
- Do not mark any launch blocker `passed` unless real sanitized evidence exists for that blocker.
- Do not run first traffic from this packet. First traffic is a separate operator action after the launch gates allow it.

## How To Use This Packet

1. Copy this template into an operator-controlled location outside Git.
2. Replace examples with actual sanitized outcomes, or leave sections `pending`, `partial`, or `blocked`.
3. Review the completed copy for forbidden private data.
4. Create or validate the sanitized JSON snapshot with `scripts/launch_snapshot_packet.py` when local evidence files are
   available.
5. Copy only final sanitized evidence summaries into [Production Readiness](production-readiness.md), the roadmap, or a
   launch evidence note.
6. Keep raw source archives, raw logs, raw backups, dashboard screenshots, account details, contact details, private
   paths, and other private artifacts outside Git.

## Snapshot Identity And Production Context

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Snapshot ID or packet basename.
- Snapshot created UTC time.
- Public hostname.
- Production commit or deployment revision.
- Deployment/update path category, without private paths.
- Production data-refresh mode expected for the launch window.
- Operator role or automation role, without personal details.
- Evidence archive category, without private paths.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: partial. Snapshot packet launch-snapshot-YYYYMMDDTHHMMSSZ.json was prepared for the public pilot hostname at
  production revision <commit>. Evidence archive category: operator-controlled launch archive.`
- `Deployment context: selected USB-based production update path; no private host path recorded.`
- `Status: pending. Snapshot identity is reserved, but final production revision evidence has not been recorded.`

Do not record:

- Private filesystem paths, SSH targets, hostnames that are not already public, operator names, emails, handles, phone
  numbers, account IDs, dashboard URLs, `.env` values, tokens, raw command transcripts, or private archive roots.

## Final Public Readiness/Freshness Recheck

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Recheck UTC time.
- Public hostname and endpoint paths checked.
- Freshness policy used.
- `/api/health` status summary.
- `/api/readiness` HTTP status, readiness state, latest date or covered end, data freshness result, row count, and
  methodology version when available.
- `/api/risk/latest` HTTP status, latest-risk date, rounded risk value, and risk state.
- Whether latest-risk date matches readiness coverage.
- Required cache/header summary for `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`.
- Evidence basenames for sanitized readiness/latest-risk captures, if stored outside Git.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Final public recheck at YYYY-MM-DDTHH:MM:SSZ returned health HTTP 200, readiness ready, data_fresh
  true, latest date YYYY-MM-DD, row count <count>, latest-risk date matched readiness, and required cache headers were
  present.`
- `Status: partial. Public readiness is fresh, but latest-risk cache-header evidence was not captured in the final
  window.`
- `Status: blocked. Readiness returned degraded or stale during the final pre-traffic window.`

Do not record:

- Raw JSON dumps, full response headers, cookies, client IP addresses, raw access logs, private runner paths, private
  hostnames, dashboard URLs, account IDs, tokens, `.env` values, or unrelated production records.

## Production Revision/Deployment Evidence

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Production revision or commit hash.
- Deployment/update evidence type.
- Service status summary.
- Origin health/readiness result after deployment or update.
- Public health/readiness result after deployment or update.
- Backup-gated mode result when a fresh pre-update backup was required.
- Production `.env` preservation status, summarized without values.
- Whether any deploy/update limitation is accepted for the first traffic window.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Production update evidence records revision <commit>, service restart success, origin readiness ready,
  public readiness ready, and backup-gated mode completed with exit result 0.`
- `Status: accepted limitation. Direct live checkout proof was unavailable; operator accepted deployment manifest
  revision plus public readiness evidence for the watched pilot.`
- `Status: pending. No current production revision evidence is recorded for the final launch window.`

Do not record:

- Private project paths, production `.env` values, server hostnames, SSH targets, service account names, raw logs,
  dashboard URLs, account IDs, tokens, private deployment manifests, screenshots with private data, or operator names.

## Operator Launch Decisions

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Operator decision packet basename or launch register reference.
- Waitlist owner/review/retention/deletion/unsubscribe status.
- Support/contact path status.
- Credential/account ownership and recovery record status.
- Data-source terms and attribution review status.
- Cloudflare first-traffic posture status.
- Accessibility launch posture status.
- Restore drill posture status.
- Named accepted limitations, if any.
- Sanitized decision date or evidence date.

Acceptable sanitized wording examples:

- `Status: partial. Waitlist handling and support/contact decisions are recorded; credential recovery and data-source
  terms remain pending operator decisions.`
- `Status: accepted limitation. The current Cloudflare Free-plan subset is accepted only for one operator-watched first
  traffic window.`
- `Status: pending. No sanitized operator decision packet has been copied into launch docs.`

Do not record:

- Operator names, personal contact details, actual email addresses, handles, phone numbers, private inboxes, private
  chat links, account holders, account IDs, dashboard URLs, recovery paths, secret locations, raw approval threads,
  source-provider private terms, tokens, or `.env` values.

## Production Import Provenance

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Import provenance packet basename or manifest ID.
- Import completion UTC time or scheduled window.
- Production revision linked to the import.
- Import mode: scheduled public download, one-off public download, manual downloaded CSV import, optional API fallback,
  restore, or correction.
- Source type and source snapshot basename.
- Source SHA-256, row count, covered range, and expected tail date.
- Canonical CSV output hash, row count, range, and tail date.
- Validation/readiness summary after import.
- Public cache/header summary after import.
- `scripts/import_provenance_packet.py` create/validate result or accepted manual-review limitation.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Import provenance packet import-YYYYMMDD.json links source basename source.csv, SHA-256 <64-hex>,
  canonical tail YYYY-MM-DD, validation ready, and public cache/header evidence for the same production import.`
- `Status: accepted limitation. Direct validation-table query was unavailable; operator accepted source archive,
  manifest validation, origin readiness, and public cache evidence for the watched pilot.`
- `Status: blocked. Source snapshot or canonical output evidence is missing, so import provenance cannot be marked
  passed.`

Do not record:

- Raw source files, raw CSV rows, raw import logs, full archive paths, browser download paths, database dumps, database
  connection strings, source-provider account details, API keys, dashboard URLs, account IDs, tokens, `.env` values,
  private host paths, or operator names.

## Backup/Off-Server Copy/Restore Posture

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Backup/restore packet basename or launch register reference.
- Backup run UTC time and timestamp basename.
- Production revision linked to the backup.
- Backup artifact category coverage: PostgreSQL dump, canonical BTC CSV, manifest, and checksum file.
- Local checksum verification result.
- Off-server copy category and matching timestamp basename result.
- Off-server checksum verification result.
- Backup freshness checker result and freshness window.
- Recurring scheduler status.
- Backup freshness alert and delivery-test status.
- Restore target type and restore drill result, or accepted deferred restore limitation.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: partial. Backup timestamp basename YYYYMMDDTHHMMSSZ is checksum-verified locally and off-server, but recurring
  scheduler and alert delivery remain pending.`
- `Status: accepted limitation. Restore drill is deferred because no staging project or intentionally empty restore
  target exists; live-production restore testing was not attempted.`
- `Status: blocked. No current backup freshness or off-server copy evidence is available for the final window.`

Do not record:

- Private backup roots, off-server paths, raw backup contents, raw dump contents, raw CSV contents, raw manifests, raw
  checksum files, database credentials, private restore target paths, storage dashboard URLs, account IDs, tokens,
  recipient addresses, operator names, contact details, raw logs, screenshots with private data, or `.env` values.

## External Monitoring And Alert Delivery

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Monitoring/alert packet basename or launch register reference.
- Provider, scheduler, or runner type.
- Public API health monitor status.
- Public API readiness/freshness monitor status and freshness policy.
- Public API latest-risk monitor status.
- Stale-data alert status after the nightly update window.
- Collector failure alert status.
- Backup freshness/off-server-copy alert status.
- Cloudflare Tunnel connector health notification status.
- Alert route type.
- Alert-delivery test UTC time and delivered/not-delivered result.
- Accepted limitations, if any.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. External provider or scheduled runner evidence covers health, readiness/freshness, latest risk, stale
  data, collector failure, backup freshness, Cloudflare connector health, and alert delivery to the chosen channel type.`
- `Status: accepted limitation. The selected provider cannot assert nested JSON; a scheduled
  scripts/check_public_endpoints.py probe supplies JSON assertions and alerts on runner failure.`
- `Status: blocked. No provider, scheduler, Cloudflare notification, or alert-delivery evidence is available.`

Do not record:

- Provider dashboard URLs, account IDs, private monitor IDs, rule IDs, tokens, recipient addresses, emails, handles,
  phone numbers, private contacts, webhook URLs, raw notification payloads, private runner paths, scheduler URLs, raw
  logs, raw response dumps, Cloudflare zone/tunnel IDs, or `.env` values.

## Public-Host Privacy/Terms/Disclaimer And Metadata Smoke

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Smoke UTC time.
- Public hostname.
- Privacy/terms/disclaimer note presence result.
- No-financial-advice framing result.
- No-sensitive-information warning result.
- Waitlist storage/logging copy presence result.
- Metadata categories checked: title, description, canonical URL, Open Graph fields, and Twitter card fields.
- Image metadata status or accepted omission.
- Whether the smoke avoided waitlist POSTs.
- Sanitized evidence basenames, if any.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Public-host smoke found the privacy/disclaimer note, no-advice framing, no-sensitive-info warning,
  expected metadata fields, and no waitlist POSTs during the smoke.`
- `Status: accepted limitation. Social image metadata is intentionally omitted because no real public repo-served image
  asset exists.`
- `Status: pending. Public-host metadata smoke has not been rerun after the latest deployment.`

Do not record:

- Screenshots with private data, raw page dumps, raw logs, waitlist contacts, private browser profiles, account IDs,
  dashboard URLs, tokens, `.env` values, private contact details, or private approval notes.

## Browser/Device/Accessibility Smoke And Accepted Limitations

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Smoke UTC time.
- Browser/device profile categories checked.
- Public hostname or production-origin category checked.
- First-viewport latest-risk/readiness visibility result.
- Chart nonblank result.
- Locale toggle result.
- Mobile horizontal-overflow result.
- Waitlist UI state result without POSTing contacts unless an approved smoke contact is used.
- Accessibility evidence categories covered.
- Manual keyboard, screen-reader/assistive-tech, physical-device/native browser, and production-host accessibility
  statuses.
- Accepted limitations, if any.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: partial. Automated desktop/mobile browser smoke passed, charts were nonblank, locale toggle worked, and no
  horizontal overflow was observed; manual screen-reader and native physical-device evidence remain pending.`
- `Status: accepted limitation. Local automated axe, chart alternative, live-region, and keyboard/focus evidence are
  accepted for the operator-watched pilot; manual/native gaps remain follow-up items.`
- `Status: blocked. Public-host browser smoke has not been run for the final launch window.`

Do not record:

- Tester names, personal device identifiers, screenshots with private data, private browser profiles, raw assistive-tech
  logs, raw Playwright traces containing private data, waitlist contact values, account IDs, dashboard URLs, tokens,
  `.env` values, or private issue reports.

## Cloudflare Edge Posture And Accepted Limitations

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Cloudflare edge evidence date.
- Public hostname category.
- Active plan posture or sanitized capability category.
- WAF/bot challenge coverage summary.
- Waitlist rate-limit coverage summary.
- Public read cache-rule coverage summary.
- `/api/waitlist` cache-bypass coverage summary.
- Broader `/api/*` burst-rate-limit status.
- Managed WAF status.
- Operator decision: accept current subset for first traffic or require upgrade before first traffic.
- Smoke-test result for normal public page use and waitlist behavior.
- Accepted limitations, if any.

Acceptable sanitized wording examples:

- `Status: accepted limitation. Current Free-plan-compatible subset covers waitlist bot challenge, one waitlist
  rate-limit rule, waitlist cache bypass, and public-read cache rules for one operator-watched first-traffic window.`
- `Status: blocked. First traffic requires an upgrade or equivalent controls before the launch window.`
- `Status: pending. No operator decision has accepted the current edge subset or required an upgrade.`

Do not record:

- Cloudflare account IDs, zone IDs, tunnel IDs, rule IDs if private, dashboard URLs, API tokens, private screenshots,
  private event logs, internal IP addresses, connector names tied to private infrastructure, private routing details, or
  `.env` values.

## First Traffic Status

Default field value: `first_traffic_status: not_run`.

First traffic can run only after required launch gates are passed or explicitly accepted for an operator-watched first
traffic window. Until then, leave first traffic `not_run` and keep the launch status `pending`, `partial`, or `blocked`
as appropriate.

Allowed section status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Section status.
- `first_traffic_status`, defaulting to `not_run`.
- Whether the traffic window has run.
- Gate decision allowing or blocking first traffic.
- Operator watch status for the traffic window.
- Start/end UTC times only if the traffic window actually ran.
- Public source/channel category only if the traffic window actually ran.
- Sanitized demand summary only after the traffic window actually ran.
- Evidence basename only if explicit first-traffic evidence exists.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Section status: pending. first_traffic_status: not_run. First traffic has not run because final launch gates remain
  incomplete or not explicitly accepted.`
- `Section status: blocked. first_traffic_status: not_run. Final readiness was stale, so first traffic did not run.`
- `Section status: passed. first_traffic_status: passed. Operator-watched first traffic ran during the recorded UTC
  window after required gates were passed or explicitly accepted, with only aggregate sanitized demand summaries copied
  into launch docs.`

Do not record:

- Raw IP addresses, raw analytics exports, raw access logs, raw waitlist contacts, contact values, names, emails,
  handles, phone numbers, private source links, private campaign URLs, recipient details, dashboard URLs, account IDs,
  tokens, `.env` values, screenshots with private data, or private operator notes.

## Known Blockers Or Accepted Launch Limitations

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Blocker or limitation name.
- Affected launch gate.
- Exact missing evidence or unavailable action.
- Operator decision: pending, blocked, or accepted limitation.
- Reason the limitation does or does not block the operator-watched pilot.
- Follow-up condition before broader public launch.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: accepted limitation. Restore drill is deferred because no safe restore target exists. This is accepted only
  for the operator-watched pilot; follow-up is to provision a staging or intentionally empty restore target.`
- `Status: blocked. External alert delivery has not been tested, so broader first traffic remains blocked until a real
  delivery result or explicit accepted limitation is recorded.`
- `Status: pending. Data-source terms review outcome has not been recorded.`

Do not record:

- Private approval threads, operator names, personal contact details, legal advice, private source-provider
  correspondence, account recovery details, dashboard URLs, account IDs, private paths, raw logs, raw backups, raw
  waitlist contacts, tokens, or `.env` values.

## `scripts/launch_snapshot_packet.py` Validation Result

Allowed status values for this template section: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

The helper's JSON schema uses machine status values for evidence categories: `present`, `pending`,
`accepted_limitation`, and `blocked`. The helper's `first_traffic_status` values are `not_run` and `passed`. When
summarizing helper output in this template, use the launch-doc status values above and quote helper values only as helper
fields.

Required sanitized fields:

- Section status.
- Helper command category: `create`, `validate`, or manual review.
- Packet basename.
- Helper exit result.
- `launch_readiness_status` from helper output.
- `first_traffic_status` from helper output, expected to remain `not_run` before first traffic.
- `blocked_or_pending_gates` summary, sanitized and shortened.
- Evidence category statuses from the packet, using helper status values when needed.
- Accepted limitations recorded by the packet, if any.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. scripts/launch_snapshot_packet.py validate passed for launch-snapshot.json. Helper output reported
  launch_readiness_status=ready_for_operator_review and first_traffic_status=not_run.`
- `Status: partial. Helper validation passed, but blocked_or_pending_gates lists monitoring, import provenance, and
  backup freshness as pending or limited.`
- `Status: blocked. Helper validation failed because the packet contained an unsafe value or missing required field.`

Do not record:

- Full commands with private paths, raw JSON packets containing private values, private evidence paths, raw payloads,
  raw logs, account IDs, dashboard URLs, tokens, `.env` values, operator names, contact details, waitlist contacts,
  private hostnames, or screenshots with private data.

## Ready For First Traffic?

First traffic can proceed only when every required item below is true. If any item is missing and not explicitly
accepted as a limitation, keep `first_traffic_status: not_run`.

- [ ] Final public readiness is fresh in the final pre-traffic window.
- [ ] Operator launch decisions are recorded or explicitly accepted as limitations.
- [ ] Monitoring and alert evidence exists, or the missing coverage has an explicit accepted limitation.
- [ ] Production import provenance is recorded, or the missing coverage has an explicit accepted limitation.
- [ ] Backup/restore posture is recorded, or the missing coverage has an explicit accepted limitation.
- [ ] Public-host privacy/terms/disclaimer and metadata smoke is current, or any missing coverage has an explicit
      accepted limitation.
- [ ] Browser/device/accessibility smoke is current, or remaining limitations are explicit.
- [ ] Cloudflare edge posture is recorded, including any accepted Free-plan limitations or upgrade requirement.
- [ ] Known blockers are closed, downgraded by real evidence, or explicitly accepted for the operator-watched pilot.
- [ ] `scripts/launch_snapshot_packet.py` snapshot validation passes.
- [ ] The completed repository note contains no private paths, raw logs, dashboard URLs, account IDs, tokens, `.env`
      values, operator names, contact details, waitlist contacts, raw source files, or raw backup contents.
