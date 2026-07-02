# API DB Change Management

> Status: future-facing. Last reviewed 2026-07-02. This is a deferred Phase 9/change-readiness gate for future API,
> database, analytics, paid-access, or methodology-version changes. It is not a Phase 8 launch blocker.

## Context

The current product is still a small production pilot. It has a simple PostgreSQL/TimescaleDB schema, one idempotent
initial migration, public read endpoints, a waitlist endpoint, validation-versioned cache headers, and version metadata
such as `methodology_version` and `snapshot_version`.

Future work may add analytics tables, API clients, key identifiers, paid access, widgets, agent integrations, or a
versioned methodology v2. Those changes can break users, agents, frontend code, cached payload assumptions, or restore
procedures if they are made opportunistically.

This design defines a lightweight gate for future API and database changes.

## Goal

Make future API and DB changes deliberate:

- preserve compatibility for current public endpoints where practical;
- define what counts as additive, risky, or breaking;
- require migration and rollback thinking before production changes;
- connect DB changes to backup/restore evidence;
- keep docs and contract tests aligned with exposed behavior;
- avoid surprising future API clients, agents, or paid licensees.

## Non-Goals

- Do not promise enterprise change-management, uptime SLA, or formal SemVer support during the free pilot.
- Do not add a public API versioning layer before external API clients exist.
- Do not build an admin dashboard or migration UI.
- Do not require feature flags for every small internal change.
- Do not freeze the product from learning after launch.

## Change Classes

Use three classes:

- **Additive compatible change:** adds optional response fields, new metadata, new internal tables, or new docs without
  removing existing behavior.
- **Risky compatible change:** changes calculations, cache semantics, migration behavior, retention, or operational flows
  while trying to preserve API shape.
- **Breaking change:** removes or renames public fields, changes endpoint envelope shape, changes meaning of an existing
  field, changes error semantics, changes auth requirements, or makes existing API clients/agents wrong by default.

Breaking changes should wait for explicit versioning, deprecation notes, and a migration path unless no external clients
exist and the launch evidence confirms the endpoint is not in active use.

## API Compatibility Rules

For public endpoints:

- keep the `{ "data": ... }` and `{ "data": ..., "meta": ... }` envelope conventions stable;
- do not remove existing response fields without a deprecation path;
- prefer adding explicit new fields over changing the meaning of existing ones;
- keep backwards-compatible aliases such as `price_usd` when introducing clearer names like `model_price_usd`;
- keep `methodology_version`, `snapshot_version`, freshness, and readiness metadata visible where relevant;
- document any new response fields in `docs/api-reference.md`;
- update frontend and API tests when endpoint contracts change;
- treat cache headers and `X-Cache-Version` as part of the public-read behavior.

If a future professional/API client exists, breaking changes should use either a versioned endpoint, versioned
methodology metadata, or an explicitly agreed migration window.

## Database Migration Rules

For schema changes:

- create a new migration file instead of editing historical migrations after they have been applied to production;
- keep migrations idempotent where practical;
- test migrations on a fresh database and an existing database with representative data;
- take a fresh backup before production migrations;
- know whether rollback means SQL down migration, restoring a backup, or reverting code and replaying import data;
- avoid destructive migrations unless the backup, restore path, and data-loss boundary are explicit;
- document any new tables that store PII, analytics, API client identifiers, billing references, or provenance metadata.

If a migration touches waitlist contacts, analytics, billing references, API keys, or retention behavior, update
`docs/security-and-privacy.md` before production use.

## Rollout And Rollback

Before deploying a risky or breaking change:

1. Identify the change class.
2. Record affected endpoints, tables, migrations, cache behavior, and docs.
3. Run relevant tests and build checks.
4. Take a backup if production data or schema is affected.
5. Apply migration and deploy code in the safest order for compatibility.
6. Smoke test readiness, latest risk, brief, waitlist, and affected endpoints.
7. Confirm cache headers and validation-version behavior.
8. Record rollback path and accepted limitations.

For the free pilot, a rollback can be manual and operator-driven. For paid access or professional API clients, rollback
expectations must be designed separately before accepting reliability commitments.

## Contract Tests

Before depending on external API clients, add contract tests for:

- required fields in public read payloads;
- envelope shape;
- error status for invalid inputs;
- cache headers for public read endpoints;
- no-store behavior for `POST /api/waitlist`;
- methodology and snapshot version metadata;
- compatibility aliases retained for existing clients.

Contract tests should be small and focused. They do not need a separate testing framework until the API has real external
consumers.

## Documentation Requirements

Every risky or breaking API/DB change should update the relevant docs:

- `docs/api-reference.md` for endpoint shape and cache behavior;
- `docs/architecture.md` for new service/table responsibilities;
- `docs/data-pipeline.md` for import, validation, or provenance changes;
- `docs/security-and-privacy.md` for PII, analytics, API client identity, billing, or retention changes;
- `docs/operations.md` for migration, backup, rollback, and smoke checks;
- `docs/production-roadmap.md` for phase status or future-scope changes.

Do not let implementation drift become the only source of truth.

## Error Handling

If a migration fails in production, stop and preserve logs before retrying. Do not repeatedly apply ad hoc SQL without an
incident note.

If a deployed API change breaks the frontend or known clients, prefer reverting code or restoring compatibility fields
over forcing clients to adapt during the pilot.

If a methodology change alters the interpretation of risk values, do not silently reuse the same version label. Use the
risk methodology research process and versioning notes.

## Acceptance Criteria

- Future analytics, API-key, paid-access, widget, agent, or methodology-v2 work has an API/DB change-management gate.
- Additive, risky, and breaking changes are classified before production deployment.
- Production schema changes have backup, migration, verification, and rollback notes.
- Public endpoint compatibility is preserved unless a deliberate versioning/deprecation path exists.
- Docs and focused tests are updated when endpoint contracts, cache semantics, migrations, or data retention behavior
  change.
