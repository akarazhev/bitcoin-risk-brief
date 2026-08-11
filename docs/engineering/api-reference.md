# API Reference

The backend is served behind the frontend nginx proxy at the same origin in local compose. API paths are prefixed with `/api`.

## Envelope Convention

Most successful data endpoints return:

```json
{ "data": "..." }
```

List endpoints may also return:

```json
{ "data": [], "meta": {} }
```

Errors use FastAPI's default JSON shape:

```json
{ "detail": "..." }
```

## Compatibility Notes

The current API is a production-pilot public interface, not a paid external API contract. Still, public endpoint shapes
should remain backwards-compatible where practical:

- prefer additive fields over changing existing field meanings;
- keep compatibility aliases such as `price_usd` when clearer fields are added;
- keep methodology, freshness, snapshot, and readiness metadata visible where relevant;
- document new fields, cache semantics, and error changes here before relying on them externally;
- use a deliberate versioning or deprecation path before breaking future API clients, agents, widgets, or paid
  integrations.

## Public Read Caching

`GET /api/readiness` is the live freshness/status endpoint and is not part of the backend public endpoint cache. It
returns `Cache-Control: no-store` and `Pragma: no-cache`.

The public product read endpoints `/api/risk/latest`, `/api/risk/history`, `/api/risk/levels`, and `/api/brief/latest`
use the backend public endpoint cache.

Cached responses include:

| Header | Meaning |
| --- | --- |
| `Cache-Control` | Defaults to `public, max-age=60, stale-while-revalidate=300`; tune with `PUBLIC_CACHE_MAX_AGE_SECONDS` and `PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS`. The stale-while-revalidate directive is for browser and edge caches; backend in-process stale-while-revalidate is intentionally deferred. |
| `ETag` | Strong validator for conditional browser and edge revalidation. |
| `X-Cache` | `MISS` when the backend rebuilt the payload, `HIT` when the in-process cache served it. |
| `X-Cache-Version` | Validation marker derived from the latest `btc_risk_validation` row. It changes after successful imports. |

Clients may send `If-None-Match` with the last `ETag`; unchanged responses return HTTP 304. The backend cache TTL is
controlled by `PUBLIC_CACHE_TTL_SECONDS` and defaults to 300 seconds. The cache key includes the full request path and
query string, so filtered history requests are cached separately.

Concurrent backend cold misses for the same request key and `X-Cache-Version` are coalesced so one rebuild is shared by
matching requests. When an in-process entry expires and the validation marker is unchanged, the backend rebuilds
synchronously rather than serving an expired in-process payload. When the validation marker changes, the next matching
public read also rebuilds synchronously for the new version; stale in-process data is not served across
`X-Cache-Version` boundaries.

The backend may warm these product cache keys during startup or via an operator command, but the response body shape and
cache headers are the same as a normal request. Operator warmup should target a local or private origin, for example
`PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache`. The command checks readiness first as a
`curl -f` gate, then calls normal public GET routes for product payloads only, fails on non-success responses, and does
not add a public admin endpoint.

## GET /api/health

Basic process health check.

Response:

```json
{ "status": "ok" }
```

## GET /api/readiness

Deployment/readiness check. Returns HTTP 200 when all checks pass, otherwise HTTP 503.

Response shape:

```json
{
  "status": "ready",
  "checks": {
    "risk_data_available": true,
    "validation_available": true,
    "risk_range_ok": true,
    "validation_has_rows": true,
    "latest_matches_validation_end": true,
    "source_is_canonical": true,
    "data_fresh": true
  },
  "data": {
    "latest_date": "2026-06-25",
    "covered_end": "2026-06-25",
    "data_age_days": 1,
    "max_age_days": 2,
    "source": "coinmarketcap_csv",
    "row_count": 5827,
    "methodology_version": "crypto-scout-canonical-v1.1"
  }
}
```

## GET /api/risk/latest

Returns the latest stored risk point.

`price_usd` is the HLC3 model price from the latest completed daily candle, not a spot price or close-only value.
`model_price_usd` is the explicit name for the same value. `low_usd` and `high_usd` come from the `btc_ohlcv_daily`
row whose `timestamp` matches the latest risk row. If that OHLCV row is missing, `low_usd` and `high_usd` are `null`;
clients should hide those sub-values rather than showing zeroes or stale values.

Response shape:

