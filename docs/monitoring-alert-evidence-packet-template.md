# Monitoring Alert Evidence Packet Template

This template helps operators collect sanitized monitoring and alert proof for Bitcoin Risk Brief before the launch
status is updated.

This file is a template, not completed evidence. It does not prove that any external monitor, scheduler, Cloudflare
notification, backup monitor, or alert-delivery route exists. Do not treat example wording as provider evidence or as a
reason to mark a launch gate passed.

## Purpose And Safety Rules

Use this packet to prepare monitoring and alert evidence before updating the monitoring/alert gate in
[Production Readiness](production-readiness.md). The packet should show what was configured, what it asserts, and
whether alerts were delivered without committing private operational details to Git.

Safety rules:

- Do not invent monitor, provider, scheduler, Cloudflare, backup, or alert-delivery evidence.
- Fill a copy of this template in an operator-controlled location outside Git first.
- Review the completed copy for forbidden private data before anything is copied into the repository.
- Copy only sanitized final evidence summaries into launch docs.
- Record only status, public endpoint paths, provider or runner type, sanitized check names, intervals/windows, assertion
  summaries, timestamp basenames, pass/fail outcomes, and accepted limitations.
- Keep private operational details outside Git.
- Do not record provider dashboard URLs, account IDs, monitor IDs if private, tokens, recipient addresses, emails, phone
  numbers, handles, private contacts, private paths, raw logs, raw backup contents, `.env` values, raw waitlist contacts,
  or secret locations.
- Keep status language conservative when evidence is incomplete.
- Do not change the monitoring/alert gate to `passed` unless real sanitized provider/scheduler evidence and
  alert-delivery evidence exist, or the missing coverage is explicitly recorded as an accepted limitation.
- Do not use this template as launch evidence by itself.

## How To Use This Packet

1. Copy this template into an operator-controlled location outside Git.
2. Fill the copy with real provider, scheduler, Cloudflare, backup, and alert-delivery evidence.
3. Replace examples with actual sanitized outcomes, or leave the area `pending` or `blocked`.
4. Review the completed copy for forbidden private data.
5. Copy only final sanitized evidence summaries into [Production Readiness](production-readiness.md) or a launch snapshot
   note.
6. Keep provider screenshots, dashboard URLs, account details, raw logs, recipient lists, private paths, raw backup
   contents, and other private artifacts outside Git.

## Status Values

Each evidence area must use one of these exact status values:

- `passed`
- `accepted limitation`
- `partial`
- `pending`
- `blocked`

Use `passed` only when the required evidence is real, current, and sanitized. Use `accepted limitation` only when the
operator deliberately accepts a named gap for an operator-watched pilot. Use `partial` when some required evidence exists
but coverage is incomplete. Use `pending` when the evidence has not been collected. Use `blocked` when the evidence
cannot be collected without missing external access, provider configuration, scheduler access, or operator action.

## Public Endpoint Probe Evidence

Use `scripts/check_public_endpoints.py` for local cron jobs, synthetic monitor runners, or external provider script steps
that need a concise public endpoint assertion:

```bash
python3 scripts/check_public_endpoints.py \
  --base-url https://bitcoinriskbrief.minihub.app \
  --max-data-age-days 2 \
  --require-cache-header Cache-Control \
  --require-cache-header ETag \
  --require-cache-header X-Cache-Version \
  --require-cache-header X-Cache
```

The probe intentionally requires a freshness policy through `--max-data-age-days`, `--expected-latest-date`, or both. It
checks `GET /api/health`, `GET /api/readiness`, and `GET /api/risk/latest`. It exits 0 only when the requested
assertions pass and prints concise sanitized status instead of raw response dumps.

Summarize probe evidence with:

- Status.
- Runner type: local operator command, cron job, synthetic runner, or external provider script step.
- Public hostname and endpoint paths.
- Freshness policy used.
- Cache-header requirements used, if any.
- UTC run time.
- Exit result.
- Sanitized assertion summary, such as latest date, readiness state, latest-risk date match, risk value rounded for
  readability, and cache-header presence.
- Whether alert delivery was tied to this probe.

Do not paste raw command logs, raw JSON payloads, full response headers, private runner paths, private scheduler URLs,
monitor IDs if private, tokens, recipient addresses, account IDs, dashboard URLs, or private contacts.

