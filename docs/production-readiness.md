# Production Readiness

This document defines the current production-pilot gate for Bitcoin Risk Brief.

## Current Public Pilot Snapshot

Recorded on 2026-07-01 for `https://bitcoinriskbrief.minihub.app`:

- Cloudflare Rulesets API apply succeeded for the custom waitlist bot challenge, one waitlist rate-limit rule, waitlist
  cache bypass, and public-read origin-cache rules.
- The active Cloudflare plan required the Free-plan-compatible rate-limit settings:
  `--skip-managed-waf --waitlist-rate-limit-only --rate-limit-period 10 --rate-limit-mitigation-timeout 10`.
- `GET /api/health` returned 200 with `{"status":"ok"}`.
- `GET /api/readiness` returned 200 with `status: ready`, `source: coinmarketcap_csv`, `latest_date: 2026-06-30`,
  `covered_end: 2026-06-30`, and `row_count: 5832`.
- `GET /api/risk/latest` returned 200 with `X-Cache: HIT`.
- Conditional `GET /api/risk/latest` with `If-None-Match` returned 304 with `X-Cache: HIT`.

This snapshot confirms the public hostname, readiness path, and public-read cache behavior. It does not replace the
remaining launch checks: waitlist production smoke, browser/device QA on the public hostname, backup/restore setup,
alerts, and the first traffic test.

Additional public smoke evidence recorded on 2026-07-02 for `https://bitcoinriskbrief.minihub.app`:

- `GET /api/health` returned 200 with `{"status":"ok"}`.
- `GET /api/readiness` returned 200 with `status: ready`, `source: coinmarketcap_csv`, `latest_date: 2026-06-30`,
  `covered_end: 2026-06-30`, `data_age_days: 2`, `max_age_days: 2`, and `row_count: 5832`.
- `GET /api/risk/latest` returned 200 for timestamp `2026-06-30T00:00:00+00:00` with `Cache-Control: public,
  max-age=60, stale-while-revalidate=300`, `ETag: "a860789d405dbf015592328b"`, `X-Cache: MISS`, and
  `X-Cache-Version: validation:2026-07-02T01:00:05.718106+00:00:2026-06-30T00:00:00+00:00:5832:true`.
- The Cloudflare Free-plan limitation remains accepted for this pilot snapshot: the public edge is still using the
  Free-plan-compatible subset instead of managed WAF execution and broader API burst-rate-limit controls.

Deployment path decision status recorded on 2026-07-02:

- Selected deployment path: USB-based local-server deployment under `/srv/projects/bitcoin-risk-brief`, confirmed by
  the operator on 2026-07-02. The direct Git workflow under `/opt/bitcoin-risk-brief` is not the active production
  update path for the next update.
- Production project directory: `/srv/projects/bitcoin-risk-brief`.
- USB Update And Install Kit V2 is required before the next production update unless the operator records equivalent
  one-time manual verification before promotion.
- Production `.env` location: `/srv/projects/bitcoin-risk-brief/.env`; filesystem owner still needs production-host
  confirmation.
- Production `COINMARKETCAP_API_KEY`: empty. Data refresh should use the scheduled public-download-first collector path
  after this change is deployed to `/srv/projects/bitcoin-risk-brief`; `download-cmc-csv` and manual downloaded CSV
  intake remain operator fallbacks.

Backup, off-server copy, and restore drill status recorded on 2026-07-05:

- Real production backup was not run from this agent environment. The current workspace is a macOS workstation checkout;
  `/srv/projects/bitcoin-risk-brief` is not present here, and no production host, confirmed off-server storage target, or
  staging restore target is mounted or reachable from this session.
- Task 4 remains blocked pending operator action. Do not mark backup/off-server/restore complete until the operator
  records redacted evidence from the production host and a staging or intentionally empty restore target.
- On the production host, run:

```bash
set -euo pipefail
cd /srv/projects/bitcoin-risk-brief
git status --short --branch
BACKUP_LOG="/tmp/bitcoin-risk-backup-$(date -u +%Y%m%dT%H%M%SZ).log"
./scripts/backup.sh | tee "${BACKUP_LOG}"
BACKUP_PATH="$(awk '/^Backup complete:/ {print $3}' "${BACKUP_LOG}" | tail -n 1)"
test -n "${BACKUP_PATH}"
test -s "${BACKUP_PATH}"/postgres_*.dump
test -s "${BACKUP_PATH}"/btc_usd_daily_*.csv
test -s "${BACKUP_PATH}/manifest.txt"
test -s "${BACKUP_PATH}/SHA256SUMS"
(cd "${BACKUP_PATH}" && sha256sum -c SHA256SUMS)
```

