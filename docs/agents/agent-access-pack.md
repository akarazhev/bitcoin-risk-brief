# Agent Access Pack

Bitcoin Risk Brief exposes a public HTTP API for analytics and research context. Its output is not financial advice,
investment advice, a price forecast, or a trading recommendation.

The examples below are response-shape examples copied from the [API reference](../engineering/api-reference.md). They
are not current readings. Fetch the API at request time and apply the readiness-first sequence below.

## Read readiness first

An agent must use this sequence for every request that could be described as current:

1. Call `GET /api/readiness` with cache bypassed. Do not substitute `GET /api/health`; process health does not prove
   that the risk data is fresh or validated.
2. Continue only when the response is HTTP 200, `status` is `ready`, and every item in `checks` is `true`.
3. Record `latest_date`, `covered_end`, `data_age_days`, `max_age_days`, `source`, and `methodology_version` from the
   readiness response.
4. Fetch the required risk, history, levels, or brief endpoint and retain its `X-Cache-Version` response header.
5. Before using a product payload as current, compare its applicable UTC date with both readiness `latest_date` and
   `covered_end`:

   - for latest risk, compare the date in `data.timestamp`;
   - for risk levels, compare `meta.evaluation_date` or the date in `meta.base.timestamp`;
   - for the brief, compare the date in `data.as_of`;
   - for history intended to include the current tail, compare the newest date in `data[*].timestamp`. An intentionally
     historical range is not expected to end on the readiness date and must not be presented as current.

6. If the applicable date does not match both readiness dates, reject the value or label it as not matching current
   readiness. A product response can come from a browser or edge cache even after the no-store readiness request has
   returned newer state. `X-Cache-Version` identifies the validation version used for the product response, but it does
   not replace the date comparison. Do not combine product responses with different `X-Cache-Version` values into one
   current snapshot.
7. Report the covered date and freshness state with any value. If readiness returns HTTP 503, report that the data is
   degraded and do not describe a stored or cached value as current.

The model uses completed daily candles. A numeric value alone does not say whether the latest import completed,
validation passed, the derived risk tail matches the validated source tail, or the accepted freshness window has
expired. Without that state, the value is unusable as a current reading.

```bash
curl --fail-with-body \
  -H 'Cache-Control: no-cache' \
  https://bitcoinriskbrief.minihub.app/api/readiness
```

See [Freshness and validation](../engineering/freshness-and-validation.md) for every readiness check.

## Endpoints

The production base URL is `https://bitcoinriskbrief.minihub.app`. The seven public application endpoints are listed
below. The separate machine-readable schema is at `/api/openapi.json`.

### `GET /api/health`

Use this only to check that the backend process can answer. It is not a data-readiness check.

```bash
curl --fail-with-body https://bitcoinriskbrief.minihub.app/api/health
```

```json
{ "status": "ok" }
```

### `GET /api/readiness`

Call this before any endpoint that returns a risk-derived value. HTTP 200 means every displayed check passed; HTTP 503
means at least one check failed. The response is not cached.

```bash
curl --fail-with-body \
  -H 'Cache-Control: no-cache' \
  https://bitcoinriskbrief.minihub.app/api/readiness
```

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

### `GET /api/risk/latest`

Returns the latest stored risk point. Read readiness first and carry its date, freshness, and methodology metadata into
any summary.

```bash
curl --fail-with-body https://bitcoinriskbrief.minihub.app/api/risk/latest
```

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

### `GET /api/risk/history`

Returns completed daily risk rows in ascending timestamp order. `start_date` and `end_date` accept `YYYY-MM-DD`;
`limit` defaults to `2000` and accepts values from `2` through `5000`.

```bash
curl --fail-with-body \
  'https://bitcoinriskbrief.minihub.app/api/risk/history?start_date=2026-06-24&end_date=2026-06-24&limit=2'
```

```json
{
  "data": [
    { "timestamp": "2026-06-24T00:00:00+00:00", "risk": 0.31, "risk_state": "neutral" }
  ],
  "meta": { "returned_points": 1 }
}
```

Actual rows also contain `price_usd`, `score`, component values, z-scores, and `turnover_enabled`. The latest-only
`model_price_usd`, `low_usd`, and `high_usd` fields are not included in history rows.

### `GET /api/risk/levels`

Returns the model's price scenarios for target risk levels. These are hypothetical model outputs, not forecasts,
targets, support levels, or trading instructions.

```bash
curl --fail-with-body https://bitcoinriskbrief.minihub.app/api/risk/levels
```

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

### `GET /api/brief/latest`

Returns the stored daily brief, or a brief built from the latest and previous risk rows when no suitable stored snapshot
exists. Sections are generated for `en`, `ru`, `zh`, `de`, `fr`, `es`, and `ar`; older local snapshots may contain only
`en` and `ru` until a fresh collector write.

```bash
curl --fail-with-body https://bitcoinriskbrief.minihub.app/api/brief/latest
```

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

### `POST /api/waitlist`

