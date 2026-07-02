# Import Provenance And Source Archive

> Status: future-facing. Last reviewed 2026-07-02. This is a Phase 7/8 operational readiness gate for production-pilot
> data imports, not a full audit platform.

## Context

The product depends on a canonical BTC/USD daily CSV. Imports validate the CSV, replace the canonical file only after
validation succeeds, recompute the full risk series, write validation metadata and the latest brief, and delete derived
rows after the CSV tail.

The correction policy explains how to handle a published bad-data incident. To make that policy useful, the operator
also needs evidence for each production import: which source file was used, where it came from, when it was retrieved,
what hash it had, what date range it covered, and which validation output it produced.

Without import provenance, a correction note can say that data was fixed, but it cannot confidently prove which input
caused the issue or which source was used to repair it.

## Goal

Define a lightweight source archive and import evidence model for production-pilot BTC data imports.

The operator should be able to answer:

- which file or download was imported;
- when and how the source was retrieved;
- what `sha256` hash identified the imported source;
- how many rows and which date range were present;
- which expected tail date was requested;
- which command, commit, and environment performed the import;
- which validation version, readiness payload, and cache evidence resulted;
- where the source snapshot and manifest are stored.

## Non-Goals

- Do not build a full audit dashboard.
- Do not expose provenance through the public API before a separate implementation design.
- Do not store secrets, API keys, waitlist contacts, raw request logs, or PII in provenance files.
- Do not mirror all vendor data or create a full data-vendor reconciliation system.
- Do not make public/downloaded CoinMarketCap data look more authoritative than the terms and source quality support.
- Do not block manual imports during the pilot if the operator captures equivalent evidence.

## Recommended Approach

Use a small import evidence packet for each production import:

1. Source snapshot.
2. Import manifest.
3. Validation/readiness evidence.
4. Cache evidence after import.
5. Link to any launch, correction, or restore note.

This can start as an operator procedure and later become automated in collector scripts. Manual evidence is acceptable
for the first production pilot as long as it is consistent and stored outside the repository.

## Source Snapshot

For each production import, preserve the exact source input when practical:

- automatic public download: staged CSV produced under `collector/btc-csv/incoming/`;
- manual CSV: the operator-downloaded CoinMarketCap CSV before normalization or merge;
- optional API refresh: the canonical CSV before and after the refresh, plus request date range metadata;
- correction import: the known-good CSV or backup source used for repair.

The archive should keep source files outside the Git repository, for example under an off-server backup or an operator
archive directory. It should not include `.env`, API keys, browser profiles, Cloudflare tokens, waitlist contacts, or
analytics events.

## Import Manifest

Each source snapshot should have a small text or JSON manifest with:

- import timestamp in UTC;
- operator or automation identity;
- git commit;
- command used;
- source type: `automatic_public_cmc`, `manual_cmc_csv`, `optional_cmc_api`, `restore`, or `correction`;
- source URL or retrieval method;
- local staged source path;
- source file `sha256`;
- source file byte size;
- source row count;
- covered start date;
- covered end date;
- expected tail date;
- canonical CSV path after import;
- canonical CSV `sha256` after import;
- validation row count;
- validation covered end;
- methodology version;
- readiness status after import;
- related launch, correction, or restore note path if any.

The manifest is operator evidence, not a secret. Still, it should be reviewed before external sharing because file paths
or operator names may reveal local environment details.

## Validation And Readiness Evidence

After the import, capture:

- `/api/readiness` payload;
- latest risk payload or at least latest date, risk value, and methodology version;
- latest brief snapshot timestamp if available;
- `ETag`, `X-Cache`, and `X-Cache-Version` for a standard public endpoint;
- collector log summary for the import;
- any warning or accepted limitation.

This evidence should reference the manifest rather than duplicate the full source file contents.

## Retention

For the pilot, keep at least:

- the latest known-good production source snapshot;
- the source snapshot used for launch;
- any source snapshot involved in a correction;
- manifests for production imports during the first traffic test;
- the latest restore-drill source/backup evidence.

Long-term retention can be reduced after the product learns its real usage pattern, but correction-related evidence
should be kept longer than ordinary successful import evidence.

## Integration With Correction Policy

The bad-data correction flow should use provenance evidence to identify:

- the source that introduced the issue;
- the first public validation version affected;
- the last known-good source;
- whether a backup contains the bad data;
- whether the corrected import changed the latest risk value or only metadata/cache state.

If provenance is missing, the correction note should say so explicitly and rely on available backup, readiness, and
operator evidence.

## Integration With Future Research And Licensing

If the risk metric is later licensed, used by agents, or compared against a v2 methodology, provenance becomes more
important. A professional or agent-facing risk signal should not depend on untraceable production inputs.

Future research datasets should record retrieval date, source URL, terms, hash, covered range, and transformation notes
before being used for methodology comparison.

## Error Handling

If a source file cannot be archived, keep the manifest and record the reason.

If the source hash cannot be reproduced, do not treat the import as strong evidence for a correction or research
comparison.

If the manifest contains secrets or PII, delete that manifest from the archive, recreate a sanitized one, and inspect why
the capture process included sensitive data.

If automatic provenance capture later fails, the import may still proceed for the free pilot only if the operator records
manual evidence and the data validation passes.

## Testing And Verification

Before broader traffic, verify the procedure without needing a full implementation:

- produce one sample import manifest for the current production CSV;
- calculate `sha256` for the source and canonical CSV;
- record covered start, covered end, row count, and expected tail date;
- link readiness and cache evidence;
- store the sample evidence outside the repository;
- confirm no secrets, `.env` values, waitlist contacts, or analytics events are included.

When automated later, add tests for manifest creation, hash calculation, sanitized fields, and failure behavior when
source files are missing.

## Acceptance Criteria

- Phase 7/8 docs include an import provenance and source archive gate.
- Production imports have at least manual evidence for source file, hash, retrieval method, row count, covered range,
  expected tail date, validation output, readiness, and cache evidence.
- Provenance artifacts are stored outside the repository and exclude secrets and PII.
- Data correction, restore drill, launch evidence, and future methodology research can refer to source manifests.
- The design does not imply a public audit product, full vendor reconciliation, paid SLA, or API change before separate
  demand and implementation work.