- Copy the verified backup to the confirmed off-server storage. Set `OFFSERVER_BACKUP_ROOT` to the mounted off-server
  backup directory before running:

```bash
set -euo pipefail
BACKUP_PATH="<backup-directory-from-production-backup-step>"
OFFSERVER_BACKUP_ROOT="<mounted-off-server-backup-directory>"
case "${OFFSERVER_BACKUP_ROOT}" in
  ""|/srv/projects/bitcoin-risk-brief|/srv/projects/bitcoin-risk-brief/*)
    echo "OFFSERVER_BACKUP_ROOT must be outside the production project directory" >&2
    exit 2
    ;;
esac
install -d -m 700 "${OFFSERVER_BACKUP_ROOT}"
cp -a "${BACKUP_PATH}" "${OFFSERVER_BACKUP_ROOT}/"
OFFSERVER_BACKUP_PATH="${OFFSERVER_BACKUP_ROOT%/}/$(basename "${BACKUP_PATH}")"
test -s "${OFFSERVER_BACKUP_PATH}/SHA256SUMS"
(cd "${OFFSERVER_BACKUP_PATH}" && sha256sum -c SHA256SUMS)
```

- On a staging project checkout or intentionally empty restore target, run the restore drill with the copied backup:

```bash
set -euo pipefail
STAGING_PROJECT_DIR="<staging-or-empty-project-directory>"
RESTORE_BACKUP_PATH="<copied-backup-directory-on-staging>"
cd "${STAGING_PROJECT_DIR}"
test -s "${RESTORE_BACKUP_PATH}/SHA256SUMS"
(cd "${RESTORE_BACKUP_PATH}" && sha256sum -c SHA256SUMS)
./scripts/manage.sh start
podman-compose -f podman-compose.yml exec -T timescaledb pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  -U postgres \
  -d bitcoin_risk_brief < "${RESTORE_BACKUP_PATH}"/postgres_*.dump
cp "${RESTORE_BACKUP_PATH}"/btc_usd_daily_*.csv collector/btc-csv/btc_usd_daily.csv
./scripts/manage.sh run-now
curl -fsS http://127.0.0.1:3001/api/readiness
```

- Record only redacted evidence: command date, production commit, backup artifact categories, checksum verification
  result, off-server copy confirmation, restore target type, and readiness result. Do not record `.env` values,
  secrets, waitlist contacts, raw dump or CSV contents, or private off-server paths.

Monitoring and first-response status recorded on 2026-07-05:

- Overall monitoring status: blocked/accepted limitation for first traffic. The first-response runbook is documented in
  [Operations](operations.md), and previous public smoke checks prove the public health/readiness paths exist, but this
  agent session has no access to the production host, Cloudflare dashboard, or an external monitoring provider. No
  monitor dashboard, alert delivery, backup freshness monitor, collector log alert, or Cloudflare Tunnel health alert
  evidence was provided. Do not mark monitoring configured until an operator records redacted evidence.

| Monitor area | Current status | Required operator action |
| --- | --- | --- |
| Public `/api/health` | Blocked/accepted limitation. Endpoint exists and has previous smoke evidence, but no external uptime monitor evidence is recorded. | Configure an HTTP monitor for `https://bitcoinriskbrief.minihub.app/api/health`, alert on non-200, timeout, or TLS failure, and record the provider/dashboard name plus alert channel without account details. |
| Public `/api/readiness` | Blocked/accepted limitation. Endpoint exists and has previous smoke evidence, but no external readiness alert evidence is recorded. | Configure an HTTP monitor for `https://bitcoinriskbrief.minihub.app/api/readiness`, alert on non-200, and route the alert to the `/api/readiness` first-response entry in `docs/operations.md`. |
| Stale readiness after nightly update window | Blocked/accepted limitation. No scheduled stale-data monitor evidence is recorded. | After the default 01:00 UTC collector window plus operator-defined grace period, check `/api/readiness`; alert if `status` is not `ready`, `latest_date`/`covered_end` is older than the last completed UTC day, or `data_age_days` exceeds `DATA_FRESHNESS_MAX_AGE_DAYS`. |
| Collector refresh failure | Blocked/accepted limitation. The scheduled public-download-first path is documented, but no production log alert evidence is recorded. | Configure production log/container alerts for `scheduled_refresh_failed`, `public_cmc_download_failed`, API fallback failure, and repeated `data-collector` restarts; record the alert source and latest passing scheduled run. |
| Backup freshness | Blocked by Task 4 and accepted only as a documented limitation until the operator acts. No real production backup, off-server copy, restore drill, or backup freshness monitor evidence is recorded here. | Schedule `./scripts/backup.sh`, copy verified backups off-server, alert when no checksum-verified backup and off-server copy exists inside the chosen freshness window, and record redacted evidence from the production host. |
| Cloudflare Tunnel health | Partially configured. The public hostname and Tunnel path have previous smoke evidence, but no Cloudflare connector health alert evidence is recorded. | In Cloudflare Zero Trust, enable or document Tunnel connector health notifications for the connector serving `bitcoinriskbrief.minihub.app`; also record whether production uses host-service `cloudflared` or compose-managed `cloudflared` and where operators check status. |

