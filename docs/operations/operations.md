# Operations

> **Operational log.** These entries record what was verified and when. They are not claims about product capability.

## Local Environment

Create a local environment file:

```bash
cp .env.example .env
```

Validate compose:

```bash
./scripts/manage.sh validate
```

Start services:

```bash
./scripts/manage.sh start
```

Apply schema to an existing database:

```bash
./scripts/manage.sh migrate
```

For future schema changes beyond the current idempotent initial migration, use the API/DB change-management gate before
production deployment: add a new migration file, take a fresh backup, test migration on a fresh and existing database,
record rollback expectations, run smoke checks, and update API/security/operations docs when endpoint contracts,
retention, analytics, API client identity, or PII behavior changes.

Import the canonical CSV without network access:

```bash
./scripts/manage.sh backfill
```

Refresh from CoinMarketCap if configured, then import the full CSV:

```bash
./scripts/manage.sh run-now
```

If `COINMARKETCAP_API_KEY` is empty, `run-now` imports the existing canonical CSV and recomputes risk without remote
network refresh.

## Automatic Public CoinMarketCap CSV Refresh

Refresh BTC history without a paid CoinMarketCap API account:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
```

The command fetches the missing days after the canonical CSV tail from CoinMarketCap's public historical-data endpoint,
stages the result under `collector/btc-csv/incoming/`, validates the staged CSV, atomically updates
`collector/btc-csv/btc_usd_daily.csv`, and runs the normal database import, risk recomputation, validation write, brief
write, and stale-row cleanup.

If the public endpoint returns an incomplete range, an error response, HTML, or blocked content, the command fails before
rewriting the canonical CSV. Use the manual workflow below or the optional official API-key refresh path.

## Scheduled Public CoinMarketCap Refresh

The production-pilot scheduler is public-download-first: once per day after the UTC day closes, the `data-collector`
targets the last completed UTC day. If the canonical CSV is stale, it tries the same public CoinMarketCap download path
automatically, then imports the validated canonical CSV, recomputes risk, writes validation and brief data, and leaves
`/api/readiness` fresh.

If the canonical CSV already covers the target date, the scheduled run imports and recomputes from the existing CSV
without downloading. If the public download fails and `COINMARKETCAP_API_KEY` is configured, the collector falls back to
the optional official API delta refresh. If no API key is configured, the scheduled run fails visibly in collector logs
and preserves `collector/btc-csv/btc_usd_daily.csv`.

Operators can still run `./scripts/manage.sh download-cmc-csv` for a one-off public refresh, and manual
`import-cmc-csv` remains the fallback if public endpoint automation and any configured API fallback are unavailable.
Scheduled no-key refresh failures should alert through collector logs and stale readiness after the nightly update
window.

## Telegram Channel Publication

Before enabling channel publication, apply migration `004_telegram_posts.sql` with `./scripts/manage.sh migrate`.
Set `TELEGRAM_BOT_TOKEN` only in the operator-managed environment; an empty token disables publication before database
reads. Set `TELEGRAM_CHANNEL_ID` to identify the public channel. The collector considers publication only after an
import has written ready validation output.

Migration `004` is idempotent. A clean install creates nullable `posted_at` with no default. An existing database that
used the earlier branch-local `posted_at TIMESTAMPTZ NOT NULL DEFAULT now()` form is converged by dropping both the
default and the `NOT NULL` constraint, so unconfirmed claims retain `NULL` values.

The `telegram_posts` ledger claims a covered date with `message_id` and `posted_at` initially `NULL`. Telegram's
returned message ID confirms the claim. A definitive Telegram API rejection releases an unconfirmed claim. An
ambiguous delivery result, including a transport failure or non-JSON response after the POST, retains the claim; there
is no automatic reclaim because a missed post is preferred over a duplicate.

For the first enabled scheduled run, observe the collector log and the channel, then inspect the ledger:

```sql
SELECT as_of, message_id, posted_at FROM telegram_posts ORDER BY as_of DESC;
```

Before any manual cleanup of an unconfirmed claim, inspect exactly:

```sql
SELECT as_of FROM telegram_posts WHERE message_id IS NULL;
```

Do not clean up a claim until the channel has been checked manually and the operator has determined that no post was
delivered. To roll back publication, first disable `TELEGRAM_BOT_TOKEN`; preserve or delete claims only after an
operator decision based on that channel check. Automated tests must use `httpx.MockTransport` or `AsyncMock`; a
live-channel smoke post is not safe.

## Manual Downloaded CoinMarketCap CSV Refresh

Refresh BTC history without a paid CoinMarketCap API account by downloading a CSV from:

```text
https://coinmarketcap.com/currencies/bitcoin/historical-data/
```

Use a date range that starts at the day after the canonical CSV tail, or download the full available Bitcoin history.
The target tail is normally the last completed UTC day.

Stage the downloaded file where the `data-collector` container can read it:

```bash
mkdir -p collector/btc-csv/incoming
cp ~/Downloads/bitcoin-historical-data.csv collector/btc-csv/incoming/
```

Optionally inspect the downloaded range before importing:

```bash
PYTHONPATH=backend:collector python3 - <<'PY'
from pathlib import Path
from collector.downloaded_csv import load_coinmarketcap_downloaded_csv

rows = load_coinmarketcap_downloaded_csv(Path("collector/btc-csv/incoming/bitcoin-historical-data.csv"))
print(rows[0]["date"], rows[-1]["date"], len(rows))
PY
```

Import and require coverage through the expected UTC tail:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
```

The command validates the downloaded schema, rejects partial files, duplicate dates and daily gaps, atomically replaces
`collector/btc-csv/btc_usd_daily.csv` only after validation passes, and then runs the normal database import, risk
recomputation, validation write, brief write, and stale-row cleanup.

If validation fails, the existing canonical CSV is preserved. Fix the downloaded file or date range and rerun the command.

Open the app:

```text
http://localhost:3001
```

## Waitlist Review

Review aggregate waitlist counts and recent masked leads from the local or deployed project checkout:

```bash
./scripts/export_waitlist.sh
```

The default mode does not export full contact values. For manual founder/operator follow-up, write a full-contact CSV to
an operator-controlled location outside the repository:

```bash
./scripts/export_waitlist.sh --include-contacts --output /secure/path/waitlist.csv
```

Treat that CSV as PII. Do not store it under the project checkout, Git history, dependency caches, browser profiles, or
ad hoc public folders. The USB server kit includes this script in the deployed project snapshot, so it is available after
fresh installs and backup-gated updates.

## Production Import Provenance

Capture a sanitized evidence packet for every production import, including scheduled imports, one-off public
CoinMarketCap downloads, manual downloaded CSV imports, restores, and corrections. Store the packet outside the
repository and outside the production project checkout. A mounted off-server evidence directory or an operator-controlled
archive is acceptable; `./backups`, `collector/btc-csv/incoming/`, workstation downloads, and Git history are not the
long-term provenance archive.

Use [docs/operations/import-provenance-evidence-packet-template.md](import-provenance-evidence-packet-template.md) as the sanitized
operator checklist for the packet. Fill a copy outside Git first, then copy only redacted final status, hashes, row
counts, date ranges, cache/header facts, and accepted limitations into launch docs. The template is not completed
production import evidence.

Repository-local bundled CSV commits and tags can support repository history, but they are not production import
provenance. For example, 2026-07-11 local repository evidence records commit
`8cbc6998c757f1ca1716277104e099b4705dfba9`, tag
`btc-csv-through-2026-07-09-evidence-2026-07-11`, and local incoming source SHA-256
`38e9b0e8717013f217b93e7501aa3e216b1f989b52899cacff9e14c13f309d07` for the bundled canonical CSV rows through
2026-07-09. Treat that as local repository data evidence only. A production import still requires the outside-repository
packet below, including the production source snapshot, manifest, `sha256`, retrieval metadata, row counts/range,
validation/readiness output, cache evidence, and deployment/operator context.