```json
{
  "data": {
    "timestamp": "2026-06-25T00:00:00+00:00",
    "price_usd": 60100.0,
    "model_price_usd": 60100.0,
    "low_usd": 58800.0,
    "high_usd": 61584.0,
    "risk": 0.3025,
    "score": -0.82,
    "risk_state": "neutral",
    "trend_dev": 0.0,
    "vol_regime": 0.0,
    "turnover": -10.2,
    "z_trend_dev": 0.0,
    "z_vol_regime": 0.0,
    "z_turnover": 0.0,
    "turnover_enabled": true
  }
}
```

## GET /api/risk/history

Returns historical risk rows sorted ascending by timestamp.

Query parameters:

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `start_date` | date | none | Optional `YYYY-MM-DD`. |
| `end_date` | date | none | Optional `YYYY-MM-DD`. |
| `limit` | integer | `2000` | Minimum `2`, maximum `5000`. |

Response shape:

```json
{
  "data": [
    { "timestamp": "2026-06-24T00:00:00+00:00", "risk": 0.31, "risk_state": "neutral" }
  ],
  "meta": { "returned_points": 1 }
}
```

Actual rows include the historical risk fields: `timestamp`, `price_usd`, `risk`, `score`, `risk_state`,
component values, z-scores, and `turnover_enabled`. Latest-only `model_price_usd`, `low_usd`, and `high_usd`
are not part of `/api/risk/history`.

## GET /api/risk/levels

Returns target risk levels and solved BTC prices.

`/api/risk/levels` returns the latest persisted collector-generated risk-level snapshot under normal production
operation. If the snapshot is missing in local/dev data, the backend may fall back to computing the compatible payload
from the available OHLCV history.

Response shape:

```json
{
  "data": [
    { "risk": 0.0, "price_usd": 10000.0 },
    { "risk": 0.025, "price_usd": 11000.0 }
  ],
  "meta": {
    "base": { "timestamp": "2026-06-25T00:00:00+00:00", "risk": 0.3025 },
    "methodology_version": "crypto-scout-canonical-v1.1",
    "evaluation_date": "2026-06-25",
    "current_price": 60100.0,
    "current_risk": 0.3025,
    "turnover_enabled": true,
    "risk_step": 0.025,
    "source_row_count": 5827
  }
}
```

## GET /api/brief/latest

Returns the latest stored brief snapshot. If no snapshot exists but risk rows exist, the backend can build a brief from latest and previous risk rows.

Response shape:

```json
{
  "data": {
    "snapshot_version": "bitcoin-risk-brief-v1",
    "as_of": "2026-06-25T00:00:00+00:00",
    "risk": 0.3025,
    "risk_state": "neutral",
    "price_usd": 60100.0,
    "delta_risk": -0.01,
    "sections": {
      "en": {
        "summary": "...",
        "what_changed": "...",
        "avoid_now": "...",
        "confirm_next": "..."
      },
      "ru": {
        "summary": "...",
        "what_changed": "...",
        "avoid_now": "...",
        "confirm_next": "..."
      }
    }
  }
}
```

Brief `sections` are generated for `en`, `ru`, `zh`, `de`, `fr`, `es`, and `ar`. `zh` is Simplified Chinese.
Older persisted local snapshots may contain only `en` and `ru` until the collector writes a fresh brief snapshot.

## POST /api/waitlist

Stores or updates a waitlist lead.

`POST /api/waitlist` is never cacheable and is not part of public cache warmup. Responses include
`Cache-Control: no-store` and `Pragma: no-cache`, including validation and rate-limit responses.

Request:

```json
{
  "contact": "user@example.com",
  "locale": "en",
  "source": "landing",
  "turnstile_token": "single-use-client-token"
}
```

Accepted locale values are `en`, `ru`, `zh`, `de`, `fr`, `es`, and `ar`. Unsupported values are normalized to `en`
before storage.

Accepted contacts:

- email address;

Response:

```json
{
  "data": {
    "contact_type": "email",
    "locale": "en",
    "created": true
  }
}
```

Status codes:

| Status | Meaning |
| --- | --- |
| `201` | Lead saved. |
| `403` | Turnstile rejected a present invalid, expired, replayed, wrong-action, or wrong-hostname token. |
| `503` | Turnstile verification is temporarily unavailable or server configuration is incomplete. |
| `422` | Invalid contact payload, including an omitted or empty `turnstile_token`. |
| `429` | Too many waitlist submissions from the same client key. |

Every waitlist outcome is returned with `Cache-Control: no-store` and `Pragma: no-cache`. Failed Turnstile
verification never writes a lead.
