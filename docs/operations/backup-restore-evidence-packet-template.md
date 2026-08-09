# Backup Restore Evidence Packet Template

> **Operational log.** These entries record what was verified and when. They are not claims about product capability.

This template helps operators collect sanitized backup, off-server copy, backup freshness, scheduler, alert, and restore
drill evidence for Bitcoin Risk Brief before launch status is updated.

This file is a template, not completed evidence. It does not prove that a production backup, off-server copy, recurring
schedule, freshness monitor, alert route, or restore drill exists. Do not treat example wording as operational evidence
or as a reason to mark a launch gate passed.

## Purpose And Safety Rules

Use this packet to prepare backup and restore evidence before updating [Production Readiness](production-readiness.md)
or a final launch snapshot. The packet should show what was backed up, whether copied backups are fresh and verified,
whether recurring checks and alerts exist, and whether a safe restore drill target was used, without committing private
operational details to Git.

Safety rules:

- Do not invent backup, scheduler, off-server-copy, alert, or restore-drill evidence.
- Fill a copy of this template in an operator-controlled location outside Git first.
- Review the completed copy for forbidden private data before anything is copied into the repository.
- Copy only sanitized final evidence summaries into launch docs.
- Record only statuses, UTC timestamps, timestamp basenames, artifact categories, checksum/freshness outcomes, runner or
  alert-system categories, restore target type, readiness result, and accepted limitations.
- For backup artifacts, record only sanitized categories and timestamp basenames, not full paths.
- Keep private operational details outside Git.
- Do not record private paths, raw backup contents, raw dump contents, raw CSV rows, raw manifests, raw checksum files,
  dashboard URLs, account IDs, tokens, `.env` values, operator names, recipient addresses, contact details, waitlist
  contacts, screenshots with private data, or secret locations.
- Live-production restore testing must not be recommended or performed for launch evidence. Use only a staging project
  or an intentionally empty restore target that is not serving live production traffic.
- Keep status language conservative when evidence is incomplete.
- Do not change the backup/restore gate to `passed` unless real sanitized backup run, off-server copy,
  freshness/checksum, recurring schedule, alert delivery, and safe restore target evidence exist, or missing coverage is
  explicitly recorded as an accepted limitation.
- Do not use this template as launch evidence by itself.

## How To Use This Packet

1. Copy this template into an operator-controlled location outside Git.
2. Fill the copy with real backup, off-server copy, freshness, scheduler, alert, and restore-drill evidence.
3. Replace examples with actual sanitized outcomes, or leave the area `pending` or `blocked`.
4. Review the completed copy for forbidden private data.
5. Copy only final sanitized evidence summaries into [Production Readiness](production-readiness.md), the launch snapshot,
   or another launch evidence note.
6. Keep raw backups, raw logs, full paths, account details, contact details, dashboard URLs, screenshots with private
   data, and other private artifacts outside Git.

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
cannot be collected without missing production host access, scheduler access, off-server storage access, alert-system
configuration, or a safe restore target.

## Backup Run Identity And Production Context

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Backup run UTC time.
- Backup timestamp basename.
- Production commit or deployment revision.
- Backup trigger type: manual operator command, pre-deploy backup-gated update, scheduled job, or restore-preparation
  run.
- Production context category: production host command, backup-gated production update, or production scheduler/runner.
- Artifact categories expected for the run.
- Whether the run completed with exit code 0.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Backup run completed at 2026-07-12T01:20:00Z for timestamp basename 20260712T012000Z. Trigger type:
  scheduled production backup. Expected categories: PostgreSQL dump, canonical BTC CSV, manifest, and checksum file.
  Backup command exited 0.`
- `Status: partial. A one-time backup-gated update produced timestamp basename 20260711T190355Z, but no recurring
  schedule evidence is recorded.`
- `Status: blocked. No production-host backup run evidence is available in this packet.`

Do not record:

- Private backup roots, production project paths, hostnames tied to private infrastructure, raw command logs, operator
  names, account IDs, tokens, `.env` values, service account names, raw backup contents, dashboard URLs, screenshots with
  private data, or contact details.

## PostgreSQL Dump Evidence

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Backup timestamp basename.
- PostgreSQL dump artifact category presence.
- Non-empty artifact result.
- Dump command exit result.
- Checksum coverage status for the dump category.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Timestamp basename 20260712T012000Z includes a non-empty PostgreSQL dump category artifact. The dump
  command exited 0 and the checksum file covered the dump category.`