- Until the actions above are complete, public traffic should be a controlled operator-watched pilot only. Pause broader
  promotion when any required monitor is missing and no operator is actively watching the matching command/dashboard from
  the first-response runbook.

Import provenance and bad-data correction status recorded on 2026-07-05:

- Task 6 status: blocked pending operator evidence for the real production import evidence packet. The operator
  procedure and bad-data correction policy are documented in [Operations](operations.md), and the data-pipeline
  provenance contract is documented in [Data Pipeline](data-pipeline.md).
- Real sample import evidence packet: not present in this repository and not created from this agent environment. This
  session has no access to the production host at `/srv/projects/bitcoin-risk-brief`, no mounted outside-repository
  provenance archive, and no Cloudflare/production host evidence source. A workstation-local or repository-local sample
  would not prove production import provenance, so it should not be recorded as completion evidence.
- Current accepted limitation: first traffic can only proceed as an operator-watched pilot if this missing evidence is
  explicitly accepted. Do not mark provenance complete until a sanitized packet for a real production import exists
  outside the repository and references readiness and cache evidence.
- Exact operator actions needed on the production host:

```bash
cd /srv/projects/bitcoin-risk-brief
git status --short --branch
git rev-parse HEAD
export PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
export IMPORT_ARCHIVE_ROOT="<outside-repository-import-evidence-root>"
test -n "${IMPORT_ARCHIVE_ROOT}"
case "${IMPORT_ARCHIVE_ROOT}" in
  /srv/projects/bitcoin-risk-brief|/srv/projects/bitcoin-risk-brief/*) exit 2 ;;
esac
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
curl -fsS http://127.0.0.1:3001/api/readiness
curl -sD - -o /tmp/bitcoin-risk-latest-public.json "${PUBLIC_BASE_URL}/api/risk/latest"
```

- After the import command above, follow the `Production Import Provenance` procedure in [Operations](operations.md):
  copy the source snapshot and canonical CSV under the per-import archive directory, calculate `sha256` and
  row/date-range evidence, save origin readiness and public cache headers, create `manifest.json`, link any
  launch/restore/correction note, and inspect the packet for forbidden data.
- Sensitive data rule for the evidence packet: do not include `.env` values, API keys, Cloudflare tokens, waitlist
  contacts, raw analytics, browser profiles, private account exports, or other PII.
- Bad-data correction posture: documented for the pilot with low/medium/high classification, observe/inspect/freeze,
  known-good restore or re-import, risk/brief recomputation, origin and edge cache verification, correction notes, and
  internal freshness/RPO/RTO/downtime boundaries. These are internal pilot targets, not public SLA commitments.

Production waitlist smoke status recorded on 2026-07-05:

- Public endpoint for the smoke: `POST https://bitcoinriskbrief.minihub.app/api/waitlist`.
- Waitlist submission was not performed from this agent environment because no operator-controlled test contact value or
  other private contact handoff was available. Using a placeholder would not satisfy the Task 7 contact constraint.
- HTTP saved/upsert status: blocked/not collected because no waitlist submission was sent.
- Cache header result: blocked/not collected. `Cache-Control: no-store` and optional `Pragma: no-cache` still need
  verification on a successful or duplicate/upsert waitlist response.
- Server-side storage verification: blocked from this workstation. `/srv/projects/bitcoin-risk-brief` is not present and
  no safe production database access was available, so `waitlist_leads` was not queried.