Local or scheduled probe evidence supports public endpoint assertions. It does not replace external provider/dashboard
proof unless the operator explicitly chooses a scheduled probe as the monitor and records that choice, schedule,
assertions, failure behavior, and alert delivery as real evidence.

## Backup Freshness Evidence

Use `scripts/check_backup_freshness.py` to summarize backup freshness and off-server-copy status without storing raw
backup paths or backup contents:

```bash
python3 scripts/check_backup_freshness.py \
  --backup-root ./backups \
  --off-server-root "<mounted-off-server-backup-root>" \
  --max-age-hours 30
```

For cron or a monitoring wrapper, the same values can come from environment variables:

```bash
BACKUP_DIR=./backups \
OFFSERVER_BACKUP_ROOT="<mounted-off-server-backup-root>" \
BACKUP_FRESHNESS_MAX_AGE_HOURS=30 \
python3 scripts/check_backup_freshness.py
```

Summarize backup freshness evidence with:

- Status.
- Runner type: production host cron, external scheduler, synthetic runner, or operator command.
- Freshness window.
- Backup timestamp basename.
- Required artifact category result: PostgreSQL dump, canonical BTC CSV copy, manifest, and checksum file.
- Checksum verification result.
- Off-server copy check result, if required.
- UTC check time.
- Alert rule status and delivery-test status.

Do not record private backup roots, off-server paths, raw dump contents, raw CSV contents, raw manifests, raw checksum
files, raw command logs, storage dashboard URLs, account IDs, token names, token values, recipient addresses, phone
numbers, handles, private contacts, or `.env` values.

Backup freshness evidence is not complete alert evidence until a real scheduler or monitor runs it on the chosen
production/off-server roots and alert delivery has been tested or the missing coverage is explicitly accepted as a
limitation.

## Public API Health Monitor

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Provider or runner type.
- Sanitized monitor/check name.
- Public endpoint path.
- Interval, timeout, and failure threshold.
- Latest check UTC time.
- Latest check result.
- Alert route type.
- Alert-delivery evidence status.
- Sanitized evidence date.

Required assertion coverage:

- `GET /api/health` returns HTTP 200.
- Response JSON includes `status: ok`.
- TLS failure, timeout, DNS failure, and HTTP non-200 results alert.
- The monitor checks the public hostname, not only the private origin.

Acceptable sanitized wording examples:

- `Status: passed. Provider type: external uptime monitor. Check name: public API health. Endpoint: /api/health.
  Interval: 1 minute. Latest check passed at 2026-07-12T01:10:00Z with HTTP 200 and status ok. Alert route type:
  operator channel. Delivery test passed separately.`
- `Status: partial. Local scheduled probe validates /api/health, but no external provider dashboard evidence or delivery
  test is recorded.`
- `Status: blocked. No provider or scheduler evidence is available for the health monitor.`

Do not record:

- Provider dashboard URLs, account IDs, private monitor IDs, tokens, recipient addresses, emails, handles, phone numbers,
  private contacts, IP allowlists, private runner paths, raw logs, raw response dumps, or `.env` values.

## Public API Readiness/Freshness Monitor

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Provider or runner type.
- Sanitized monitor/check name.
- Public endpoint path.
- Freshness policy: maximum data age, expected latest date, or both.
- Interval, timeout, and failure threshold.
- Latest check UTC time.
- Latest readiness date and sanitized freshness result.
- Alert route type.
- Alert-delivery evidence status.
- Sanitized evidence date.

Required assertion coverage:

- `GET /api/readiness` returns HTTP 200.
- Response JSON includes `status: ready`.
- Required readiness checks are true, including `checks.data_fresh` when present.
- `latest_date` or `covered_end` satisfies the chosen freshness policy.
- Readiness date matches the latest-risk date when the monitor also checks `/api/risk/latest`.
- Required cache headers are present when cache-header assertions are part of the launch gate.
- HTTP 503, stale data, missing fields, malformed JSON, timeout, and HTTP non-200 results alert.

Acceptable sanitized wording examples:

- `Status: passed. Provider type: external synthetic monitor. Check name: public readiness freshness. Endpoint:
  /api/readiness. Policy: max data age 2 UTC days. Latest check passed at 2026-07-12T01:12:00Z with status ready,
  data_fresh true, latest_date within policy, and required cache headers present. Delivery test passed separately.`
- `Status: accepted limitation. The selected provider cannot assert nested JSON, so a scheduled
  scripts/check_public_endpoints.py probe supplies JSON freshness assertions and the provider alerts on runner failure.`
- `Status: pending. Freshness policy is chosen, but no scheduled run or provider assertion evidence is recorded.`

Do not record:

- Raw readiness payloads, full response headers, provider dashboard URLs, account IDs, private monitor IDs, tokens,
  recipient addresses, emails, handles, phone numbers, private contacts, private runner paths, raw logs, raw backup
  paths, raw waitlist contacts, or `.env` values.

## Public API Latest-Risk Monitor

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Provider or runner type.
- Sanitized monitor/check name.
- Public endpoint path.
- Freshness policy or readiness-date-match policy.
- Interval, timeout, and failure threshold.
- Latest check UTC time.
- Latest-risk date, rounded risk value, and sanitized risk state.
- Alert route type.
- Alert-delivery evidence status.
- Sanitized evidence date.

Required assertion coverage:

- `GET /api/risk/latest` returns HTTP 200.
- Response JSON is parseable.
- Timestamp date is present and matches readiness `latest_date` or `covered_end` when checked with readiness.
- Risk value is numeric and inside the expected 0 to 1 range.
- Risk state is present.
- Required cache headers are present when cache-header assertions are part of the launch gate.
- Missing timestamp, stale date, date mismatch, malformed JSON, nonnumeric risk, timeout, and HTTP non-200 results alert.

Acceptable sanitized wording examples:

- `Status: passed. Provider type: external synthetic monitor. Check name: public latest risk. Endpoint:
  /api/risk/latest. Latest check passed at 2026-07-12T01:14:00Z with latest-risk date matching readiness, risk 0.26,
  state low, and required cache headers present. Delivery test passed separately.`
- `Status: partial. Local public probe validates latest-risk date and range, but no provider or scheduler alert evidence
  is recorded.`
- `Status: blocked. No latest-risk monitor evidence is available.`

Do not record:

- Raw latest-risk payloads, full response headers, provider dashboard URLs, account IDs, private monitor IDs, tokens,
  recipient addresses, emails, handles, phone numbers, private contacts, private runner paths, raw logs, raw waitlist
  contacts, or `.env` values.

## Stale-Data Alert After The Nightly Update Window

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Provider, scheduler, or alert-rule type.
- Sanitized alert/check name.
- Nightly update window and grace period.
- Freshness policy.
- Public endpoint or local validation source used.
- Latest scheduled evaluation UTC time.
- Latest scheduled evaluation result.
- Alert route type.
- Alert-delivery evidence status.
- Sanitized evidence date.

Required assertion coverage:

- The alert evaluates after the nightly collector window plus the operator-defined grace period.
- It alerts when readiness is HTTP 503, `status` is not `ready`, or `checks.data_fresh` is not true.
- It alerts when `data_age_days` exceeds `max_age_days`.
- It alerts when `latest_date` or `covered_end` is older than the expected last completed UTC day.
- It distinguishes an endpoint outage from stale data where practical.

Acceptable sanitized wording examples:

- `Status: passed. Scheduler type: external synthetic runner. Alert name: stale data after nightly window. Policy:
  evaluate after the UTC nightly update window plus 90 minutes; max data age 2 UTC days. Latest scheduled evaluation
  passed at 2026-07-12T03:30:00Z. Delivery test passed separately.`
- `Status: partial. Freshness probe exists, but no after-window schedule or alert-delivery proof is recorded.`
- `Status: pending. Operator has not chosen the nightly window grace period.`

Do not record:

- Private scheduler URLs, private job IDs, provider dashboard URLs, account IDs, tokens, recipient addresses, emails,
  handles, phone numbers, private contacts, private runner paths, raw logs, raw response dumps, private hostnames, or
  `.env` values.

