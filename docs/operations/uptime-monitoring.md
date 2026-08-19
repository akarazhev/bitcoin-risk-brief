# Uptime Monitoring

> **Operational log.** These entries record what was verified and when. They are not claims about product
> capability.

External uptime monitoring for the public endpoints and the agent surface. The monitor set is checked into this
repository as [`uptime-monitors.csv`](uptime-monitors.csv) so the configuration is reproducible rather than living only
inside a provider dashboard.

The file holds public URLs and response keywords only. No account identifiers, monitor identifiers, dashboard links,
alert recipients, or secrets belong in it, or anywhere else in this repository.

## Importing

The provider accepts a `.csv` with the columns `Name,Target,Keyword,Port`. `Port` stays empty for website monitors.

Two things the import cannot carry, both of which must be set afterwards:

- **The maintenance window on `BRB API freshness`.** See below; without it the monitor alerts every night.
- **Where alerts are delivered.** Route them to a private channel. Never to the public Telegram channel, which product
  subscribers read.

Quotation marks inside a keyword are doubled and the field is quoted, per RFC 4180 — `"""status"":""ready"""` is the
correct on-disk form of `"status":"ready"`. After importing, confirm the keyword fields in the dashboard read as the
plain form.

## What Each Monitor Proves

| Monitor | Keyword | What its absence means |
| --- | --- | --- |
| API readiness | `"status":"ready"` | A readiness check failed, or something other than the application answered |
| API health | `"status":"ok"` | The process is down, as distinct from the data being stale |
| API freshness | `"data_age_days":1` | Today's import did not land |
| homepage | `Bitcoin Risk Brief` | nginx is not serving the application shell |
| API latest risk | `"model_price_usd"` | The primary data endpoint is not returning a well-formed payload |
| API risk levels | `"evaluation_date"` | The scenario ladder is unavailable |
| API brief | `"sections"` | The localised brief is unavailable |
| agent `llms.txt` | the readiness-first rule | The agent surface is unreachable |
| docs site | `Bitcoin Risk Brief` | The documentation origin is down |
| docs `llms.txt` | the reference summary | The documentation agent file is unreachable |

**Keywords assert presence, never absence.** The provider treats a missing keyword as downtime, so every keyword here
is a string that exists while the system is healthy and disappears when it is not. A monitor phrased the other way
round — watching for a string that appears only when something is wrong — cannot be expressed and must not be
attempted by inverting the keyword.

**The keyword is not redundant with the status code.** A status check proves something answered; the keyword proves it
was this application. A proxy error page or a challenge interstitial returning HTTP 200 passes the first and fails the
second.

`/robots.txt` and `/sitemap.xml` are deliberately unmonitored: neither can fail independently of the homepage, and an
extra monitor is extra noise. `/openapi.json` is not served at that path.

## Why The Freshness Monitor Needs A Maintenance Window

Set a daily maintenance window of **00:00–01:15 UTC** on `BRB API freshness`.

`data_age_days` is `current_date - latest_date`, and the collector runs at 01:00 UTC importing the last completed day.
So the value is `1` for most of the day, legitimately becomes `2` at 00:00 UTC when the date rolls over, and returns
to `1` once the import lands. Without the window the monitor alerts for that hour every night.

With the window, a failed import is detected at about 01:15 the same morning.

Without this monitor at all, a failed import is caught by the readiness monitor roughly 23 hours later: freshness
tolerates `data_age_days <= 2`, so readiness keeps returning HTTP 200 through the following day and only flips to 503
at the next midnight. That delay is the reason the monitor exists.

## What This Does Not Cover

- **Collector failure alerting.** The freshness monitor infers a failed import from its effect on the data. It does not
  report which stage failed, and it says nothing about a run that partially succeeded. A direct alert from the
  collector remains deferred broader-launch work.
- **Backup freshness**, which is deferred with the rest of the backup automation.
- **Delivery of the daily Telegram post**, which has no HTTP surface to probe.