- Contact value is intentionally omitted from this document and must also be omitted from logs summaries, final reports,
  screenshots, and commit messages.

Browser and device QA status recorded on 2026-07-05:

- Automated frontend checks completed: `npm test --prefix frontend` passed 2 files / 17 tests;
  `npm run build --prefix frontend` passed; `npm run smoke --prefix frontend` was first blocked in the sandbox by
  `listen EPERM: operation not permitted 127.0.0.1:4173`, then passed 15 Playwright checks when rerun outside the
  sandbox.
- Public-hostname browser-capable QA was performed against `https://bitcoinriskbrief.minihub.app/` with Playwright
  desktop Chromium, mobile Chromium Pixel 5, and mobile WebKit iPhone 13 profiles. The page loaded, latest risk was
  visible, readiness/freshness was visible, both chart canvases were non-empty, the waitlist form was visible, EN/RU
  switching worked, and mobile checks found no horizontal overflow or obvious text overlap in saved screenshots.
- Launch-gate result: browser-capable public-hostname rendering passes with limitations, but broader launch remains
  blocked/limited by degraded data freshness shown on the public page (`2026-06-30`, `4 days old`) and by the missing
  physical device/native branded browser pass. No production waitlist submission was sent as part of this Task 8 pass.

Launch governance and release evidence status recorded on 2026-07-05:

- Launch snapshot commit: `f42f266542981483a87964fa8726a5513eb339d6`. This is a snapshot target only, not a
  production-ready or launch-ready declaration because current readiness is degraded.
- Methodology version: `crypto-scout-canonical-v1`.
- Selected data refresh path: scheduled public-download-first CoinMarketCap CSV refresh with manual
  `download-cmc-csv` or `import-cmc-csv` fallback. The optional official CoinMarketCap API path is used only when
  `COINMARKETCAP_API_KEY` is configured.
- Known accepted limitations for the current candidate: no standalone privacy/terms page is recorded; waitlist lead
  owner, review cadence, deletion/unsubscribe contact path, and support/contact identity are pending operator decisions;
  production backup/off-server copy/restore evidence is missing; monitoring evidence is missing; production import
  provenance evidence is missing; waitlist smoke was not run; public page data was observed stale during Task 8; full
  native-device/browser QA, focused accessibility, and SEO/social metadata evidence are not complete; Cloudflare remains
  on the documented Free-plan-compatible subset.
- Governance evidence process: keep privacy/terms/disclaimer posture, waitlist handling, credential/account ownership,
  data-source terms review, dependency/security maintenance, accessibility, and metadata status in
  [Security and Privacy](security-and-privacy.md) and [Operations](operations.md). Unknown operator-owned facts must be
  recorded as pending decisions, not guessed.
- First-user feedback review path: after the first controlled traffic window, summarize waitlist conversion,
  repeat-use signals, direct questions, methodology confusion, and requests for alerts, daily briefs, API access,
  agents, embeddings, widgets, or commercial reuse into this document or [Production Roadmap](production-roadmap.md).
  Do not copy raw waitlist contacts into feedback notes.
- Support/contact identity status: pending operator decision. One operator-owned contact path is required before
  broader sharing, but no public support portal, paid SLA, or guaranteed response time is implied for the first pilot.
- Dependency-license review status: pending lightweight review. Before broader portfolio sharing or commercial claims,
  review production Python and npm dependency licenses for obvious conflicts and record the repository posture. Do not
  claim open-source status unless a license is intentionally chosen.
- Release evidence packet process: the final launch snapshot should reference the launch commit, public hostname,
  readiness payload, cache headers, selected refresh path, deployment path, backup/restore evidence, waitlist smoke,
  browser QA, known limitations, and any related import provenance manifest. Store private artifacts, raw contacts,
  secrets, account details, and private storage paths outside this repository.

Task 10 launch snapshot recorded on 2026-07-05 at 11:37 UTC for `https://bitcoinriskbrief.minihub.app`:

- Repository state: `git status --short --branch` returned `## main...origin/main`, and `git rev-parse HEAD` returned
  `f42f266542981483a87964fa8726a5513eb339d6`. No commit or push was performed for this snapshot.
- Public health: `GET /api/health` returned HTTP 200 with `status: ok`.
- Public readiness: `GET /api/readiness` returned HTTP 503 with `status: degraded`. All readiness checks were true
  except `data_fresh: false`; the payload reported `latest_date: 2026-06-30`, `covered_end: 2026-06-30`,
  `data_age_days: 4`, `max_age_days: 2`, `source: coinmarketcap_csv`, `row_count: 5832`, and
  `methodology_version: crypto-scout-canonical-v1`.
