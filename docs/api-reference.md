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

## Public Read Caching

The public read endpoints `/api/readiness`, `/api/risk/latest`, `/api/risk/history`, `/api/risk/levels`, and
`/api/brief/latest` use the backend public endpoint cache.

Cached responses include:

| Header | Meaning |
| --- | --- |
| `Cache-Control` | Defaults to `public, max-age=60, stale-while-revalidate=300`; tune with `PUBLIC_CACHE_MAX_AGE_SECONDS` and `PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS`. |
| `ETag` | Strong validator for conditional browser and edge revalidation. |
| `X-Cache` | `MISS` when the backend rebuilt the payload, `HIT` when the in-process cache served it. |
| `X-Cache-Version` | Validation marker derived from the latest `btc_risk_validation` row. It changes after successful imports. |

Clients may send `If-None-Match` with the last `ETag`; unchanged responses return HTTP 304. The backend cache TTL is
controlled by `PUBLIC_CACHE_TTL_SECONDS` and defaults to 300 seconds. The cache key includes the full request path and
query string, so filtered history requests are cached separately.

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
    "methodology_version": "crypto-scout-canonical-v1"
  }
}
```

## GET /api/risk/latest

Returns the latest stored risk point.

Response shape:

```json
{
  "data": {
    "timestamp": "2026-06-25T00:00:00+00:00",
    "price_usd": 60100.0,
    "risk": 0.3025,
    "score": -0.82,
    "risk_state": "low",
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
    { "timestamp": "2026-06-24T00:00:00+00:00", "risk": 0.31, "risk_state": "low" }
  ],
  "meta": { "returned_points": 1 }
}
```

Actual rows include the full `RiskPoint` fields shown in `/api/risk/latest`.

## GET /api/risk/levels

Returns target risk levels and solved BTC prices.

Response shape:

```json
{
  "data": [
    { "risk": 0.0, "price_usd": 10000.0 },
    { "risk": 0.025, "price_usd": 11000.0 }
  ],
  "meta": {
    "base": { "timestamp": "2026-06-25T00:00:00+00:00", "risk": 0.3025 },
    "methodology_version": "crypto-scout-canonical-v1",
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
    "risk_state": "low",
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

## POST /api/waitlist

Stores or updates a waitlist lead.

`POST /api/waitlist` is never cacheable. Responses include `Cache-Control: no-store` and `Pragma: no-cache`, including
validation and rate-limit responses.

Request:

```json
{
  "contact": "user@example.com",
  "locale": "en",
  "source": "landing"
}
```

Accepted contacts:

- email address;
- Telegram handle matching `@[A-Za-z0-9_]{5,32}`.

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
| `422` | Invalid contact payload. |
| `429` | Too many waitlist submissions from the same client key. |