- `Status: partial. A dump artifact category is present, but checksum coverage has not been verified.`
- `Status: pending. PostgreSQL dump evidence has not been collected.`

Do not record:

- Full dump paths, raw dump contents, database connection strings, database passwords, private container paths, raw
  command logs, account IDs, service account names, tokens, `.env` values, private hostnames, or screenshots with private
  data.

## Canonical BTC CSV Backup Evidence

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Backup timestamp basename.
- Canonical BTC CSV artifact category presence.
- Non-empty artifact result.
- Covered date range or row count, if safely summarized.
- Checksum coverage status for the CSV category.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Timestamp basename 20260712T012000Z includes a non-empty canonical BTC CSV backup category artifact.
  The sanitized row count and covered end date match the expected production import evidence, and checksum coverage
  includes the CSV category.`
- `Status: partial. The BTC CSV backup category exists, but the row count/date-range summary is not recorded.`
- `Status: blocked. No canonical BTC CSV backup artifact evidence is available.`

Do not record:

- Full CSV paths, raw CSV rows, private staged-source paths, raw source snapshots, raw manifests, raw command logs,
  account IDs, API keys, source-provider account details, `.env` values, or screenshots with private data.

## Manifest And Checksum Evidence

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Backup timestamp basename.
- Manifest category presence.
- Checksum file category presence.
- Checksum verification result.
- Required artifact categories covered: PostgreSQL dump, canonical BTC CSV copy, and manifest.
- Checksum tool category: `sha256sum` or `shasum -a 256`.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Timestamp basename 20260712T012000Z includes manifest and checksum file categories. Checksum
  verification passed with SHA-256 tooling, and the checksum file covered PostgreSQL dump, BTC CSV, and manifest
  categories.`
- `Status: partial. Manifest and checksum categories exist, but verification output has not been recorded.`
- `Status: blocked. No manifest or checksum evidence is available.`

Do not record:

- Raw manifest contents, raw checksum files, full artifact paths, private storage paths, raw command logs, account IDs,
  tokens, `.env` values, operator names, private hostnames, or screenshots with private data.

## Off-Server Copy Evidence

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Backup timestamp basename.
- Off-server copy requirement.
- Off-server storage category: mounted removable media, mounted remote storage, operator-controlled archive, or other
  sanitized category.
- Matching timestamp basename result.
- Required artifact categories present under the copied backup.
- Off-server checksum verification result.
- Copy UTC time or latest copied-check UTC time.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Off-server storage category: mounted operator-controlled archive. Matching timestamp basename
  20260712T012000Z was present. PostgreSQL dump, BTC CSV, manifest, and checksum categories were present in the copied
  backup, and checksum verification passed for the copy.`
- `Status: partial. A copied backup exists for timestamp basename 20260711T190355Z, but recurring copy evidence is not
  recorded.`
- `Status: pending. The operator has not copied the backup off-server yet.`

Do not record:

- Off-server paths, private storage dashboard URLs, removable-media labels if private, account IDs, bucket names if
  private, tokens, `.env` values, raw backup contents, raw manifests, raw checksum files, raw command logs, operator
  names, contact details, or screenshots with private data.

## Backup Freshness Checker Result

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Checker command category: `scripts/check_backup_freshness.py`.
- Runner type: production host command, production cron, external scheduler, synthetic runner, or operator command.
- Freshness window.
- Backup timestamp basename.
- Latest check UTC time.
- Local backup check result.
- Off-server copy check result, if required.
- Checksum verification result.
- Exit result.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Runner type: production cron. Freshness window: 30 hours. Latest check passed at
  2026-07-12T02:00:00Z for timestamp basename 20260712T012000Z. Local backup and off-server copy were valid and fresh;
  checksum verification passed; exit result 0.`