- Latest BTC data and risk: `GET /api/risk/latest` returned HTTP 200 for timestamp `2026-06-30T00:00:00+00:00` with
  `risk_state: low` and risk approximately `0.2860`. The latest BTC data date remains `2026-06-30`, so production data
  freshness blocks launch.
- Cache headers: public readiness and latest-risk responses included `Cache-Control: public, max-age=60,
  stale-while-revalidate=300`, `ETag`, `X-Cache`, and `X-Cache-Version`. The readiness response used
  `ETag: "e794a17b08b6404888453563"`, `X-Cache: MISS`,
  `X-Cache-Version: validation:2026-07-04T01:00:05.639122+00:00:2026-06-30T00:00:00+00:00:5832:true`, and
  `cf-cache-status: STALE`. The latest-risk response used `ETag: "0b452ec072778d840d5ed64d"`, `X-Cache: MISS`,
  `X-Cache-Version: validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true`, and
  `cf-cache-status: UPDATING`.
- Waitlist smoke status: blocked/not collected. No operator-controlled test contact was available, no public waitlist
  submission was sent, and server-side storage was not verified.
- Browser QA status: browser-capable public-hostname QA passed with accepted limitations. The public page rendered in
  Playwright desktop Chromium, mobile Chromium, and mobile WebKit profiles, but it visibly showed stale data and no
  physical-device/native branded browser pass is recorded.
- Selected deployment path: USB-based local-server deployment under `/srv/projects/bitcoin-risk-brief`; USB Update And
  Install Kit V2 or equivalent one-time manual verification remains required before the next production update, and the
  production `.env` owner still needs host confirmation.
- Selected data refresh path: scheduled public-download-first CoinMarketCap CSV refresh, with manual
  `download-cmc-csv` and `import-cmc-csv` fallbacks. The current public readiness result proves this path has not kept
  production fresh through the accepted freshness window and needs operator action before launch.
- Backup/restore evidence status: blocked pending operator evidence. No real production backup, off-server copy, restore
  drill, or backup freshness monitor is recorded.
- Monitoring status: blocked/accepted limitation. Public endpoints exist, but no external monitor dashboard, alert
  delivery, collector failure alert, backup freshness alert, or Cloudflare Tunnel health alert evidence is recorded.
- Import provenance status: blocked pending operator evidence. No sanitized production import evidence packet is recorded
  outside the repository.
- Accepted limitations/blockers: Cloudflare remains on the documented Free-plan-compatible subset; waitlist smoke,
  backup/off-server/restore, monitoring, production import provenance, physical/native browser QA, support/contact
  identity, dependency-license review, and focused accessibility/SEO metadata evidence remain incomplete. The launch
  blocker for this snapshot is data freshness: readiness is HTTP 503 with `data_fresh: false`. Do not run or mark the
  first traffic test complete until readiness is HTTP 200 and the other required launch limitations are explicitly
  resolved or accepted.

Task 11 cache latency measurement recorded on 2026-07-05 from 12:15 to 12:17 UTC for
`https://bitcoinriskbrief.minihub.app`:

- Measurement context: production readiness was degraded during this pass. `GET /api/readiness` returned HTTP 503 with
  `status: degraded`, `data_fresh: false`, `latest_date: 2026-06-30`, `covered_end: 2026-06-30`, `data_age_days: 4`,
  `max_age_days: 2`, `source: coinmarketcap_csv`, and `row_count: 5832`. This measurement is useful for cache-latency
  evidence, but it does not close the launch blocker and must be repeated after production data freshness is restored.
- Commands used `curl -sS -D - -o /tmp/... -w 'time_total=%{time_total}\n'` against the public hostname. Initial sandbox
  DNS resolution failed, so the public curl checks were rerun with network access for the measurement.