Before or immediately after an import, create an archive directory:

```bash
cd /srv/projects/bitcoin-risk-brief
IMPORT_ARCHIVE_ROOT="<outside-repository-import-evidence-root>"
IMPORT_ID="$(date -u +%Y%m%dT%H%M%SZ)-btc-csv"
case "${IMPORT_ARCHIVE_ROOT}" in
  ""|/srv/projects/bitcoin-risk-brief|/srv/projects/bitcoin-risk-brief/*)
    echo "IMPORT_ARCHIVE_ROOT must be outside the project checkout" >&2
    exit 2
    ;;
esac
ARCHIVE_DIR="${IMPORT_ARCHIVE_ROOT%/}/${IMPORT_ID}"
install -d -m 700 "${ARCHIVE_DIR}"
```

Preserve the exact source input when practical:

```bash
SOURCE_PATH="<staged-source-csv-or-known-good-csv>"
test -s "${SOURCE_PATH}"
cp "${SOURCE_PATH}" "${ARCHIVE_DIR}/source.csv"
sha256sum "${ARCHIVE_DIR}/source.csv" > "${ARCHIVE_DIR}/source.sha256"
wc -c "${ARCHIVE_DIR}/source.csv" > "${ARCHIVE_DIR}/source.bytes"
```

After the import completes and readiness is healthy, preserve the canonical output and public evidence:

```bash
PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
CANONICAL_CSV=collector/btc-csv/btc_usd_daily.csv
cp "${CANONICAL_CSV}" "${ARCHIVE_DIR}/canonical-after.csv"
sha256sum "${ARCHIVE_DIR}/canonical-after.csv" > "${ARCHIVE_DIR}/canonical-after.sha256"
python3 - <<'PY' > "${ARCHIVE_DIR}/canonical-range.json"
import csv
import json
from pathlib import Path

rows = list(csv.DictReader(Path("collector/btc-csv/btc_usd_daily.csv").open(newline=""), delimiter=";"))
dates = [row["timeOpen"][:10] for row in rows]
print(json.dumps({"row_count": len(rows), "covered_start": dates[0], "covered_end": dates[-1]}, indent=2))
PY
git rev-parse HEAD > "${ARCHIVE_DIR}/git-commit.txt"
curl -fsS http://127.0.0.1:3001/api/readiness -o "${ARCHIVE_DIR}/readiness-origin.json"
curl -sD "${ARCHIVE_DIR}/risk-latest-public.headers" \
  -o "${ARCHIVE_DIR}/risk-latest-public.json" \
  "${PUBLIC_BASE_URL}/api/risk/latest"
podman-compose -f podman-compose.yml logs --tail=300 data-collector > "${ARCHIVE_DIR}/collector-log-tail.txt"
```

Create or validate the sanitized JSON manifest in the same directory. The local helper reads local files only, stores
file basenames rather than full paths, records `sha256`, observed row count/date range, canonical tail date, and supplied
evidence-file basenames, and rejects unsupported source types, checksum/date mismatches, malformed CSVs, and unsafe
manifest fields. It does not copy the source snapshot or prove production provenance by itself; operators must still
store the packet outside the repository and include the real production source, validation/readiness, cache, and
deployment/operator context.

Example helper flow:

```bash
python3 scripts/import_provenance_packet.py create \
  --source-type automatic_public_cmc \
  --source-csv "${ARCHIVE_DIR}/source.csv" \
  --canonical-csv "${ARCHIVE_DIR}/canonical-after.csv" \
  --output "${ARCHIVE_DIR}/manifest.json" \
  --evidence-created-at-utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --expected-end-date "${EXPECTED_END_DATE}" \
  --readiness-evidence "${ARCHIVE_DIR}/readiness-origin.json" \
  --validation-evidence "${ARCHIVE_DIR}/canonical-range.json" \
  --cache-evidence "${ARCHIVE_DIR}/risk-latest-public.headers" \
  --production-commit "$(cat "${ARCHIVE_DIR}/git-commit.txt")" \
  --note "sanitized packet for this production import"

python3 scripts/import_provenance_packet.py validate \
  --manifest "${ARCHIVE_DIR}/manifest.json" \
  --source-csv "${ARCHIVE_DIR}/source.csv"
```

If the helper is unavailable, create a manifest manually in the same directory. Use real values, not placeholders, before
treating it as evidence:

```json
{
  "manifest_id": "<YYYYMMDDTHHMMSSZ-btc-csv>",
  "import_timestamp_utc": "<YYYY-MM-DDTHH:MM:SSZ>",
  "operator_or_automation": "<operator-name-or-scheduler>",
  "git_commit": "<commit-sha>",
  "command_used": "<exact import command>",
  "source_type": "<automatic_public_cmc|manual_cmc_csv|optional_cmc_api|restore|correction>",
  "source_retrieval_method": "<retrieval method>",
  "source_url_or_page": "<source URL, download page, backup path, or retrieval note>",
  "staged_source_path": "<staged source path>",
  "archived_source_snapshot": "source.csv",
  "source_sha256": "<sha256>",
  "source_byte_size": "<bytes>",
  "source_row_count": "<rows>",
  "covered_start": "<YYYY-MM-DD>",
  "covered_end": "<YYYY-MM-DD>",
  "expected_tail_date": "<YYYY-MM-DD>",
  "canonical_csv_path_after_import": "collector/btc-csv/btc_usd_daily.csv",
  "canonical_csv_sha256_after_import": "<sha256>",
  "validation_row_count": "<rows>",
  "validation_covered_end": "<YYYY-MM-DD>",
  "validation_source_strategy": "<source strategy>",
  "methodology_version": "crypto-scout-canonical-v1.1",
  "readiness_status_after_import": "<ready|degraded>",
  "latest_risk_date": "<YYYY-MM-DD>",
  "latest_risk_value": "<risk value>",
  "latest_brief_timestamp": "<timestamp-or-null>",
  "evidence_files": {
    "readiness_origin": "readiness-origin.json",
    "risk_latest_public_headers": "risk-latest-public.headers",
    "risk_latest_public_payload": "risk-latest-public.json",
    "collector_log_summary": "collector-log-tail.txt"
  },
  "related_launch_note": null,
  "related_restore_note": null,
  "related_correction_note": null,
  "accepted_limitations": []
}
```

The manifest, readiness payload, cache evidence, restore notes, launch notes, and correction notes should reference the
same `manifest_id`. Correction notes should also name the affected source hash or explicitly say that provenance is
missing. Do not copy `.env` values, API keys, Cloudflare tokens, waitlist contacts, raw analytics, browser profiles,
private account exports, or other PII into the archive.

## Service Logs

Follow all logs:

```bash
./scripts/manage.sh logs
```

Follow a single service:

```bash
./scripts/manage.sh logs backend
./scripts/manage.sh logs data-collector
./scripts/manage.sh logs frontend
./scripts/manage.sh logs timescaledb
```

Backend API access logs include method, path, status, client key, Cloudflare ray ID when present, cache status, and
duration. Use them to distinguish normal page loads from bursts against `/api/waitlist` or `/api/*` without logging
waitlist contact values.

## Health and Readiness

Basic health:

```bash
curl -fsS http://localhost:3001/api/health
```

Production readiness:

```bash
curl -fsS http://localhost:3001/api/readiness
```

Readiness should be used for deployment probes and monitoring alerts. After an automatic or manual CSV import, readiness
should be HTTP 200 before the refreshed data is trusted.

## Monitoring And Alerts

Local public endpoint probe tooling is available for cron jobs, a synthetic monitor runner, or an external monitoring
provider script step:

```bash
python3 scripts/check_public_endpoints.py \
  --base-url https://bitcoinriskbrief.minihub.app \
  --max-data-age-days 2
```

Use `--expected-latest-date YYYY-MM-DD` when the monitor should require one exact latest data date instead of, or in
addition to, a maximum age. The probe intentionally has no default freshness policy; every cron or monitor invocation
must provide `--max-data-age-days`, `--expected-latest-date`, or both. It checks only `GET /api/health`,
`GET /api/readiness`, and `GET /api/risk/latest`, exits 0 only when the requested assertions pass, and prints concise
sanitized status without raw response dumps.

Optional cache-header assertions can be enabled for the cacheable public read endpoints:

```bash
python3 scripts/check_public_endpoints.py \
  --base-url https://bitcoinriskbrief.minihub.app \
  --max-data-age-days 2 \
  --require-cache-header Cache-Control \
  --require-cache-header ETag \
  --require-cache-header X-Cache-Version \
  --require-cache-header X-Cache
```

Small operator-watched pilot monitoring coverage accepted on 2026-07-14:

- Cloudflare Tunnel Health Alert is configured.
- External uptime monitor provider category is HetrixTools/external uptime monitor provider.
- Public homepage availability monitoring is configured for `https://bitcoinriskbrief.minihub.app/`.
- This accepted coverage is intentionally limited to Tunnel health plus homepage availability for a small
  operator-watched pilot. It is not full API readiness/freshness monitoring and does not prove alert delivery.

Before broader public traffic, configure and record redacted evidence for these monitors. Store provider names, sanitized
check names, monitored paths, assertion summaries, intervals/windows, latest check status, and delivery-test status only;
do not record tokens, account IDs, private dashboard URLs, recipient addresses, phone numbers, IPs, raw logs with PII, or
secret values.

Use [docs/operations/monitoring-alert-evidence-packet-template.md](monitoring-alert-evidence-packet-template.md) to collect the
sanitized provider, scheduler, probe, backup freshness, Cloudflare connector, and alert-delivery fields before copying
final outcomes into launch docs. The template is not provider evidence and does not mark the gate passed.

- Health uptime: before broader launch, monitor `GET https://bitcoinriskbrief.minihub.app/api/health`; alert on HTTP
  non-200, timeout, or TLS failure. The local probe can supply this assertion, but provider/dashboard evidence is still
  required before full API monitoring is treated as configured.
- Readiness/freshness: before broader launch, monitor `GET https://bitcoinriskbrief.minihub.app/api/readiness`; alert on
  HTTP non-200, `status` not `ready`, or `checks.data_fresh` not `true`. The local probe can also require an exact latest
  date or a maximum data age and compare readiness with `/api/risk/latest`.
- Stale data: after the nightly collector window plus the operator-defined grace period, alert when readiness is HTTP
  503, `data_age_days` exceeds `max_age_days`, or `latest_date`/`covered_end` is older than the last completed UTC day.
- Collector failure: alert on `scheduled_refresh_failed`, `public_cmc_download_failed`, API fallback failure, missed
  scheduled refresh evidence, or repeated `data-collector` restarts.
- Backup freshness/off-server copy: choose the freshness window, schedule backups and off-server copies, run
  `scripts/check_backup_freshness.py`, and alert when no checksum-verified backup plus off-server copy exists inside
  that window.
- Cloudflare Tunnel connector health: enable or document Cloudflare Zero Trust connector-down or flapping notifications
  for the tunnel serving `bitcoinriskbrief.minihub.app`; record whether production uses host-service `cloudflared` or
  compose-managed `cloudflared`. Current small-pilot status records Cloudflare Tunnel Health Alert as configured, without
  private account, tunnel, dashboard, routing, or recipient details.
- Alert delivery channel: before broader launch, choose the pilot channel, send a provider test notification, and record
  only the channel type, test time, and delivered/not-delivered result.

## Cache Verification

Readiness is intentionally not cacheable. `GET /api/readiness` should return `Cache-Control: no-store` and should be
used as the live freshness/status check before trusting public risk payloads.

Public product read endpoints are cacheable at the backend and edge:

- `/api/risk/latest`
- `/api/risk/history`
- `/api/risk/levels`
- `/api/brief/latest`

Check cache headers on a public read endpoint:

```bash
curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest
```

Expected headers include `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`. Repeat the same request and confirm
`X-Cache: HIT` once the backend has built the payload:

```bash
curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest
```

The backend warms standard public product payloads during startup after the database pool is ready and readiness is
healthy. Startup warmup runs the standard product targets concurrently, isolates per-target failures, and logs
`public_cache_warmup_complete` with warmed count, failed count, total duration, and the slowest targets. If validation
data is missing, readiness cannot be probed, or readiness returns a non-200 status, startup warmup is skipped and logged
so degraded or stale data is not hidden.

Warm the standard public product payloads after manual or scheduled imports before active traffic:

- `/api/risk/latest`
- `/api/risk/history?limit=730`
- `/api/risk/levels`
- `/api/brief/latest`

The warmup script checks readiness first as a `curl -f` gate, but does not warm readiness as a cached payload.

For the normal local production import flow:

```bash
./scripts/manage.sh run-now
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
```

For the automatic public CoinMarketCap CSV flow:

```bash
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
```

For an operator-downloaded CSV flow:

```bash
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
```

`warm-public-cache` uses normal public GET endpoints against `PUBLIC_BASE_URL`, which should point to a local or private
origin such as `http://127.0.0.1:3001`. It does not add or call a public admin endpoint. The readiness request runs
first with `curl -f`, so readiness must be HTTP 200 before the command warms the remaining payloads. Production
stale/degraded readiness remains a blocker until the production data issue is fixed. Each warmup request uses
`curl -fsS`, so any non-success response fails the command instead of silently accepting a partial warmup. This command
only benefits production after the warmup implementation is deployed there.

The expensive first-miss candidate is `/api/risk/levels`, because it reads full OHLCV history and builds risk-level rows
on demand. Historical design context remains in
`docs/superpowers/specs/2026-07-01-public-payload-cache-warmup-precompute-design.md`.

Verify conditional revalidation:

```bash
ETAG="$(curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest | awk 'BEGIN{IGNORECASE=1} /^etag:/ {print $2}' | tr -d '\r')"
curl -s -o /dev/null -w "%{http_code}\n" -H "If-None-Match: ${ETAG}" http://localhost:3001/api/risk/latest
```

The second command should print `304`.

After `backfill`, `run-now`, `download-cmc-csv`, or `import-cmc-csv`, the collector writes a new
`btc_risk_validation` marker. The backend derives `X-Cache-Version` from that marker, so the next public read misses the
old in-process cache and rebuilds from the database unless startup or operator warmup has already rebuilt the standard
key. If Cloudflare cache is enabled, purge the hostname or wait for `PUBLIC_CACHE_MAX_AGE_SECONDS` before using cached
public data for a launch snapshot.

`POST /api/waitlist` must remain uncached. Confirm it returns `Cache-Control: no-store` during launch checks.
Every waitlist outcome, including Turnstile rejection (`403`) and temporary verification/configuration failure (`503`),
must remain no-store; failed verification must not create a lead.

For issue #35, local verification can cover backend cache correctness, warmup timing, and header behavior. Keep the issue
open until a deployed production version has been checked with GET-only public endpoint smoke tests and startup/import
warmup log review.

## Launch Snapshot Packet

Local launch snapshot packet tooling is available for future pre-traffic or pre-update evidence windows. The
2026-07-15 final launch snapshot was already created and validated outside Git; use this helper again only when a future
snapshot needs a fresh sanitized packet:

