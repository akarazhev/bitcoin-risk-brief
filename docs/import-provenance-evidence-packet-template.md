# Import Provenance Evidence Packet Template

This is a template, not completed evidence. It does not prove that a production refresh/import ran, does not prove the
source archive exists, and does not close the production import provenance launch gate by itself.

Use this packet to collect sanitized proof for a real production Bitcoin CSV refresh/import. Fill a working copy outside
Git first, in the operator-controlled evidence archive for that import. After review and redaction, copy only sanitized
final outcomes into launch docs such as [Production Readiness](production-readiness.md), [Operations](operations.md), or
the final launch snapshot packet.

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

## Safety Rules

- Record evidence summaries, basenames, timestamp basenames, hashes, row counts, dates, status values, and public
  endpoint/header facts only.
- Do not record private paths, raw source files, raw CSV rows, raw logs, raw backup contents, dashboard URLs, account
  IDs, tokens, `.env` values, waitlist contacts, private operator details, private recipient details, or other PII.
- Keep the complete source/archive packet outside the repository and outside the production project checkout.
- Do not infer production proof from repository CSV commits, helper scripts, cache state, or memory.
- Do not mark a gate `passed` unless the required real evidence exists, or explicitly record the missing item as an
  `accepted limitation`.

## Import Identity And Production Context

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Import ID or manifest ID.
- Import completion UTC timestamp or scheduled window.
- Production commit hash or short hash.
- Production deployment context, described without private paths.
- Import mode: scheduled public download, one-off public download, manual downloaded CSV import, optional API fallback,
  restore, or correction.
- Operator role or automation role, without personal details.

Acceptable sanitized wording examples:

- `Status: partial. Scheduled public-download-first import completed during the YYYY-MM-DD UTC update window; source archive review remains pending.`
- `Production context: deployed public pilot revision <commit> on the selected production path; no private host path recorded.`
- `Operator/automation: nightly collector automation.`

Do not record:

- Private filesystem paths, hostnames that are not already public, account IDs, operator names, email addresses, phone
  numbers, SSH targets, dashboard URLs, `.env` values, tokens, or raw command transcripts.

## Source/Archive Snapshot Evidence

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Source type: `automatic_public_cmc`, `manual_cmc_csv`, `optional_cmc_api`, `restore`, or `correction`.
- Source retrieval method summary.
- Archived source snapshot basename.
- Source SHA-256 digest.
- Source byte size.
- Source row count.
- Source covered start and covered end dates.
- Expected tail date.
- Retrieval started/completed UTC timestamps when available.

Acceptable sanitized wording examples:

- `Status: passed. Source snapshot source.csv was archived outside Git with SHA-256 <64-hex>, <row-count> rows, covering YYYY-MM-DD through YYYY-MM-DD.`
- `Status: accepted limitation. Retrieval timestamps were not preserved; operator accepted the limitation while source basename, hash, row count, and range were captured.`
- `Retrieval method: public CoinMarketCap Bitcoin historical data download, summarized without storing raw page output.`

Do not record:

- Raw source files, raw CSV rows, browser downloads directory paths, full archive paths, private backup paths, signed URLs,
  API keys, account details, raw page responses, raw backup contents, or unsanitized operator notes.

## Canonical CSV Output Evidence

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Canonical output basename or repository-relative canonical CSV identifier.
- Canonical CSV SHA-256 after import.
- Output row count.
- Output covered start and covered end dates.
- Tail date after import.
- Whether the output was produced by the production import, restore, or correction flow.

Acceptable sanitized wording examples:

- `Status: passed. Canonical output canonical-after.csv was captured after the production import with SHA-256 <64-hex>, <row-count> rows, tail date YYYY-MM-DD.`
- `Canonical identifier: collector/btc-csv/btc_usd_daily.csv; only sanitized range/hash metadata copied into Git.`
- `Status: partial. Canonical hash and tail date exist, but operator has not yet linked them to the matching source archive.`

Do not record:

- Raw canonical CSV contents, full production paths, raw backups, private archive roots, ad hoc workstation paths,
  database dumps, or local files that were not produced by the production import.

## Validation And Readiness Evidence

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Origin readiness status after import.
- Validation source and source strategy summary.
- Validation row count and covered end date.
- Risk range validation result.
- Latest risk date and risk state/value summary.
- Latest brief timestamp or sanitized absence statement.
- Evidence basename for readiness/validation payloads, if stored outside Git.

Acceptable sanitized wording examples:

- `Status: passed. Origin readiness returned ready; validation source coinmarketcap_csv covered YYYY-MM-DD with <row-count> rows and risk range validation true.`
- `Latest risk summary: latest date YYYY-MM-DD, risk state low, numeric risk in expected range.`
- `Status: accepted limitation. Direct validation-table query was unavailable; operator accepted public readiness plus manifest validation as the launch evidence for this import.`

Do not record:

- Raw JSON dumps with private fields, raw database query output containing private values, database connection strings,
  private host paths, credentials, `.env` values, full logs, or unrelated production records.

