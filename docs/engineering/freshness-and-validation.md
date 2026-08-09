# Freshness and Validation

Freshness is an API contract, not an inference from the latest numeric value. Bitcoin Risk Brief provides analytics and
research context only; its output is not financial advice, investment advice, a forecast, or a trading recommendation.

## The readiness contract

`GET /api/readiness` reads the latest stored risk row and the `btc_risk_validation` row whose `validation_key` is
`latest`. It returns HTTP 200 with `status: ready` only when every check is true. If any check is false, it returns HTTP
503 with `status: degraded` and the same diagnostic shape. The response always uses `Cache-Control: no-store` and
`Pragma: no-cache`.

| Check | What the implementation asserts |
| --- | --- |
| `risk_data_available` | A latest row exists in `btc_risk_daily`. |
| `validation_available` | The `btc_risk_validation` row keyed as `latest` exists. |
| `risk_range_ok` | The validation row says every risk value computed for that import was within `[0.0, 1.0]`. |
| `validation_has_rows` | The validation row's `row_count` is greater than zero. |
| `latest_matches_validation_end` | The UTC date of the latest stored risk row equals the validation row's `covered_end` date. |
| `source_is_canonical` | The validation payload identifies the source as `coinmarketcap_csv`. |
| `data_fresh` | `data_age_days` exists and is no greater than the configured maximum age. |

The `data` object explains those decisions. `latest_date` is the UTC date of the latest risk row; `covered_end` is the
end of the validated risk coverage; `source`, `row_count`, and `methodology_version` come from the latest validation
record; and `max_age_days` exposes the policy used for this response.

## How freshness is calculated

The backend converts the latest risk timestamp to a UTC date, takes the current UTC date, and calculates:

```text
data_age_days = current_utc_date - latest_risk_utc_date
```

`data_fresh` is true when a latest date exists and:

```text
data_age_days <= DATA_FRESHNESS_MAX_AGE_DAYS
```

`DATA_FRESHNESS_MAX_AGE_DAYS` defaults to `2`; production can configure it. If no latest risk row exists,
`data_age_days` is `null` and `data_fresh` is false. This is calendar-day freshness for completed daily data, not a
rolling hour count and not a claim that a live spot price was sampled.

## Why coverage alignment is separate

Freshness alone cannot detect mismatched derived state. A recent risk row could coexist with validation metadata for a
different source tail, or a validation row could cover a newer date than the latest derived risk row.

`latest_matches_validation_end` rules out that mismatch by requiring the latest risk date and `covered_end` to be the
same UTC date. It complements `data_fresh`: one check asks whether the data is recent enough, while the other asks
whether the public risk tail is the tail that the latest validation record describes.

## Why degraded readiness is HTTP 503

HTTP 503 makes failed freshness or validation machine-actionable. A monitor, deployment gate, script, or agent using
`curl --fail` stops instead of silently treating a stale or invalid row as current. The response body remains available
so the failing checks, dates, source, and configured age policy can be diagnosed.

The risk read endpoints are not an alternative readiness gate: they can return stored data independently. Correct
clients call `/api/readiness` first and do not fetch or report a current reading after a 503. This separation preserves
diagnostic access without allowing the presence of a numeric row to stand in for freshness.

## What validation records per import

Each collector import recomputes the risk series and upserts the `btc_risk_validation` row keyed as `latest`. The row is
the latest validation state, not an append-only import history. It records:

- `computed_at`, `covered_start`, and `covered_end`;
- the computed risk `row_count`;
- `risk_range_ok` and a human-readable `validation_summary`;
- a JSON payload containing the canonical source, methodology version, robust-z window and minimum periods,
  turnover-enabled state, source-row count, risk-row count, and the dataset validation details used for that import.

Readiness deliberately reads this row together with the latest risk row. That makes source identity, method version,
coverage, row presence, range validation, and age part of one public decision.

## Cache binding with `X-Cache-Version`

The four cached product reads—latest risk, history, levels, and brief—fetch a public data version from the same latest
validation row. The version has this implemented composition:

```text
validation:<computed_at>:<covered_end>:<row_count>:<risk_range_ok>
```

The backend returns that marker as `X-Cache-Version`, includes it in the `ETag` input, and uses `(request key,
data version)` as the in-process cache storage key. A successful import upserts validation with a new `computed_at` and
therefore changes the version. An entry built for the previous validation row cannot satisfy a request under the new
version; the backend rebuilds the payload synchronously instead of serving the expired or prior-version in-process
entry.

This is the binding between a cached payload and the validation state that authorized it. It prevents the backend cache
from outliving its data version. Browser and edge caches still follow `Cache-Control`, including the configured
`stale-while-revalidate` window, which is why clients must call the no-store readiness endpoint first and keep the
cacheable product response's `X-Cache-Version` when recording cache evidence.

## Import provenance packets

The repository provides `scripts/import_provenance_packet.py` and an
[import provenance packet template](../operations/import-provenance-evidence-packet-template.md). The collector does not
automatically create a completed production packet, and the presence of the helper or template is not production proof.

For one real import, an operator packet records sanitized links between:

- import identity, UTC timing, mode, deployed revision, and operator or automation role;
- source type and retrieval method, archived snapshot basename, SHA-256, byte size, row count, covered range, expected
  tail date, and retrieval timestamps when available;
- canonical CSV basename or identifier, post-import SHA-256, row count, coverage, and tail date;
- validation and readiness status, source, range result, row count, coverage end, latest risk/brief date summary, and
  evidence basenames;
- public readiness and product-cache status, including `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`;
- collector/import outcome, deployment context, helper validation result, and any explicit limitation.

Complete source files, raw rows, secrets, private paths, account identifiers, contacts, and unsanitized logs stay outside
Git. A packet is evidence only when it is built from the real source/archive and matching import outputs; otherwise its
status remains partial, pending, blocked, or an explicitly accepted limitation.