Stores or updates an email address after Turnstile verification. Replace the example token with the
single-use token issued to the client. Unsupported locales are normalized to `en` before storage.

```bash
curl --fail-with-body \
  -X POST \
  -H 'Content-Type: application/json' \
  --data '{
    "contact": "user@example.com",
    "locale": "en",
    "source": "agent_access",
    "turnstile_token": "single-use-client-token"
  }' \
  https://bitcoinriskbrief.minihub.app/api/waitlist
```

```json
{
  "data": {
    "contact_type": "email",
    "locale": "en",
    "created": true
  }
}
```

Successful writes return HTTP 201. The endpoint can also return 403 for rejected Turnstile verification, 503 when
verification is unavailable, 422 for an invalid payload, and 429 for rate limiting. Failed Turnstile verification does
not write a lead. Every waitlist response uses `Cache-Control: no-store` and `Pragma: no-cache`.

## Demand tracking

Use `source=agent_access` for waitlist leads or direct contacts about agent and developer access. Use
`source=risk_signal_license` when the request is specifically about paid reuse of the BTC risk metric in one product or
AI agent. These values measure demand for a future experiment; they do not imply that authenticated, paid, or licensed
access exists today.

Collect manual requests for API keys, webhooks, MCP, SDKs, embeds, alerts, commercial use, and one-product risk-signal
licensing. Keep those requests as sanitized demand themes under the project's privacy constraints; do not place raw
contacts or private messages in repository evidence. Raw API traffic alone is not proof of integration or payment
intent.

## Cache semantics

The backend product cache covers `GET /api/risk/latest`, `GET /api/risk/history`, `GET /api/risk/levels`, and
`GET /api/brief/latest`. It does not cover readiness or waitlist requests.

| Header | Implemented meaning |
| --- | --- |
| `Cache-Control` | Defaults to `public, max-age=60, stale-while-revalidate=300`. The values are configurable. `stale-while-revalidate` applies to browser and edge caches; the backend does not serve expired in-process entries. |
| `ETag` | Strong validator derived from the request key, validation version, and response body. |
| `X-Cache` | `MISS` when the backend built the payload and `HIT` when its in-process cache supplied it. It is not an edge-cache status. |
| `X-Cache-Version` | Marker derived from the latest `btc_risk_validation` row. It changes after a successful import. |

Save the `ETag` from a response and send it back with `If-None-Match`:

```bash
curl -i \
  -H 'If-None-Match: "previous-etag-value"' \
  https://bitcoinriskbrief.minihub.app/api/risk/latest
```

If the request key, validation version, and payload are unchanged, the backend returns HTTP 304 with no response body.
The cache key includes the full path and query string, so different history filters are separate entries.

The backend cache storage key also includes `X-Cache-Version`. After the collector successfully writes a new validation
row, an older in-process entry cannot satisfy a request for the new version; the next request rebuilds synchronously.
Clients must still read readiness first and compare product dates because browser and edge caches follow their own
`Cache-Control` lifetime.

## Rate limits

`POST /api/waitlist` has an application-level fixed window controlled by `WAITLIST_RATE_LIMIT_PER_HOUR`, which defaults
to 20 requests per client key per hour. The key preference is `CF-Connecting-IP`, then the first `X-Forwarded-For`
address, then the socket host. An exceeded application limit returns HTTP 429 with a no-store response.

The repository's Cloudflare helper can configure a waitlist rule for 5 requests per 60-second period and a broader
`/api/*` rule for 120 requests per 60-second period. The documented Free-plan public-pilot subset is narrower: it skips
the managed WAF and broader API rule, applies only the waitlist rule with a 10-second period and 10-second mitigation
timeout, and therefore does not justify claiming a general public-read API limit. Agents should back off on HTTP 429 and
must not use retries to bypass either layer.

## Interpretation

The implemented state thresholds are:

| Risk range | State |
| --- | --- |
| below `0.30` | `low` |
| `0.30` through below `0.70` | `neutral` |
| `0.70` and above | `high` |

`price_usd` and `model_price_usd` in the latest-risk payload are the same HLC3 model price:
`(high + low + close) / 3` for the latest completed daily candle. They are not live spot prices and are not close-only
prices. `low_usd` and `high_usd` are the bounds of that same candle when the matching OHLCV row exists.

Risk-level prices answer a constrained model question: what hypothetical price would correspond to each target risk
level while the solver keeps non-price components fixed for the latest day? They are scenarios, not predictions of
where Bitcoin will trade. See [Risk methodology](../product/risk-methodology.md) for the complete implemented model.

## What an agent must not do

An agent must not:

- present a risk value, state, brief, or scenario as financial advice, investment advice, or a buy or sell signal;
- report a value as current without first obtaining HTTP 200 readiness and carrying the covered date and freshness
  state into the answer;
- use `GET /api/health` as evidence that the data is current;
- treat a scenario price as a prediction, target, support level, or resistance level;
- call HLC3 a live spot price;
- reuse an example value from this page as if it came from the live API.
