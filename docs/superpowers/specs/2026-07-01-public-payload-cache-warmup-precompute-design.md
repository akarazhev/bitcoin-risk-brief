# Public Payload Cache Warmup And Precompute Design

> Status: future-facing performance hardening. Last reviewed 2026-07-13 for live readiness semantics. This extends the
> existing public endpoint cache before active traffic if first-load latency remains too high. `GET /api/readiness` is
> intentionally live/no-store and is a warmup gate, not a warmed cache payload.

## Goal

Make the first public page load fast after backend startup and after the nightly data import.

The current backend already caches public product read endpoints with `Cache-Control`, `ETag`, `X-Cache`, and
`X-Cache-Version`. The cache is validation-versioned, but it is lazy: the first request for a cache key after startup,
TTL expiry, or a new validation marker still reads from TimescaleDB and builds the response payload. Readiness is
separate: it returns `Cache-Control: no-store` and should be built live on each request.

The product should avoid making the first real user pay that cache-miss cost.

## Current Behavior

Risk calculation is not done on every public request. The collector imports the canonical CSV, recomputes risk rows, and
writes validation data and brief snapshots. The backend then serves public endpoints from the database and its in-process
public endpoint cache.

The likely first-load costs are:

- `/api/risk/history?limit=2000` reads and serializes a large history payload;
- `/api/risk/levels` reads full OHLCV history and builds the risk-level table on a cache miss;
- `/api/brief/latest` and `/api/risk/latest` are smaller but still miss until warmed;
- `/api/readiness` is a live no-store status endpoint and should be checked before warming product payloads;
- the frontend requests several endpoints at once;
- the chart bundle is lazy-loaded separately by the frontend.

## Roadmap Placement

This belongs as a Phase 5/8 performance hardening add-on:

- Phase 5 already delivered public cache headers and in-process cache behavior.
- Phase 8 should verify first-load latency on the public hostname before active traffic.
- If the first cache miss is too slow, add cache warmup and, if needed, persisted precomputed payloads.

## Recommended Approach

Use a staged approach.

### Stage 1: Measure

Before changing behavior, measure:

- backend access-log `duration_ms` for each public read endpoint;
- `X-Cache: MISS` versus `X-Cache: HIT`;
- browser waterfall timing for API calls and the lazy chart chunk;
- first request after backend startup;
- first request after a successful import and validation-version change.

This distinguishes backend payload cost from frontend bundle/render cost.

### Stage 2: Warm In-Process Public Cache

Add a backend warmup routine that checks readiness first, then builds the standard public product payloads:

- `/api/risk/latest`;
- `/api/risk/history?limit=2000`;
- `/api/risk/levels`;
- `/api/brief/latest`.

Warmup should run:

- during backend startup after the database pool is ready, if data exists;
- after a successful collector/import run, either through an internal warmup call, a backend admin/internal endpoint, or
  a lightweight operational command;
- after detecting a new validation version, if lazy refresh is still needed as a fallback.

Warmup must use the same serialization and cache-key behavior as normal product public requests so `ETag`,
`X-Cache-Version`, and response shapes stay identical. Readiness should keep returning live `Cache-Control: no-store`
responses and should not be inserted into the public cache.

### Stage 3: Precompute Expensive Payloads If Needed

If warmup is still not enough, precompute the expensive payloads at import time and store them as derived data.

Candidates:

- risk levels payload, because it currently reads full OHLCV history and builds levels on cache miss;
- default risk history payload for the launch chart;
- latest/brief bundle if the frontend later moves to a combined bootstrap endpoint.

Readiness can still be checked before serving a combined bootstrap response, but it should remain live/no-store and
should not be stored as a cached or precomputed payload.

Precomputed payloads must be derived from the same validation version as the latest risk data. They should be replaced
after successful imports and ignored when validation is missing or stale.

## Cache TTL Strategy

Backend in-process cache TTL can be longer than browser or edge freshness.

For a daily risk product, consider:

- keeping browser/edge freshness conservative, such as `PUBLIC_CACHE_MAX_AGE_SECONDS=60`;
- increasing backend in-process TTL to several hours or one day;
- relying on validation-version changes to invalidate old backend payloads after successful imports.

Do not serve stale data across a validation-version change. `X-Cache-Version` remains the freshness boundary.

## Safety Rules

- Do not recompute the canonical risk methodology inside public request handlers.
- Do not serve warmed payloads when readiness validation fails.
- Do not let warmup hide failed imports or stale data.
- Keep `POST /api/waitlist` uncached.
- Preserve existing public endpoint response shapes.
- Keep Cloudflare/browser cache behavior separate from backend in-memory warmup.

## Testing And Verification

Tests should cover:

- warmup populates the same cache keys used by public requests;
- a warmed endpoint returns `X-Cache: HIT` without rebuilding from the database;
- a validation-version change invalidates old warmed payloads;
- warmup failure is logged but does not break backend startup when data is absent;
- `POST /api/waitlist` remains no-store;
- risk levels and history responses match the existing endpoint schemas.

Operational checks should cover:

- first public request after backend start;
- first public request after nightly import;
- a repeated request showing `X-Cache: HIT`;
- public hostname behavior through Cloudflare.

## Non-Goals

This design does not include:

- replacing TimescaleDB as the durable source;
- moving canonical risk computation into the backend request path;
- adding Redis or another external cache before in-process warmup is measured;
- adding a broad analytics or dashboard cache;
- changing waitlist caching behavior;
- changing chart rendering or ECharts bundling unless measurements prove frontend bundle load is the bottleneck.

## Success Criteria

The work is successful when:

- the first public page load after backend startup avoids slow database-backed cache misses for standard public payloads;
- the first public page load after nightly import sees warmed payloads for the new validation version;
- `/api/risk/levels` no longer causes visible first-load latency;
- `X-Cache-Version` still changes after successful imports;
- stale or failed imports do not produce fresh-looking cached responses;
- launch checks can observe `X-Cache: HIT` for warmed standard endpoints before sending active traffic.