## Public Cache/Header Evidence

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Public base hostname or public endpoint category.
- Checked public endpoints.
- HTTP status summary.
- Required cache/header summary: `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`.
- Whether public latest-risk date matches readiness covered end.
- Cloudflare or edge cache status summary when available.
- Evidence basenames for public payload/header captures, if stored outside Git.

Acceptable sanitized wording examples:

- `Status: passed. Public readiness and latest-risk returned HTTP 200; latest risk date matched readiness covered_end YYYY-MM-DD; Cache-Control, ETag, X-Cache, and X-Cache-Version were present.`
- `Edge cache summary: repeat public read returned Cloudflare HIT; app X-Cache nuance remained documented.`
- `Status: partial. Public headers were captured, but edge repeat-cache behavior was not checked before the evidence window ended.`

Do not record:

- Private dashboard URLs, account IDs, Cloudflare tokens, request cookies, client IP addresses, raw access logs, full
  response dumps containing private data, or headers unrelated to public cache/readiness evidence.

## Collector/Import Log Summary

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Import command category or scheduler run category.
- Import start/end UTC timestamps when available.
- Collector outcome summary.
- Row count/range summary from logs or validation output.
- Error/warning summary if any.
- Evidence basename for the sanitized log summary, if stored outside Git.

Acceptable sanitized wording examples:

- `Status: passed. Scheduled collector run completed successfully; public download, validation, database import, risk recomputation, validation write, and stale-row cleanup all completed.`
- `Status: accepted limitation. Raw collector logs were not retained; operator accepted validation/readiness plus manifest evidence and recorded the missing log tail.`
- `Warning summary: no import errors observed; no raw log lines copied into Git.`

Do not record:

- Raw log dumps, private paths, environment variables, tokens, API keys, account IDs, waitlist contacts, IP addresses,
  private hostnames, raw exception traces containing secrets, or unrelated service logs.

## `scripts/import_provenance_packet.py` Manifest Result

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Manifest basename.
- Helper command category: `create`, `validate`, or manual manifest review.
- Helper result: passed, failed, pending, or unavailable.
- Manifest source type.
- Manifest source SHA-256.
- Observed row count and date range.
- Canonical tail date when present.
- Evidence file basenames included by the manifest.
- Production commit included by the manifest, if supplied.

Acceptable sanitized wording examples:

- `Status: passed. scripts/import_provenance_packet.py validate passed for manifest.json and source.csv; manifest source hash <64-hex> covered YYYY-MM-DD with canonical tail YYYY-MM-DD.`
- `Status: partial. Manifest was created, but validation against the archived source has not yet run.`
- `Status: accepted limitation. Helper unavailable on the production host; operator manually reviewed the same sanitized fields and recorded the exception.`

Do not record:

- Full manifest values that include private paths or private operator details, full command output with private paths,
  raw JSON payloads, source file contents, archive roots, `.env` values, account IDs, tokens, or private contact details.

## Known Limitations Or Accepted Operator Exceptions

Required sanitized fields:

- Status: one of `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.
- Limitation or exception name.
- Exact missing evidence or unavailable action.
- Operator decision: pending, blocked, or accepted limitation.
- Reason the limitation does or does not block the launch gate.
- Expiration or follow-up condition, if any.

Acceptable sanitized wording examples:

- `Status: accepted limitation. Direct production validation-table query was unavailable during the evidence window; operator accepted origin readiness, public cache/header evidence, manifest validation, and source archive proof for the watched pilot only.`
- `Status: blocked. Source snapshot was not archived, so production import provenance cannot be marked passed.`
- `Follow-up: collect direct validation-table metadata during the next production import.`

Do not record:

- Private operator names, private approval threads, account recovery details, dashboard URLs, credentials, personal
  contact details, raw internal chat logs, or legal/source-terms text that is not intended for the repository.

## Ready To Record?

The production import provenance gate can be marked `passed` only when the sanitized launch record is backed by real
source/archive evidence, canonical CSV output evidence, validation/readiness evidence, public cache/header evidence,
deployment context, and `scripts/import_provenance_packet.py` manifest evidence for the same production import. If any
item is missing, the gate remains `partial`, `pending`, or `blocked` unless an operator explicitly records the missing
item as an `accepted limitation`.

- [ ] Real source/archive snapshot exists outside Git, with sanitized basename, SHA-256, row count, covered range, and
      expected tail date recorded.
- [ ] Canonical CSV output after the production import is captured or summarized with sanitized hash, row count, range,
      and tail date.
- [ ] Validation/readiness evidence proves the imported data is the current production source of truth, or an explicit
      accepted limitation explains the gap.
- [ ] Public cache/header evidence proves the public read path reflects the same import, or an explicit accepted
      limitation explains the gap.
- [ ] Deployment context links the import to the production revision and import mode without private paths or operator
      details.
- [ ] `scripts/import_provenance_packet.py` manifest was created and validated against the archived source, or an
      explicit accepted limitation documents why equivalent manual manifest review was used.
- [ ] Known limitations are recorded with one of the allowed status values and do not silently upgrade missing evidence
      to `passed`.