## Collector Failure Alert

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Alert source type: production logs, service supervisor, container health, scheduler, or external log alert.
- Sanitized alert/check name.
- Collector failure signals covered.
- Scheduled run evidence window.
- Latest evaluation UTC time.
- Latest evaluation result.
- Alert route type.
- Alert-delivery evidence status.
- Sanitized evidence date.

Required assertion coverage:

- Alerts on `scheduled_refresh_failed`.
- Alerts on `public_cmc_download_failed`.
- Alerts on optional API fallback failure when that fallback is configured.
- Alerts on missed scheduled refresh evidence.
- Alerts on repeated `data-collector` restarts or unhealthy collector service state.
- Preserves the canonical CSV when a download or validation failure occurs.

Acceptable sanitized wording examples:

- `Status: passed. Alert source type: production scheduler and service monitor. Alert name: collector refresh failure.
  Covered signals: scheduled refresh failed, public download failed, optional API fallback failed when configured,
  missed scheduled run, and repeated collector restarts. Latest evaluation passed at 2026-07-12T02:20:00Z. Delivery test
  passed separately.`
- `Status: partial. Collector logs are available to operators, but no log-alert rule or delivery test is recorded.`
- `Status: blocked. This workstation has no production host or log-alert evidence.`

Do not record:

- Raw collector logs, private host paths, private scheduler URLs, provider dashboard URLs, account IDs, service account
  names, tokens, recipient addresses, emails, handles, phone numbers, private contacts, raw CSV rows, `.env` values, or
  private source-provider account details.

## Backup Freshness/Off-Server-Copy Alert

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Provider, scheduler, or runner type.
- Sanitized alert/check name.
- Freshness window.
- Required backup artifact categories.
- Off-server copy requirement.
- Latest backup timestamp basename.
- Latest check UTC time.
- Latest check result.
- Alert route type.
- Alert-delivery evidence status.
- Sanitized evidence date.

Required assertion coverage:

- A checksum-verified backup exists inside the chosen freshness window.
- Required artifact categories are present: PostgreSQL dump, canonical BTC CSV copy, manifest, and checksum file.
- Checksum verification passed for the selected timestamp basename.
- The same timestamp basename exists under the off-server root when off-server copy is required.
- Missing, stale, malformed, checksum-invalid, or missing off-server copy results alert.

Acceptable sanitized wording examples:

- `Status: passed. Runner type: production cron with external alert wrapper. Check name: backup freshness and off-server
  copy. Freshness window: 30 hours. Latest timestamp basename: 20260712T012000Z. PostgreSQL dump, BTC CSV, manifest, and
  checksum categories were present; checksum verification passed locally and for the off-server copy. Delivery test
  passed separately.`
- `Status: partial. A one-time copied/off-server checker pass exists, but no recurring schedule or delivery test is
  recorded.`
- `Status: blocked. No production backup scheduler or off-server monitor evidence is available.`

Do not record:

- Private backup roots, off-server paths, raw dump contents, raw CSV contents, raw manifests, raw checksum files, storage
  dashboard URLs, account IDs, tokens, recipient addresses, emails, handles, phone numbers, private contacts, raw logs,
  database connection strings, or `.env` values.

## Cloudflare Tunnel Connector Health Notification

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Cloudflare notification status or accepted limitation.
- Sanitized tunnel/service category.
- Production connector management type: host service or compose-managed service.
- Connector health signals covered.
- Latest notification configuration check UTC time.
- Latest connector status, if available.
- Alert route type.
- Alert-delivery evidence status.
- Sanitized evidence date.

Required assertion coverage:

- Connector-down notification is enabled or the missing notification is explicitly accepted as a limitation.
- Flapping or repeated disconnect behavior is covered when available on the active plan.
- The notification applies to the tunnel serving the public hostname.
- Public endpoint health is not treated as proof that connector-down notifications exist.
- Alert delivery is tested through the chosen route or missing delivery is explicitly accepted as a limitation.

Acceptable sanitized wording examples:

- `Status: passed. Cloudflare connector health notification is enabled for the production tunnel category serving the
  public hostname. Production connector type: host-service cloudflared. Covered signals: connector down and repeated
  disconnects where supported. Latest configuration check passed at 2026-07-12T01:30:00Z. Delivery test passed
  separately.`
- `Status: accepted limitation. Public endpoints are healthy, but connector-down notifications are not available on the
  current setup; the operator accepts this only for an operator-watched pilot.`