- `Status: partial. A one-time checker pass exists for timestamp basename 20260711T190355Z, but no recurring runner or
  alert delivery is recorded.`
- `Status: blocked. No current production backup freshness checker result is available.`

Do not record:

- Full checker commands with private roots, private backup paths, private off-server paths, raw command logs, raw
  checksum output, raw backup contents, account IDs, tokens, `.env` values, private runner paths, private scheduler URLs,
  operator names, recipient details, or screenshots with private data.

## Recurring Scheduler Evidence

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Scheduler type: production cron, system timer, external scheduler, synthetic runner, or other sanitized category.
- Sanitized job/check name.
- Backup run cadence.
- Off-server copy cadence.
- Freshness checker cadence.
- Latest scheduled run UTC time.
- Latest scheduled run result.
- Failure behavior summary.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Scheduler type: production cron. Sanitized job name: backup and off-server copy. Cadence: daily after
  the UTC data window. Latest scheduled run passed at 2026-07-12T02:00:00Z, including backup creation, off-server copy,
  and freshness checker execution. Failures alert through the selected alert route.`
- `Status: partial. The backup command has a schedule, but off-server copy and freshness checker scheduling are not
  recorded.`
- `Status: pending. The operator has not chosen the backup schedule.`

Do not record:

- Private scheduler URLs, private job IDs, private host paths, raw cron files if they contain private data, service
  account names, account IDs, tokens, `.env` values, raw logs, operator names, recipient details, or screenshots with
  private data.

## Backup Freshness Alert Evidence

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Alert system type.
- Sanitized alert/check name.
- Freshness window.
- Failure conditions covered.
- Latest alert-rule evaluation UTC time.
- Latest alert-rule evaluation result.
- Alert route type.
- Alert-delivery test UTC time.
- Alert-delivery result.
- Sanitized evidence date.

Required failure coverage:

- Missing backup.
- Stale backup.
- Malformed timestamp basename.
- Missing PostgreSQL dump, BTC CSV, manifest, or checksum category.
- Checksum verification failure.
- Missing off-server copy when required.
- Scheduler or runner failure.

Acceptable sanitized wording examples:

- `Status: passed. Alert system type: external monitor. Sanitized alert name: backup freshness and off-server copy.
  Freshness window: 30 hours. Covered failures: missing, stale, malformed, checksum-invalid, missing off-server copy, and
  runner failure. Latest evaluation passed at 2026-07-12T02:05:00Z. Delivery test delivered to operator channel type.`
- `Status: partial. Backup freshness checker passes, but no alert-delivery test is recorded.`
- `Status: blocked. No alert-system or delivery evidence is available.`

Do not record:

- Recipient addresses, emails, handles, phone numbers, private contacts, webhook URLs, private channel IDs, provider
  dashboard URLs, account IDs, monitor IDs if private, tokens, raw notification payloads, raw logs, raw backup contents,
  `.env` values, operator names, or screenshots with private messages.

## Restore Drill Target And Result

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Live-production restore testing must not be recommended or performed for launch evidence. Use only a staging project or
an intentionally empty restore target that is not serving live production traffic. If no safe target exists, leave the
restore drill `pending`, `blocked`, or `accepted limitation`; do not test against the live production database.

Required sanitized fields:

- Status.
- Restore target type: staging project or intentionally empty restore target.
- Confirmation that the target was not serving live production traffic.
- Backup timestamp basename used.
- Restored artifact categories: PostgreSQL dump and canonical BTC CSV.
- Checksum verification before restore.
- Restore command exit result.
- Post-restore readiness result.
- Post-restore data date or row count, if safely summarized.
- Cleanup or teardown status for the target.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: passed. Restore target type: staging project. The target was not serving live production traffic. Timestamp
  basename 20260712T012000Z was checksum-verified before restore. PostgreSQL dump and BTC CSV categories restored,
  restore commands exited 0, and post-restore readiness returned ready with the expected sanitized date summary.`
