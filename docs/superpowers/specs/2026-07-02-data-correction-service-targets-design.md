# Data Correction And Service Targets

> Status: future-facing. Last reviewed 2026-07-02. This is a Phase 7/8 operational readiness gate for the production
> pilot, not a paid SLA or enterprise support commitment.

## Context

The project already validates imported BTC CSV data, recomputes the full risk series after imports, deletes stale rows
after the CSV tail, caches public payloads by validation version, and plans backups, restore drills, alerts, and incident
notes.

One important gap remains: the operator needs a written policy for correcting data after a wrong value has already been
published. A bad CoinMarketCap CSV, partial CSV, mistaken manual import, stale cache, or methodology bug could show an
incorrect latest risk value to users. Backup and restore docs explain how to recover data, but not how to classify,
correct, communicate, and record a published data correction.

The same document should also define lightweight production-pilot service targets so the operator can distinguish
"acceptable for a free pilot" from "must stop traffic or correct immediately".

## Goal

Define how the product handles:

- incorrect or incomplete BTC source data;
- incorrect risk rows or latest brief snapshots;
- stale public cache after correction;
- public or portfolio correction notes;
- pilot-level freshness, recovery, and downtime targets.

## Non-Goals

- Do not promise SLA/SLO terms to users or licensees.
- Do not add a public status page requirement for the first pilot.
- Do not build an admin dashboard or data-editor UI.
- Do not add automated data-vendor reconciliation before evidence shows it is needed.
- Do not override the existing backup, restore, data-pipeline, or incident-response docs.

## Recommended Approach

Use a small correction policy plus pilot service targets:

1. Classify the issue.
2. Freeze or limit further automated changes when needed.
3. Restore or re-import from the last known-good source.
4. Recompute risk and brief snapshots.
5. Purge or wait out public caches.
6. Capture a correction note.
7. Review pilot service targets and decide whether broader traffic should pause.

This should live as an operational gate in Phase 7/8 because it affects launch trust, but it should not block the first
small smoke test if the operator has a manual correction path and accepted limitations recorded.

## Issue Classification

Use three practical severity levels:

- **Low:** cosmetic copy, chart label, or stale portfolio text that does not change the risk value or data date.
- **Medium:** stale data, delayed import, cache inconsistency, missing latest day, or incorrect brief text while the
  canonical historical data remains valid.
- **High:** wrong source data, wrong methodology output, bad manual import, incorrect latest risk value, corrupted DB
  rows, or a misleading public risk state.

High-severity issues should pause active promotion and trigger a correction note. Medium issues need an operator note
and a fix before broader traffic. Low issues can be handled in the next normal release if no user-facing trust claim is
wrong.

## Correction Flow

When the latest risk value, data date, or brief snapshot may be wrong:

1. Record the first observed time, public URL, affected endpoint, latest displayed data date, and current commit.
2. Check `/api/readiness`, latest risk, validation metadata, collector logs, and the canonical CSV tail.
3. Stop or defer additional automated imports if they could overwrite evidence or make the issue harder to inspect.
4. Identify the last known-good source: previous canonical CSV, off-server backup, staged manual CSV, or trusted
   operator-downloaded CoinMarketCap CSV.
5. Restore or re-import the known-good source using the documented data-pipeline and restore procedures.
6. Recompute all risk rows and the latest brief snapshot.
7. Verify readiness, latest risk, history tail, brief snapshot, and cache headers.
8. Purge Cloudflare or wait for public cache expiry if stale responses could remain visible.
9. Capture a correction note with cause, affected window, fixed data date, fixed commit or import evidence, and whether
   any public/portfolio note is required.

The correction path should prefer re-importing a known-good CSV when the database is otherwise healthy. Use full restore
only when the database state is corrupted or when re-import cannot confidently return the product to a known-good state.

## Public Or Portfolio Correction Note

A correction note is required when the public product or portfolio material could have shown a wrong risk value, wrong
latest date, or misleading risk state.

The note should be short:

- what was corrected;
- affected date or time window;
- whether the risk value changed;
- current methodology version;
- current data date;
- no-advice framing;
- operator follow-up if a user asked about the issue.

Do not overstate precision, blame a vendor without evidence, or imply an audit. If no external users saw the issue, an
internal launch evidence note is enough.

## Pilot Service Targets

These are internal pilot targets, not user-facing SLA promises:

- **Freshness target:** latest production data should normally cover the last completed UTC day within the configured
  freshness window, currently `DATA_FRESHNESS_MAX_AGE_DAYS=2` unless explicitly changed.
- **Correction target:** high-severity bad-data issues should be investigated the same operator day and either corrected
  or marked as an accepted public limitation before additional promotion.
- **Recovery target:** after a known-good backup or CSV is selected, the operator should be able to restore or re-import,
  recompute, and verify readiness using documented commands before broader traffic resumes.
- **Downtime tolerance:** the free production pilot can accept temporary downtime while fixing data integrity. Serving a
  known-wrong risk value is worse than being temporarily unavailable.
- **RPO target:** the pilot should be able to recover to the latest off-server backup or known-good canonical CSV. Paid
  experiments require a separate target before accepting payment.
- **RTO target:** no public guarantee for the free pilot. Before paid usage, define a realistic target based on restore
  drill evidence.

## Cache And Correction Safety

After correction, verify both origin and edge behavior:

- `/api/readiness` returns ready with the expected source and latest date;
- latest risk and brief payloads match the corrected validation version;
- `ETag`, `X-Cache`, and `X-Cache-Version` reflect the corrected data after cache expiry or purge;
- stale Cloudflare responses are not used as correction evidence.

If immediate public correction is needed, purge the public hostname cache or disable caching for the affected path until
the corrected payload is visible.

## Error Handling

If the cause is unknown, record it as unknown and keep the product in a conservative state. Do not invent a source cause.

If no known-good source exists, pause active promotion, mark readiness or launch evidence as degraded, and restore from
the most recent backup only after understanding whether the backup contains the same bad data.

If the correction requires methodology changes, do not silently replace `crypto-scout-canonical-v1`. Treat it as a
separate methodology fix or versioned research decision.

## Testing And Verification

Before broader traffic, the operator should verify the manual correction path with documentation, not necessarily by
injecting bad production data:

- identify where previous CSV and database backups are stored;
- confirm re-import commands are documented;
- confirm restore commands are documented;
- confirm cache purge or cache-expiry behavior is documented;
- run a restore drill as part of Phase 7;
- capture one launch evidence note that includes latest data date, readiness payload, cache headers, and backup/restore
  evidence.

## Acceptance Criteria

- Phase 7/8 docs include a bad-data correction policy.
- The operator can classify low, medium, and high data issues.
- The correction flow covers source CSV, database rows, brief snapshots, public cache, and correction notes.
- Pilot freshness, RPO/RTO, correction, and downtime targets are explicit internal targets, not public SLA promises.
- Paid or professional usage is blocked from inheriting these pilot targets without a separate commercial reliability
  design.