```bash
python3 scripts/launch_snapshot_packet.py create \
  --output "${ARCHIVE_DIR}/launch-snapshot-packet.json" \
  --packet-created-at-utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --production-commit "$(git rev-parse HEAD)" \
  --base-url https://bitcoinriskbrief.minihub.app \
  --readiness-evidence "${ARCHIVE_DIR}/readiness-public.json" \
  --readiness-status present \
  --readiness-latest-date "${EXPECTED_LATEST_DATE}" \
  --readiness-data-fresh true \
  --latest-risk-evidence "${ARCHIVE_DIR}/risk-latest-public.json" \
  --latest-risk-status present \
  --latest-risk-timestamp "${LATEST_RISK_TIMESTAMP}" \
  --latest-risk-state low \
  --public-endpoint-monitor-probe-evidence "${ARCHIVE_DIR}/public-endpoint-probe.txt" \
  --public-endpoint-monitor-probe-status present \
  --public-endpoint-monitor-probe-summary "health readiness latest-risk assertions passed" \
  --waitlist-smoke-status present \
  --waitlist-smoke-summary "HTTP 201 no-store aggregate-only storage verification" \
  --import-provenance-packet "${ARCHIVE_DIR}/import-provenance.json" \
  --import-provenance-status present \
  --backup-freshness-evidence "${ARCHIVE_DIR}/backup-freshness.txt" \
  --backup-freshness-status present \
  --accessibility-status pending \
  --browser-status pending \
  --metadata-status pending
```

Validate an existing packet without contacting the network:

```bash
python3 scripts/launch_snapshot_packet.py validate \
  --packet "${ARCHIVE_DIR}/launch-snapshot-packet.json"
```

The helper stores evidence basenames, not full paths, and rejects unsafe packet values such as absolute/private paths,
token-like strings, environment assignments, raw waitlist contacts, phone numbers, dashboard URLs, raw logs, and raw
response dumps. Missing evidence categories are reported as pending gates rather than treated as passed. Operator
decisions such as waitlist owner, review cadence, retention, deletion/unsubscribe path, support/contact identity,
account ownership, and data-source terms must be supplied to the packet only as sanitized status values with
`--operator-decision name=status`. The current sanitized decision status is recorded in
[Production Readiness](production-readiness.md); the helper still treats any omitted packet category as pending.

The first-traffic field defaults to the helper's no-run state. Do not change it in a future snapshot unless an operator
has separate sanitized first-traffic evidence for that specific window and intentionally supplies the explicit
first-traffic fields. Creating or validating a packet does not prove the snapshot is complete, does not configure
monitors or alerts, does not prove production import provenance or backup freshness, and does not run traffic.

## Post-Pilot And Future Update Sequence

Run this sequence from the selected production path and the operator-controlled evidence archive after the completed
small-pilot first-traffic window, or before future pilot traffic/update windows. Record only sanitized evidence: status,
dates, commit IDs, timestamp basenames, check names, and pass/fail summaries. Do not record secrets, tokens, `.env`
values, raw waitlist contacts, private account details, raw logs, dashboard URLs, private contacts, or private filesystem
paths.

1. Confirm the intended scope: post-pilot observation only, a future production update, a future pilot-window evidence
   refresh, or broader-launch preparation. Do not expand the 2026-07-15 first-traffic evidence into broad launch claims.
2. Verify the selected production path and project revision. Record service status, local health/readiness, public
   readiness, and whether the current Cloudflare Free-plan edge subset remains accepted or an upgraded edge posture is
   configured.
3. Recheck public freshness before promoting additional traffic:

```bash
python3 scripts/check_public_endpoints.py \
  --base-url https://bitcoinriskbrief.minihub.app \
  --max-data-age-days 2 \
  --require-cache-header Cache-Control \
  --require-cache-header ETag \
  --require-cache-header X-Cache-Version \
  --require-cache-header X-Cache
```

4. If a data refresh/import is run, create a production import provenance packet from the real source snapshot, source
   `sha256`, retrieval metadata, canonical output, validation/readiness output, public cache evidence, row count/range,
   expected tail, and deployment/operator context. Keep the packet outside Git.
5. Keep the 2026-07-15 final launch snapshot and first-traffic evidence available, but create a new sanitized snapshot
   packet only for a future launch/update window that needs one. Keep missing categories pending; do not reuse old
   first-traffic fields for a new window.
6. Keep accepted small-pilot monitoring active: Cloudflare Tunnel Health Alert plus public homepage availability
   monitoring. Dedicated external API monitors, stale-data after-window alerting, collector-failure alerts, backup
   freshness alerts, and explicit alert delivery evidence remain broader-launch work.
7. Keep backup/off-server evidence fresh for update windows. Recurring backup automation remains post-pilot work until
   configured, and the restore drill remains deferred until a staging project or intentionally empty restore target
   exists.
8. Summarize post-traffic learning with the [Pilot Learning Loop](pilot-learning-loop.md). Use aggregate
   waitlist/source/locale/repeat-use/request signals and sanitized support themes only. Do not copy raw contacts, raw
   analytics, raw messages, account IDs, dashboard URLs, or private support details into Git.

## Cloudflare Edge Rules

Render the repo-managed Cloudflare WAF, rate-limit, cache, and waitlist bot-challenge rules:

```bash
python3 scripts/cloudflare_edge_rules.py render --hostname risk.example.com > /tmp/bitcoin-risk-cloudflare-edge.json
```

Apply the rules with an operator API token:

```bash
export CLOUDFLARE_ZONE_ID=replace-with-zone-id
export CLOUDFLARE_API_TOKEN=replace-with-api-token
python3 scripts/cloudflare_edge_rules.py apply \
  --zone-id "${CLOUDFLARE_ZONE_ID}" \
  --hostname risk.example.com
```

To update only the cache settings rules for the production pilot hostname, use the narrower helper. It preserves unrelated
Cloudflare rules and only changes the repo-managed cache settings entrypoint. Add `--purge` to purge
`https://bitcoinriskbrief.minihub.app/api/readiness` immediately after the rule update:

```bash
export CLOUDFLARE_ZONE_ID=replace-with-zone-id
export CLOUDFLARE_API_TOKEN=replace-with-api-token
scripts/apply-cloudflare-cache-rules.sh --purge
```

For a Cloudflare Free plan that is not entitled to execute the managed WAF ruleset, create more than one rate-limit rule,
or use 60-second rate-limit windows, apply the current public-pilot subset instead:

```bash
python3 scripts/cloudflare_edge_rules.py apply \
  --zone-id "${CLOUDFLARE_ZONE_ID}" \
  --hostname bitcoinriskbrief.minihub.app \
  --skip-managed-waf \
  --waitlist-rate-limit-only \
  --rate-limit-period 10 \
  --rate-limit-mitigation-timeout 10
```

The script preserves unrelated Cloudflare rules and only replaces rules with refs starting `bitcoin-risk-brief:`. After
applying it, enable Cloudflare Bot Fight Mode, Super Bot Fight Mode, or equivalent dashboard bot protection if the active
plan supports it. Record any accepted plan limitations before broader traffic or a future pilot-window promotion.

Verify the public hostname after applying edge rules:

```bash
curl -fsS https://risk.example.com/api/health
curl -sD - -o /tmp/bitcoin-risk-readiness.json https://risk.example.com/api/readiness
curl -sD - -o /tmp/bitcoin-risk-latest.json https://risk.example.com/api/risk/latest
```

Readiness should return `Cache-Control: no-store`. Cacheable product read responses should include `Cache-Control`,
`ETag`, and `X-Cache-Version`. Waitlist submissions should still work for normal users and return
`Cache-Control: no-store`.

## Backups

Create a timestamped backup of PostgreSQL and the canonical BTC CSV:

```bash
./scripts/backup.sh
```

Preview the target paths without touching the database:

```bash
./scripts/backup.sh --dry-run
```

Production defaults can be controlled from the environment:

```bash
BACKUP_DIR=./backups BACKUP_RETENTION_DAYS=30 ./scripts/backup.sh
```