| Endpoint | HTTP | X-Cache | X-Cache-Version | Cache-Control | First observed `time_total` | Repeat behavior |
| --- | --- | --- | --- | --- | --- | --- |
| `/api/readiness` | 503 | `MISS` | `validation:2026-07-04T01:00:05.639122+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `0.579072s` | Repeats stayed `X-Cache: MISS` with Cloudflare `STALE`; observed `0.223646s` to `0.293653s`. |
| `/api/risk/latest` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `15.720018s` | Repeats were fast through Cloudflare (`HIT` or `UPDATING`) at `0.156413s` to `0.182181s`, but the public response still exposed cached origin `X-Cache: MISS`. |
| `/api/risk/history?limit=2000` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `0.502109s` | Repeats stayed under `0.37s` through Cloudflare (`HIT` or `UPDATING`), with cached origin `X-Cache: MISS`. |
| `/api/risk/levels` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `16.289584s` | Repeats were fast through Cloudflare (`HIT` or `UPDATING`) at `0.155345s` to `0.184155s`, but the public response still exposed cached origin `X-Cache: MISS`. |
| `/api/brief/latest` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `0.291438s` | Repeats were fast through Cloudflare (`HIT` or `UPDATING`) at `0.159051s` to `0.170369s`, with cached origin `X-Cache: MISS`. |

- Backend `X-Cache: HIT` behavior was not directly observable from the public Cloudflare path in this pass. Repeated
  requests showed fast Cloudflare edge behavior, but the response header continued to expose the cached origin
  `X-Cache: MISS` value.
- Slow MISS/revalidation was observed for `/api/risk/levels` and `/api/risk/latest`. `/api/risk/levels` is one of the
  documented expensive first-miss candidates, so a separate implementation plan should be created for local public cache
  warmup before active traffic. Do not implement warmup inside this Task 11 documentation-only measurement.
- Cache warmup remains a pre-traffic recommendation: warm `/api/readiness`, `/api/risk/latest`,
  `/api/risk/history?limit=2000`, `/api/risk/levels`, and `/api/brief/latest` after backend startup and after successful
  import/validation-version changes. Warmup must not hide stale readiness, and it must preserve `X-Cache-Version`
  invalidation.

## Release Gates

Run these before every deploy:

```bash
./scripts/manage.sh test-python
python3 -m compileall backend collector
npm test --prefix frontend
npm run build --prefix frontend
npm run smoke --prefix frontend
./scripts/manage.sh validate
podman-compose -f podman-compose.yml build backend data-collector frontend
./scripts/manage.sh run-now
python3 scripts/cloudflare_edge_rules.py render --hostname risk.example.com > /tmp/bitcoin-risk-cloudflare-edge.json
```

If a one-off production refresh is needed before the scheduled collector has run, use the no-key public CoinMarketCap
path before the final readiness check:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
```