- `Status: accepted limitation. No staging project or intentionally empty restore target exists for this pilot window, so
  the operator accepts the restore drill as deferred. Live-production restore testing was not attempted.`
- `Status: blocked. Restore drill cannot run because no safe restore target exists.`

Do not record:

- Live production database paths, private restore target paths, private hostnames, raw dump contents, raw CSV rows,
  database credentials, `.env` values, raw restore logs, account IDs, tokens, operator names, contact details, or
  screenshots with private data.

## Accepted Limitations Or Deferred Restore Status

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Required sanitized fields:

- Status.
- Named limitation or deferred area.
- Reason the limitation is accepted for the operator-watched pilot, if accepted.
- Evidence that still exists despite the limitation.
- Exact missing coverage.
- Required follow-up before broader public launch.
- Sanitized evidence date.

Acceptable sanitized wording examples:

- `Status: accepted limitation. Restore drill is deferred because no staging or intentionally empty restore target exists.
  Existing evidence covers one checksum-verified copied backup timestamp basename, but no safe restore target result.
  Follow-up: provision a safe restore target and record post-restore readiness before broader launch.`
- `Status: partial. Backup run and off-server copy evidence exist, but recurring scheduler and alert delivery remain
  pending.`
- `Status: blocked. No operator decision is available for accepting the missing restore target evidence.`

Do not record:

- Operator names, private decision records, private contact details, account IDs, dashboard URLs, private paths, raw
  logs, raw backup contents, raw restore output, tokens, `.env` values, or screenshots with private data.

## Ready To Record?

The backup/restore gate can be marked `passed` only when backup run, off-server copy, freshness/checksum, recurring
schedule, alert delivery, and safe restore target evidence exist, or when missing coverage is explicitly accepted as a
limitation. If any required area remains without real evidence or an accepted limitation, keep the gate `partial`,
`pending`, or `blocked`.

Before copying final evidence into [Production Readiness](production-readiness.md), verify:

- Each evidence area uses one allowed status value.
- Every `passed` status is backed by real sanitized evidence, not example wording.
- Every `accepted limitation` names the missing coverage and why it is acceptable for the operator-watched pilot.
- Every `partial`, `pending`, or `blocked` status keeps the launch gate partial/blocked.
- Backup run identity evidence includes the run UTC time, timestamp basename, production revision, trigger type, expected
  artifact categories, and exit result.
- PostgreSQL dump evidence records only the dump category, timestamp basename, non-empty result, exit result, and
  checksum coverage.
- Canonical BTC CSV backup evidence records only the CSV category, timestamp basename, non-empty result, sanitized date
  or row summary, and checksum coverage.
- Manifest and checksum evidence proves required categories are covered and checksum verification passed.
- Off-server copy evidence proves the matching timestamp basename and required categories exist under the copied backup,
  or records a specific accepted limitation.
- Backup freshness checker evidence summarizes `scripts/check_backup_freshness.py` without private roots, raw logs, raw
  checksum files, or raw backup contents.
- Recurring scheduler evidence proves backup, off-server copy, and freshness-check cadence, or records a specific
  accepted limitation.
- Backup freshness alert evidence proves alert-rule coverage and delivery-test result, or records a specific accepted
  limitation.
- Restore drill evidence uses only a staging project or intentionally empty restore target and confirms live production
  was not used.
- The final repository note contains no private paths, raw backup contents, raw logs, dashboard URLs, account IDs,
  tokens, `.env` values, operator names, contact details, waitlist contacts, or secret locations.