- `Status: blocked. No Cloudflare dashboard/API evidence is available.`

Do not record:

- Cloudflare dashboard URLs, account IDs, zone IDs, tunnel IDs, connector IDs, token names, token values, recipient
  addresses, emails, handles, phone numbers, private contacts, private hostnames, connector names tied to private
  infrastructure, raw event logs, screenshots with private data, or `.env` values.

## Alert Delivery Test

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Provider or alert system type.
- Channel type only.
- Sanitized test name.
- Test trigger source.
- Test UTC time.
- Delivered/not-delivered result.
- Monitor or alert rules covered by the test.
- Retry/escalation behavior summary, if configured.
- Sanitized evidence date.

Required assertion coverage:

- A real test notification was sent through the chosen monitoring or alert system.
- The notification was delivered to the intended channel type or delivery failure was recorded.
- The delivery route covers the monitors and alert rules listed in this packet, or any exceptions are named.
- The test does not expose recipient identifiers in repository notes.
- Failed or untested delivery keeps the monitoring/alert gate `partial`, `pending`, or `blocked` unless explicitly
  accepted as a limitation.

Acceptable sanitized wording examples:

- `Status: passed. Provider type: external monitoring provider. Channel type: operator chat channel. Test source:
  provider test notification. Test time: 2026-07-12T01:40:00Z. Result: delivered. Covered rules: health, readiness,
  latest risk, stale data, collector failure, backup freshness, and Cloudflare connector health.`
- `Status: partial. A delivery channel is selected, but no provider test notification has been sent.`
- `Status: blocked. No alert channel or provider test evidence is available.`

Do not record:

- Recipient addresses, emails, handles, phone numbers, names, private contacts, private chat URLs, webhook URLs, tokens,
  provider dashboard URLs, account IDs, private channel IDs, screenshots with private messages, raw notification payloads,
  raw logs, or `.env` values.

## Ready To Record?

The monitoring/alert gate can be marked `passed` only when provider/scheduler evidence and alert-delivery evidence exist
for the required coverage, or when missing coverage is explicitly accepted as a limitation. If any required area remains
without real evidence or an accepted limitation, keep the gate `partial`, `pending`, or `blocked`.

Before copying final evidence into [Production Readiness](production-readiness.md), verify:

- Each evidence area uses one allowed status value.
- Every `passed` status is backed by real sanitized provider, scheduler, Cloudflare, backup, or alert-delivery evidence.
- Every `accepted limitation` names the missing coverage and why it is acceptable for the operator-watched pilot.
- Every `partial`, `pending`, or `blocked` status keeps the launch gate partial/blocked.
- Public API health monitor evidence covers HTTP 200, JSON `status: ok`, timeout, TLS failure, and HTTP non-200 alerting.
- Public API readiness/freshness evidence covers HTTP 200, `status: ready`, data freshness, freshness policy, and
  failure alerting.
- Public API latest-risk evidence covers HTTP 200, parseable JSON, timestamp/date match, numeric risk range, risk state,
  and failure alerting.
- Stale-data alert evidence proves the after-window schedule or records a specific accepted limitation.
- Collector failure alert evidence covers scheduled refresh failure, public download failure, optional API fallback
  failure when configured, missed scheduled runs, and repeated collector restarts.
- Backup freshness/off-server-copy alert evidence covers the chosen freshness window, checksum verification, required
  artifact categories, off-server copy status, and alerting.
- Cloudflare Tunnel connector health notification evidence covers connector-down notification status or a specific
  accepted limitation.
- Alert delivery test evidence proves a real delivered test through the chosen channel type, or records a specific
  accepted limitation.
- `scripts/check_public_endpoints.py` evidence is summarized without raw logs, raw payloads, raw headers, or private
  runner details.
- `scripts/check_backup_freshness.py` evidence is summarized without raw backup paths, raw backup contents, raw checksum
  files, or private storage details.
- The final repository note contains no provider dashboard URLs, account IDs, private monitor IDs, tokens, recipient
  addresses, emails, phone numbers, handles, private contacts, private paths, raw logs, raw backup contents, `.env`
  values, raw waitlist contacts, or secret locations.