If the public endpoint automation is unavailable, stage a manually downloaded CSV and run:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
```

After services are running, verify:

```bash
curl -fsS http://localhost:3001/api/health
curl -fsS http://localhost:3001/api/readiness
```

Also verify latest risk and risk levels are consistent:

```bash
python3 - <<'PY'
import json
from urllib.request import urlopen
latest = json.load(urlopen('http://localhost:3001/api/risk/latest'))['data']
levels = json.load(urlopen('http://localhost:3001/api/risk/levels'))
print(abs(latest['risk'] - levels['meta']['current_risk']))
PY
```

Verify public read cache headers and conditional revalidation:

```bash
curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest
ETAG="$(curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest | awk 'BEGIN{IGNORECASE=1} /^etag:/ {print $2}' | tr -d '\r')"
curl -s -o /dev/null -w "%{http_code}\n" -H "If-None-Match: ${ETAG}" http://localhost:3001/api/risk/latest
```

The first response should include `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`. The conditional request
should print `304`.

Before public launch, also complete and record:

- browser/device QA for the launch matrix;
- selected BTC data refresh path: automatic public CSV download, manual downloaded CSV intake, or optional CoinMarketCap API refresh;
- selected deployment path: direct Git workflow or USB-based local-server deployment. If USB deployment is used, verify
  the kit contains a filtered project snapshot, server-kit scripts, docs, manifest, and checksums, and does not contain
  local `.env`, `.git`, backups, dependency caches, build output, or container images;
- cache policy for public read endpoints;
- Cloudflare WAF, bot protection, cache rules, and edge rate limits rendered and applied with
  `scripts/cloudflare_edge_rules.py`, plus dashboard bot protection enabled where required by the Cloudflare plan;
- launch operations and governance posture: privacy/terms/disclaimer copy, post-waitlist handling, dependency/security
  maintenance cadence, credential/account ownership, resource monitoring, data-source terms, accessibility, metadata,
  and incident response notes;
- release feedback and operational evidence posture: release notes or decision log, first-user feedback review path,
  support/contact identity, dependency-license review, and launch/backup/restore evidence;
- data correction and service-target posture: bad CSV/import/risk correction flow, correction-note rules, cache
  correction safety, freshness target, RPO/RTO boundaries, and pilot downtime tolerance;
- import provenance and source archive posture: source snapshot, import manifest, `sha256`, retrieval metadata, row
  count, covered range, expected tail, validation/readiness output, cache evidence, and storage outside the repository;
- documentation hygiene pass across roadmap, data pipeline, security, testing, operations, and deployment docs;
- after implementation freeze, a private/portfolio presentation pass covering the root README, docs index, sibling
  product-ideas brief, GitHub description/topics, optional screenshot or GIF, and repository hygiene.

## Production Environment

Start from `.env.production.example`, not `.env.example`.

Required production changes:

- Set `APP_ENV=production`.
- Replace `DB_PASSWORD` with a long random value.
- Set `CORS_ORIGINS` to the public HTTPS domain only.
- Keep `FRONTEND_BIND_IP=127.0.0.1` when Cloudflare Tunnel is the only ingress.
- Set `COINMARKETCAP_API_KEY` only if the optional API refresh path is used.
- If no paid CoinMarketCap API account is available, use the documented automatic or manual public CSV workflow and leave
  `COINMARKETCAP_API_KEY` empty intentionally.
- Keep `DATA_FRESHNESS_MAX_AGE_DAYS=2` unless the product explicitly accepts slower updates.
- Tune `WAITLIST_RATE_LIMIT_PER_HOUR` for expected traffic.
- Keep the public cache defaults unless launch testing shows a reason to tune them:
  `PUBLIC_CACHE_TTL_SECONDS=300`, `PUBLIC_CACHE_MAX_AGE_SECONDS=60`, and
  `PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS=300`.

## Readiness Contract

`/api/readiness` returns HTTP 200 only when:

- latest risk data exists;
- validation data exists;
- validation row count is positive;
- risk range validation passed;
- latest risk timestamp matches validation coverage end;
- validation source is `coinmarketcap_csv`;
- data age is within `DATA_FRESHNESS_MAX_AGE_DAYS`.

A non-200 readiness response should block deploy promotion and should alert in production.

## Data Pipeline Guarantees

- `collector/btc-csv/btc_usd_daily.csv` is the canonical source.
- Scheduled collector runs target the last completed UTC day. If the CSV is stale, they use public CoinMarketCap
  download first and fall back to the optional official API delta refresh only when `COINMARKETCAP_API_KEY` is
  configured.
- If the CSV already covers the scheduled target date, the collector imports and recomputes from the existing CSV
  without downloading.
- The production-pilot path supports automatic public CoinMarketCap downloads and validated imports from
  operator-downloaded CoinMarketCap historical CSVs.
- Remote deltas, public downloads, and downloaded CSV imports must exactly match the expected contiguous daily range.
- Non-contiguous or invalid inputs fail without rewriting the canonical CSV.
- CSV writes use atomic replace.
- Every import recalculates all risk rows and removes DB rows after the CSV tail.

## Performance And Caching Gate

Before public traffic, verify the implemented cache policy for public read endpoints:

- latest risk;
- risk history;
- risk levels;
- daily brief;
- readiness.

These endpoints should return `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`. Backend cache invalidation is
versioned from `btc_risk_validation`; after a successful import, the collector rewrites validation and the next backend
read rebuilds against the new version. `POST /api/waitlist` must return `Cache-Control: no-store` and must not be cached
by Cloudflare.

Before active traffic, measure first-load latency for both backend `X-Cache: MISS` and `X-Cache: HIT` responses on the
public hostname. If the first miss after backend startup or nightly import is user-visible, implement public payload
cache warmup for the standard endpoint set and consider precomputing expensive payloads such as `/api/risk/levels`.
Warmup must preserve `X-Cache-Version` invalidation and must not hide stale readiness.

At the Cloudflare edge, respect origin cache headers for the public GET API paths and bypass `/api/waitlist`. If a launch
snapshot must reflect a just-completed import immediately, purge the public hostname or wait for
`PUBLIC_CACHE_MAX_AGE_SECONDS`.

## Security Controls

- Public responses include baseline security headers at the nginx entrypoint.
- Backend responses also set API-safe security headers.
- `POST /api/waitlist` uses input validation, parameterized SQL, and an in-memory per-client rate limit.
- Waitlist contacts are stored server-side only.
- The frontend does not persist submitted contacts in browser storage.
- Cloudflare WAF managed rules, edge rate limits, cache rules, and repo-managed waitlist bot challenge should be active
  before public traffic when the active Cloudflare plan is entitled to run them. Render/apply them with
  `scripts/cloudflare_edge_rules.py`. If the zone is on a Free plan, use the documented Free-plan-compatible subset and
  record the accepted limitation before first traffic.
- Cloudflare Bot Fight Mode, Super Bot Fight Mode, or equivalent dashboard bot protection should be enabled after the
  script is applied and smoke-tested.
- Initial Cloudflare limits should protect `POST /api/waitlist` at 5 requests per minute per IP and `/api/*` at 120
  requests per minute per IP, adjusted only after reviewing real traffic.
- Abuse smoke checks should confirm bursty waitlist/API traffic is challenged, blocked, or rate-limited without breaking
  normal page use.

## Browser And Device Gate

Before public traffic, verify the page on current desktop Chrome, Safari, Firefox, mobile Safari, and mobile Chrome. The
check should cover loading, degraded readiness, API errors, chart rendering, waitlist states, enabled-locale behavior,
localized copy fit, first-viewport price model input labels, and common mobile/desktop viewport widths.

The automated frontend smoke matrix and current results are recorded in [Frontend QA](frontend-qa.md). Treat that as the
minimum automated check; repeat a short manual pass on the production hostname before public launch.

If the Phase 8 localization add-on is implemented before active traffic, include English, Russian, Spanish, and German in
the browser/device pass. Arabic and Chinese should remain disabled until their separate right-to-left, Simplified versus
Traditional, platform, and channel requirements are documented and tested.

## Remaining External Operations

These are operational tasks outside this repository.

Completed or partially completed as of 2026-07-01:

- Cloudflare Tunnel/public hostname is serving `https://bitcoinriskbrief.minihub.app`.
- Public `/api/health`, `/api/readiness`, `/api/risk/latest`, and conditional `/api/risk/latest` checks pass through
  Cloudflare.
- Cloudflare edge cache settings and the waitlist-specific rate-limit/custom challenge subset were applied with
  `scripts/cloudflare_edge_rules.py`.

Still required before treating the pilot as publicly launched:

- Confirm the production host runbook, `.env`, service path, and selected data-refresh workflow.
- If the production host is updated through USB, replace manual copying with the planned USB Update And Install Kit V2 or
  record the manual verification evidence until that script exists.
- Decide whether to accept the current Cloudflare Free-plan subset for first traffic or upgrade/configure additional WAF,
  bot protection, and broader API burst-rate-limit controls.
- Configure scheduled `./scripts/backup.sh` runs and copy backups off the server.
- Deploy and verify scheduled public-download-first refresh on the production host because the production pilot runs
  without a `COINMARKETCAP_API_KEY`.
- Put request logging, backup health, and operational review in place.
- Configure alerts on `/api/readiness` returning non-200, readiness becoming stale after the nightly update window, or
  collector logs containing scheduled/public/API refresh failures.
- Complete a short browser/device QA pass on the public hostname.
- Submit a deliberate test waitlist lead and verify it is stored server-side without caching the response.
- Complete or explicitly defer the launch operations and governance checklist: privacy/terms, post-waitlist handling,
  credential ownership, resource monitoring, dependency/security maintenance, data-source terms, accessibility,
  SEO/social metadata, and incident response.
- Complete or explicitly defer the release feedback and operational evidence checklist: release notes or decision log,
  first-user feedback path, support/contact identity, dependency-license review, and launch/backup/restore evidence.
- Keep the documented bad-data correction and service-target policy current as real restore/import evidence arrives;
  pilot freshness, RPO/RTO, correction, and downtime targets remain internal targets, not public SLA promises.
- Capture a real production import evidence packet outside the repository: source snapshot, import manifest, `sha256`,
  retrieval metadata, row count, covered range, expected tail, validation/readiness output, cache evidence, and any
  related launch, restore, or correction note.
- Complete the documentation and portfolio presentation pass, including the sibling product-ideas brief, if the
  repository will be shown as a private/portfolio project.
- Capture the launch snapshot and run the first small traffic test.

## Related Docs

- [Architecture](architecture.md)
- [Data Pipeline](data-pipeline.md)
- [Security and Privacy](security-and-privacy.md)
- [Operations](operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Testing and Quality](testing-and-quality.md)