The PostgreSQL dump runs non-interactively through direct `podman exec` against the running `timescaledb` container. The
main controls are `BACKUP_DUMP_TIMEOUT_SECONDS=300`,
`BACKUP_PODMAN_PS_TIMEOUT_SECONDS=20`, `BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS=10`, and
`BACKUP_DUMP_LOCK_WAIT_TIMEOUT=30s`; increase the dump timeout only after checking Podman health, database locks, and
disk pressure.

Each backup directory contains:

- compressed PostgreSQL custom-format `pg_dump` output;
- a copy of `collector/btc-csv/btc_usd_daily.csv`;
- `manifest.txt` with source metadata;
- `SHA256SUMS` for integrity checks.

Backups should be copied off the server. Keeping the only backup under `./backups` protects against accidental database edits, but not against disk failure.

Check local backup freshness and checksums without creating or modifying backup files:

```bash
python3 scripts/check_backup_freshness.py \
  --backup-root ./backups \
  --max-age-hours 30
```

The freshness window is intentionally required; choose the production value before putting the check under cron or an
external monitor. The checker validates the newest timestamped backup directory basename, required PostgreSQL dump, BTC
CSV copy, `manifest.txt`, `SHA256SUMS`, and checksum verification using `sha256sum` or `shasum -a 256`. It prints concise
status with the timestamp basename and exits nonzero when the backup is missing, stale, malformed, or checksum-invalid.

After verified backups are copied to off-server storage, require the same timestamped basename under the off-server root:

```bash
python3 scripts/check_backup_freshness.py \
  --backup-root ./backups \
  --off-server-root "<mounted-off-server-backup-root>" \
  --max-age-hours 30
```

For cron or a monitoring wrapper, the same values can come from the environment:

```bash
BACKUP_DIR=./backups \
OFFSERVER_BACKUP_ROOT="<mounted-off-server-backup-root>" \
BACKUP_FRESHNESS_MAX_AGE_HOURS=30 \
python3 scripts/check_backup_freshness.py
```

Local checker implementation and unit coverage are in place. A 2026-07-11 backup-gated USB production update recorded a
copied/off-server freshness/checksum checker pass for timestamp basename `20260711T190355Z` as valid and fresh, and the
2026-07-15 fresh manual backup/off-server copy evidence records timestamp basename `20260715T082457Z` with PostgreSQL
dump, BTC CSV, manifest, and checksum artifacts present plus copied-backup SHA-256 verification passed. Production
scheduling, recurring off-server copy configuration, and external alert delivery remain pending until an operator records
redacted recurring evidence from the production host or monitoring system.

Use [docs/operations/backup-restore-evidence-packet-template.md](backup-restore-evidence-packet-template.md) to collect the
sanitized backup run, off-server copy, freshness/checksum, scheduler, alert-delivery, and safe restore-target fields
outside Git before copying final outcomes into launch docs. The template is not completed backup or restore evidence.

## USB Kit Packaging And Updates

Prepare the USB kit on the workstation from the repository checkout:

```bash
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

The command creates `/Volumes/USB/bitcoin-risk-brief-server-kit` and replaces only that kit directory when rerun. The
expected kit contents are deployment docs, a top-level `deploy-from-usb.sh` entrypoint, ordered server scripts, a
filtered `project/bitcoin-risk-brief/` snapshot, `manifest.txt`, and `SHA256SUMS`.

The USB kit must not contain local `.env`, `.git`, backups, database volumes, dependency caches, build output, browser
artifacts, container images, or an offline package mirror. The workstation project snapshot keeps backup artifacts out of
the kit.

Fresh install on the server remains an ordered script flow from the mounted kit:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash scripts/01-bootstrap-host.sh
bash scripts/02-install-cloudflared-from-usb.sh
bash scripts/03-deploy-bitcoin-risk-brief.sh
sudo bash scripts/09-install-telegram-env-from-usb.sh
sudoedit /srv/projects/bitcoin-risk-brief/.env
bash scripts/04-enable-bitcoin-risk-service.sh
bash scripts/05-health-check.sh
```

For an existing production deployment, use the top-level deploy entrypoint:

Before the update build/restart, edit the existing server `.env`: set `VITE_TURNSTILE_SITE_KEY` to the public sitekey in
the operator-controlled Managed-widget record, `TURNSTILE_SECRET` to its matching private secret from
operator-controlled storage, and `TURNSTILE_HOSTNAMES` exactly to `bitcoinriskbrief.minihub.app`. If Telegram channel
publication should be enabled, put `bitcoin-risk-brief-telegram.env` beside the kit and run
`sudo bash scripts/09-install-telegram-env-from-usb.sh`, or set `TELEGRAM_BOT_TOKEN` and
`TELEGRAM_CHANNEL_ID=@bitcoinriskbrief` directly in the server `.env`; leave `TELEGRAM_BOT_TOKEN` empty to keep
publication disabled. The production `.env` stays on the server, is preserved by the update, and is excluded from the USB
kit. Then run:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app
```

The backup-gated command verifies `SHA256SUMS`, runs a backup from the current deployed project before copying new code,
verifies the backup checksums, copies the verified backup to the USB default `backups-from-server/` or an
operator-provided `BACKUP_COPY_DEST`, verifies the copied backup, then deploys and checks the service.

The Turnstile integration is not yet USB-deployed or production-validated. Do not infer that status from the earlier
backup-gated update evidence below; record new sanitized operator evidence only after this update completes.

Production update evidence recorded on 2026-07-11 confirms this backup-gated flow for target commit
`86cb2dad889baf24a7464a105bbe2224f75b14ef`: the server-reported exit code was 0, the copied/off-server
freshness/checksum checker passed for timestamp basename `20260711T190355Z`, public readiness/latest checks passed,
public metadata/privacy smoke passed, and desktop/mobile browser smoke passed without waitlist POSTs. That evidence does
not record a data refresh/import, monitor configuration, restore drill, launch snapshot, or first traffic.

## Restore Notes

Restore only into a staging copy or an intentionally empty restore target that is not serving live production traffic.
On the current single-server production setup, defer restore drills until a separate target exists; do not run a restore
drill against the live production database:

```bash
podman-compose -f podman-compose.yml exec -T timescaledb pg_restore --clean --if-exists --no-owner --no-privileges -U postgres -d bitcoin_risk_brief < backups/<timestamp>/postgres_<timestamp>.dump
cp backups/<timestamp>/btc_usd_daily_<timestamp>.csv collector/btc-csv/btc_usd_daily.csv
./scripts/manage.sh run-now
curl -fsS http://localhost:3001/api/readiness
```

Take the public app offline before restoring production data. TimescaleDB may print circular foreign-key warnings during backup; treat them as informational only when `scripts/backup.sh` exits with code 0.

## Bad-Data Correction Policy

This policy is an internal production-pilot operating procedure, not a public SLA. It applies when a wrong source row,
bad manual import, stale cache, methodology defect, corrupted database row, or incorrect brief may have reached the
public product.

Classify the issue before changing data:

- **Low:** cosmetic copy, chart label, or portfolio text issue that does not change risk value, data date, freshness, or
  readiness.
- **Medium:** stale data, delayed import, missing latest completed UTC day, cache inconsistency, or incorrect brief text
  while the canonical historical BTC data remains valid.
- **High:** wrong source data, bad manual import, wrong methodology output, corrupted DB rows, incorrect latest risk
  value, or a misleading public risk state.

High severity pauses active promotion and requires a correction note. Medium severity needs an operator note and a fix
before broader traffic resumes. Low severity can wait for the next normal release if no trust claim is wrong.

For a suspected published bad-data incident:

1. Record the first observed UTC time, public URL, affected endpoint, displayed data date, displayed risk value if any,
   current commit, and who observed it.
2. Inspect readiness, validation metadata, collector logs, latest public payload, and the CSV tail:

```bash
PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
curl -sD - -o /tmp/bitcoin-risk-readiness-public.json "${PUBLIC_BASE_URL}/api/readiness"
curl -sD - -o /tmp/bitcoin-risk-latest-public.json "${PUBLIC_BASE_URL}/api/risk/latest"
curl -fsS http://127.0.0.1:3001/api/readiness -o /tmp/bitcoin-risk-readiness-origin.json
podman-compose -f podman-compose.yml logs --tail=300 data-collector
podman-compose -f podman-compose.yml exec timescaledb psql -U postgres -d bitcoin_risk_brief -t -A -c "SELECT validation_json->>'source', validation_json->'validation'->>'source_strategy', covered_end, row_count, passed FROM btc_risk_validation WHERE validation_key='latest';"
tail -n 10 collector/btc-csv/btc_usd_daily.csv
```

3. Stop or defer automated imports if they could overwrite evidence or make the source harder to inspect:

```bash
podman-compose -f podman-compose.yml stop data-collector
```

4. Identify the last known-good source from the import provenance archive, latest off-server backup, previous canonical
   CSV, staged manual CSV, or a fresh trusted operator-downloaded CoinMarketCap CSV.
5. Restore or re-import the known-good CSV. Prefer re-importing a known-good CSV when the database is otherwise healthy;
   use the restore procedure only when database state is corrupted or re-import cannot confidently repair the product:

```bash
EXPECTED_END_DATE="<known-good-covered-end>"
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
```

6. Recompute risk and the latest brief through the import command or, after copying a known-good canonical CSV from a
   backup, by running:

```bash
./scripts/manage.sh run-now
```

7. Verify origin data, public edge behavior, cache version, latest brief, and history tail:

```bash
curl -fsS http://127.0.0.1:3001/api/readiness
curl -sD - -o /tmp/bitcoin-risk-latest-origin.json http://127.0.0.1:3001/api/risk/latest
curl -sD - -o /tmp/bitcoin-risk-brief-origin.json http://127.0.0.1:3001/api/brief/latest
curl -sD - -o /tmp/bitcoin-risk-latest-public.json "${PUBLIC_BASE_URL}/api/risk/latest"
curl -sD - -o /tmp/bitcoin-risk-levels-public.json "${PUBLIC_BASE_URL}/api/risk/levels"
```

Expected public read headers include `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`, and the latest risk
timestamp should match readiness `covered_end`. If stale edge responses can show a known-wrong value, purge the
Cloudflare hostname/API cache or disable public ingress until corrected payloads are visible.

8. Capture a correction note outside the repository, and add a redacted summary to production readiness when it affects
   launch status. Include cause if known, affected window, affected endpoints, source/manifest id, bad and corrected
   data dates, whether the risk value changed, verification commands, cache evidence, downtime if any, and whether a
   public or portfolio note is required. If provenance is missing, say so explicitly. Do not blame a vendor without
   evidence and do not imply an audit.
9. Restart the scheduled collector only after the corrected state and evidence are captured:

```bash
podman-compose -f podman-compose.yml start data-collector
```

Internal pilot service targets:

- **Freshness:** production should normally cover the last completed UTC day within `DATA_FRESHNESS_MAX_AGE_DAYS`,
  currently `2` unless explicitly changed.
- **Correction target:** high-severity bad-data issues should be investigated the same operator day and either corrected
  or marked as an accepted limitation before additional promotion.
- **RPO boundary:** recover to the latest verified off-server backup or known-good canonical CSV/source snapshot.
- **RTO boundary:** no public guarantee for the free pilot. Define a realistic target from restore-drill evidence before
  paid or professional usage.
- **Downtime boundary:** temporary downtime is acceptable while fixing data integrity. Serving a known-wrong risk value
  is worse than being temporarily unavailable.

## Resource And Ownership Checks

Before active traffic, record the operator and recovery path for:

- GitHub repository access;
- Cloudflare account, tunnel, zone, and API token;
- domain registration if a custom domain is used;
- production `.env` storage;
- backup storage;
- server login or physical access;
- optional CoinMarketCap API credentials.

Operational review should also check disk usage, database volume growth, backup directory growth, container restart
loops, Cloudflare Tunnel connector health, public hostname availability, and any infrastructure cost or resource limits.

## Launch Governance Operating Notes

Recorded on 2026-07-05 for the production-pilot candidate and updated through the 2026-07-15 watched first-traffic
evidence in [Production Readiness](production-readiness.md):

- Privacy/terms/disclaimer note: locally implemented on 2026-07-10 as compact public copy near the waitlist, with
  public-host smoke verification recorded in the 2026-07-11 update evidence. It documents
  no-advice/no-recommendation limits, sensitive-info caution, implemented waitlist storage, operational log fields, no
  paid support SLA, and the current absence of app product-analytics/tracking-cookie source code.
- Waitlist lead owner and cadence: partial/resolved for pilot. Owner role is founder/operator, with review several times
  per week during the pilot through a manual operator-run database query or script. Do not record raw contacts, raw
  output, private paths, or query details in Git.
- Waitlist retention: partial/resolved for pilot. Retain pilot contacts until beta ends; delete earlier on
  operator-approved request. Record only sanitized status in Git.
- Deletion and unsubscribe path: completed for first-traffic readiness. Use manual requests through the dedicated support
  contact path kept outside Git for deletion, unsubscribe, product questions, bug reports, and professional/API/license
  interest. Keep the actual address or handle out of this repository unless the operator intentionally makes it public.
- Support/contact identity: completed for first-traffic readiness. The path category is a dedicated support mailbox with
  a project-domain alias, exact addresses and provider details are kept outside Git, and no paid support SLA is recorded.
  Do not add an SLA unless the operator explicitly creates one.
- Manual waitlist handling: review aggregate lead counts and source/locale values without copying contact values into
  general notes. Raw waitlist contacts should stay in the production database or another controlled operational system.
- Credential/account ownership: completed for first-traffic readiness. Owner role for GitHub, Cloudflare/domain, server,
  secrets/.env, and backups is founder/operator, and the account recovery record is created outside Git and current. Track
  recovery for the categories in the resource checklist above, but do not store holders, emails, account IDs, secrets,
  account exports, personal account details, secret locations, or private recovery paths in Git.
- Fresh manual backup/off-server copy: completed for the current first-traffic evidence set by the 2026-07-15 copied
  backup timestamp basename `20260715T082457Z`; PostgreSQL dump, BTC CSV, manifest, and checksum categories were present,
  and copied-backup SHA-256 verification passed. Recurring backup automation, backup freshness monitoring, and backup
  alert delivery remain deferred until after the initial operator-watched pilot.
- Dependency and security maintenance cadence: `.github/dependabot.yml` is configured locally for conservative monthly
  version-update checks across frontend npm, backend and collector pip requirements, GitHub Actions, Dockerfiles, and the
  root `docker-compose` ecosystem entry for Compose-style image references. GitHub-hosted Dependabot execution, first PR
  evidence, and Podman-specific filename handling remain pending until the config is merged/pushed and observed. Continue
  the monthly manual review for security advisories, vulnerability scan results if available, secret-scan output, Python
  transitive inventory, container image and OS package licenses, GitHub Actions/license posture, scoped project-licence
  boundaries, third-party market-data terms, and legal compatibility. Record only the date, scope, outcome, and required
  follow-up.
- Data-source terms review: accepted limitation for the unpaid/non-commercial pilot only. Record the CoinMarketCap public
  CSV and optional API usage terms/plan outcome before commercial claims, paid beta, or broader distribution. For future
  methodology sources, record terms and attribution before the source becomes production-critical.
- Cloudflare Free-plan first-traffic decision: accepted limitation for a small operator-watched pilot only. Managed WAF
  execution, broader `/api/*` burst limiting, multiple rate-limit rules, and longer rate-limit windows remain deferred
  until broader traffic or observed abuse risk.
- Small-pilot monitoring acceptance: Cloudflare Tunnel Health Alert plus external public homepage availability monitoring
  are accepted for the small operator-watched pilot only. Dedicated external `/api/health` and `/api/readiness`
  freshness monitoring, stale-data after-window alerting, and explicit alert delivery proof remain pending before broader
  launch.
- Accessibility and metadata pass: browser-capable public-hostname QA is recorded, and local focused accessibility,
  chart-alternative, waitlist live-region/keyboard, privacy/terms/disclaimer, and SEO/social metadata evidence exists.
  The 2026-07-15 manual/native browser QA evidence completes the small-pilot manual keyboard/native desktop and mobile
  browser blocker. The 2026-07-15 assistive-tech proxy QA pass records the missing dedicated screen-reader/manual
  assistive-tech pass as an accepted limitation only for the small operator-watched pilot. True assistive-tech evidence,
  broader accessibility evidence, and full WCAG/legal accessibility approval remain pending before broader claims.
- Restore drill: accepted limitation/deferred until a staging project or intentionally empty restore target exists. Do not
  run a restore drill against live production.
- Feedback review path: after the completed first controlled traffic window and during the pilot, use the
  [Pilot Learning Loop](pilot-learning-loop.md) to summarize waitlist conversion, repeat-use signals, direct questions,
  and requests for alerts, API access, agents, widgets, embeddings, or licensing into the production readiness or roadmap
  notes. Do not copy raw contacts into feedback summaries.

## First-Response Runbook

Run commands from the production project directory unless the step names a public URL or Cloudflare dashboard. The current
pilot production directory is `/srv/projects/bitcoin-risk-brief`; the current public hostname is
`https://bitcoinriskbrief.minihub.app`.

If the runbook says to take public traffic down, disable only the public ingress first: stop the Cloudflare Tunnel
connector or disable the public hostname route in the Cloudflare Zero Trust dashboard. Do not expose `FRONTEND_PORT`
directly to the internet as a workaround.

### `/api/readiness` degraded or non-200

- Where to look first: public readiness JSON, local readiness JSON, container state, backend logs, and validation
  metadata.
- Check:

```bash
PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
curl -sD - -o /tmp/bitcoin-risk-readiness-public.json "${PUBLIC_BASE_URL}/api/readiness"
curl -fsS http://127.0.0.1:3001/api/readiness -o /tmp/bitcoin-risk-readiness-local.json
podman-compose -f podman-compose.yml ps
podman-compose -f podman-compose.yml logs --tail=200 backend
podman-compose -f podman-compose.yml exec timescaledb psql -U postgres -d bitcoin_risk_brief -t -A -c "SELECT validation_json->>'source', validation_json->'validation'->>'source_strategy', covered_end, row_count, passed FROM btc_risk_validation WHERE validation_key='latest';"
```

- First safe action: if the only failed readiness flag is stale data, run the scheduled refresh fallback and recheck
  readiness:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
curl -fsS http://127.0.0.1:3001/api/readiness
curl -fsS "${PUBLIC_BASE_URL}/api/readiness"
```

- Pause promotion or take public traffic down: pause every deploy or traffic promotion while readiness is non-200. Take
  public traffic down if public readiness stays non-200 after the safe refresh path, if validation metadata is missing or
  failed, or if the public page could be serving stale or wrong risk data.

### Scheduled data refresh failure

- Where to look first: `data-collector` logs after the configured UTC schedule, the canonical CSV tail, and readiness.
- Check:

```bash
podman-compose -f podman-compose.yml logs --tail=300 data-collector
tail -n 5 collector/btc-csv/btc_usd_daily.csv
curl -fsS http://127.0.0.1:3001/api/readiness
```

- First safe action: run the same no-key public refresh target manually. This path validates before replacing the
  canonical CSV:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
curl -fsS http://127.0.0.1:3001/api/readiness
```

- Pause promotion or take public traffic down: pause promotion if the scheduled run did not complete before broader
  promotion or future pilot-window checks. Take public traffic down if readiness becomes stale beyond
  `DATA_FRESHNESS_MAX_AGE_DAYS`, if collector logs show repeated `scheduled_refresh_failed` events, or if the refresh
  failure may have left public data inconsistent.

### Public CoinMarketCap download failure

- Where to look first: manual `download-cmc-csv` output, `data-collector` logs, and the staged incoming CSV directory.
- Check:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
podman-compose -f podman-compose.yml logs --tail=300 data-collector
find collector/btc-csv/incoming -maxdepth 1 -type f -print
tail -n 5 collector/btc-csv/btc_usd_daily.csv
```

- First safe action: do not hand-edit `collector/btc-csv/btc_usd_daily.csv`. Retry once after confirming the expected
  tail date. If the public endpoint is blocked or incomplete, stage an operator-downloaded CoinMarketCap CSV and run:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
curl -fsS http://127.0.0.1:3001/api/readiness
```

- Pause promotion or take public traffic down: pause promotion until the public download, manual CSV import, or optional
  API fallback completes and readiness is 200. Take public traffic down if the current public data is outside the
  accepted freshness window or the source range cannot be verified.

### Waitlist submission failure

- Where to look first: public waitlist response headers, backend access logs, backend error logs, Cloudflare security
  events for `POST /api/waitlist`, and `waitlist_leads` aggregate counts without copying contact values.
- An omitted or empty `turnstile_token` is an invalid request payload and returns `422` before Siteverify. A present
  token that is invalid, expired, replayed, wrong-action, or wrong-hostname returns `403`; unavailable Siteverify or
  incomplete server configuration returns `503`. None of these results may write a lead, and every result must be
  no-store.
- Check:

Use a real browser for the user-path smoke: it obtains the required single-use token from
`challenges.cloudflare.com`. Do not attempt a successful Turnstile smoke with curl. Curl with a non-empty invalid token
is useful only to confirm the expected rejected, no-store path and absence of a database write; default curl can also
match the repo-managed edge challenge and return Cloudflare `403` before the application.

```bash
PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
WAITLIST_TEST_CONTACT="<operator-controlled-test-contact>"
SMOKE_SOURCE="ops-smoke-$(date -u +%Y%m%d%H%M%S)"
curl -sD - -o /tmp/bitcoin-risk-waitlist.json \
  -H 'Content-Type: application/json' \
  -X POST "${PUBLIC_BASE_URL}/api/waitlist" \
  --data "{\"contact\":\"${WAITLIST_TEST_CONTACT}\",\"locale\":\"en\",\"source\":\"${SMOKE_SOURCE}\",\"turnstile_token\":\"invalid-turnstile-token\"}"
podman-compose -f podman-compose.yml logs --tail=200 backend
podman-compose -f podman-compose.yml exec timescaledb psql -U postgres -d bitcoin_risk_brief -t -A -c "SELECT count(*), max(created_at) FROM waitlist_leads WHERE source='${SMOKE_SOURCE}' AND contact_type='email' AND locale='en';"
```

Also check Cloudflare dashboard: Security Events filtered to hostname `bitcoinriskbrief.minihub.app` and path
`/api/waitlist`.

- First safe action: if the backend returns validation, rate-limit, or database errors, fix the backend or database cause
  before changing edge controls. If Cloudflare is challenging legitimate submissions, pause waitlist promotion and adjust
  only the waitlist-specific rule or bot mode after confirming normal page loads still work.
- Pause promotion or take public traffic down: pause promotion of the waitlist whenever submissions do not return a
  successful or documented duplicate/upsert response with `Cache-Control: no-store`. Take public traffic down if waitlist
  failures coincide with backend instability, database write failures, or an abuse burst that the current edge rules do
  not contain.

### Cloudflare Tunnel down

- Where to look first: public health, local health, Cloudflare Zero Trust tunnel connector status, and the active
  `cloudflared` service logs.
- Check:

```bash
PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
curl -sD - -o /tmp/bitcoin-risk-health-public.json "${PUBLIC_BASE_URL}/api/health"
curl -fsS http://127.0.0.1:3001/api/health
sudo systemctl status cloudflared --no-pager
sudo journalctl -u cloudflared -n 100 --no-pager
```

For a compose-managed connector, use:

```bash
podman-compose -f podman-compose.yml -f podman-compose.cloudflare.yml ps cloudflared
podman-compose -f podman-compose.yml -f podman-compose.cloudflare.yml logs --tail=100 cloudflared
```

Also check Cloudflare dashboard: Zero Trust > Networks > Tunnels > the tunnel serving
`bitcoinriskbrief.minihub.app`.

- First safe action: if local health is 200 and only the tunnel is down, restart the connector:

```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared --no-pager
```

For a compose-managed connector:

```bash
podman-compose -f podman-compose.yml -f podman-compose.cloudflare.yml restart cloudflared
podman-compose -f podman-compose.yml -f podman-compose.cloudflare.yml logs --tail=100 cloudflared
```

- Pause promotion or take public traffic down: pause promotion until public `/api/health` and `/api/readiness` pass
  through Cloudflare. If the connector flaps or cannot be restored quickly, keep the public hostname disabled instead of
  exposing the local frontend port.

### Public cache stale after import or correction

- Where to look first: readiness coverage, latest risk cache headers, backend cache version, and Cloudflare cache
  behavior for the public read endpoint.
- Check:

```bash
PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
curl -sD - -o /tmp/bitcoin-risk-readiness.json "${PUBLIC_BASE_URL}/api/readiness"
curl -sD - -o /tmp/bitcoin-risk-latest.json "${PUBLIC_BASE_URL}/api/risk/latest"
curl -sD - -o /tmp/bitcoin-risk-levels.json "${PUBLIC_BASE_URL}/api/risk/levels"
```

Expected readiness headers include `Cache-Control: no-store`. Expected cacheable public read headers include
`Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`; the latest timestamp should match readiness `covered_end`.

- First safe action: purge the single public hostname/API cache in Cloudflare when a previous product API response may
  already be cached at the edge. If readiness appears cached, treat that as an edge/origin configuration fault, correct
  the rule or header behavior, and recheck that `/api/readiness` is `no-store`. After purge, compare readiness with
  `/api/risk/latest`. Do not rerun imports solely to clear a stale edge cache.
- Pause promotion or take public traffic down: pause promotion if public `covered_end`, latest risk timestamp, or
  `X-Cache-Version` still points to the old validation marker after the cache window or a targeted purge. Take public
  traffic down if stale cache could show known-wrong data after a correction.

### Backup failure

- Where to look first: backup command output, backup directory contents, checksum file, TimescaleDB container state, and
  disk usage.
- Check:

```bash
./scripts/backup.sh --dry-run
BACKUP_LOG="/tmp/bitcoin-risk-backup-$(date -u +%Y%m%dT%H%M%SZ).log"
./scripts/backup.sh | tee "${BACKUP_LOG}"
tail -n 50 "${BACKUP_LOG}"
podman-compose -f podman-compose.yml ps timescaledb
df -h . ./data ./backups
```

- First safe action: if a backup directory was created, verify `SHA256SUMS` before trusting it:

```bash
BACKUP_PATH="<backup-directory-from-backup-log>"
test -s "${BACKUP_PATH}/SHA256SUMS"
(cd "${BACKUP_PATH}" && sha256sum -c SHA256SUMS)
```

If the failure is disk pressure, copy the latest verified backup off-server before pruning old timestamped backup
directories. Do not delete `./data/timescaledb`.

- Pause promotion or take public traffic down: pause migrations, deploys, bulk imports, and public launch until a fresh
  verified backup exists and has an off-server copy. Take public traffic down before any production restore or data
  repair from backup.

### Disk or database volume pressure

- Where to look first: host filesystem usage, `./data/timescaledb`, `./backups`, container restarts, and database size.
- Check:

```bash
df -h . ./data ./data/timescaledb ./backups
du -sh ./data/timescaledb ./backups collector/btc-csv
podman-compose -f podman-compose.yml ps
podman-compose -f podman-compose.yml exec timescaledb psql -U postgres -d bitcoin_risk_brief -t -A -c "SELECT pg_size_pretty(pg_database_size('bitcoin_risk_brief'));"
```

- First safe action: stop nonessential growth first. Pause manual imports and backups that are not needed for immediate
  recovery, copy verified backups off-server, and prune only old timestamped backup directories after checksum and
  off-server copy are confirmed. Never remove TimescaleDB files or canonical CSV files by hand.
- Pause promotion or take public traffic down: pause promotion when the project filesystem or database volume is above
  80% usage until capacity is confirmed. Take public traffic down if disk usage is above 90%, writes are failing, the
  database container is restarting, or readiness is non-200 due to storage pressure.

For suspected published bad-data incidents, use the bad-data correction policy above. For production imports, use the
production import provenance procedure above. Do not rely on raw logs, cache state, or memory as a substitute for a
source manifest and sanitized evidence packet.

## Database Checks

Check latest source/risk coverage:

```bash
podman-compose -f podman-compose.yml exec timescaledb   psql -U postgres -d bitcoin_risk_brief -t -A -c   "SELECT max(timestamp)::date, count(*) FROM btc_ohlcv_daily; SELECT max(timestamp)::date, count(*) FROM btc_risk_daily;"
```

Check validation source:

```bash
podman-compose -f podman-compose.yml exec timescaledb   psql -U postgres -d bitcoin_risk_brief -t -A -c   "SELECT validation_json->>'source', validation_json->'validation'->>'source_strategy', row_count FROM btc_risk_validation WHERE validation_key='latest';"
```

## Common Troubleshooting

### Readiness is degraded

Inspect `/api/readiness` and check which flag failed. Common causes:

- collector has not run;
- data is older than `DATA_FRESHNESS_MAX_AGE_DAYS`;
- validation source is not `coinmarketcap_csv`;
- latest risk timestamp does not match validation coverage end.

### Collector skips official API refresh

For `./scripts/manage.sh run-now`, an empty `COINMARKETCAP_API_KEY` means the official API refresh is skipped; the
collector still imports the existing CSV and recomputes risk.

For scheduled runs, an empty API key should not skip public no-key refresh when the CSV is stale. Inspect
`data-collector` logs for `public_cmc_download_started`, `public_cmc_download_success`, `public_cmc_download_failed`,
or `scheduled_refresh_failed`.

### Downloaded CSV import fails

The canonical CSV is preserved when a downloaded import fails. Common causes:

- the file was not staged under `collector/btc-csv/incoming/`;
- required columns such as `Date`, `Open`, `High`, `Low`, `Close`, `Volume`, or `Market Cap` are missing;
- the downloaded range skips one or more daily dates;
- the file ends before the existing canonical tail;
- `--expected-end-date` is later than the merged CSV tail.

### Collector fails on remote delta

A non-contiguous CoinMarketCap delta is rejected without rewriting the CSV. Inspect `data-collector` logs and rerun after the upstream data issue is resolved.

### TimescaleDB connection race

The collector wraps pool creation in retry logic, but if the database is unhealthy for longer than the retry window, fix the database container first:

```bash
podman-compose -f podman-compose.yml ps
podman-compose -f podman-compose.yml logs timescaledb
```

## Stopping Services

```bash
./scripts/manage.sh stop
```

This stops containers but keeps `./data/timescaledb` on disk.

## Related Docs

- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Production Readiness](production-readiness.md)
