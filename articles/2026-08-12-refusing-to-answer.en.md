<!--
Draft. Not published.

Status:    awaiting the author's rewrite before publication
Venue:     dev.to
Language:  English
Design:    docs/superpowers/specs/2026-08-12-first-article-freshness-design.md

The structure, facts and links here were prepared for editing, not for
publication as written. The piece goes out under a byline and should
read in that person's voice.
-->

# Your API should refuse to answer

Most data products will happily tell you something wrong rather than tell you nothing. I spent a while building one that does the opposite, and the interesting part was not the endpoint that returns 503 — it was discovering how many other places had the same decision hiding in them.

## The number is worth what its date is worth

Bitcoin Risk Brief computes one value a day: a risk score from 0.0 to 1.0, derived from canonical BTC/USD daily data. Low below 0.30, neutral to 0.70, high above. One number, one job.

A daily figure has a property that a real-time figure does not. It is *always* about yesterday — you cannot compute the average of a day that has not finished. So the value carries a date by construction, and the date is not decoration. A risk score for a Tuesday, read on a Friday, is not a stale version of Friday's answer. It is a different question's answer, presented as if it were this one's.

Which raises a question that most dashboards answer badly.

## What most dashboards do

They show you the figure. Somewhere, maybe, a timestamp in grey text. Often nothing at all.

The implicit contract is: here is a number, it is probably current, work out the rest yourself. And it usually *is* current, which is what makes the failure mode nasty. You learn to trust the figure because it was right the last forty times, and the forty-first time the collector died at 3am and the page cheerfully shows Tuesday.

The system knows. The collector logged the failure. The database has a row saying the last successful import covered Tuesday. Every piece of information needed to say "this is three days old, don't act on it" exists somewhere in the stack. It just does not reach the reader.

## Readiness as an endpoint, not a footnote

The first move was making that knowledge addressable:

```
GET /api/readiness
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
    "latest_date": "2026-08-11",
    "covered_end": "2026-08-11",
    "data_age_days": 1,
    "max_age_days": 2,
    "source": "coinmarketcap_csv",
    "row_count": 5874,
    "methodology_version": "crypto-scout-canonical-v1.1"
  }
}
```

Seven named checks rather than one boolean, because "not ready" has causes and the caller deserves to know which one. `latest_matches_validation_end` is there because risk rows and the validation record can disagree — the import wrote some rows and died — and a system that only checked "do we have data" would answer yes.

Then the part that matters:

```python
ready = all(checks.values())
payload = {"status": "ready" if ready else "degraded", ...}
```

and the endpoint returns **HTTP 503** when `ready` is false. Not 200 with a warning field. Not 200 with `"status": "degraded"` for the client to notice if it feels like it. A status code that a load balancer, a monitor, and a careless `response.raise_for_status()` all understand the same way.

This is the easy part. It is one endpoint, and once you have decided that freshness is part of the answer, writing it takes an afternoon.

## The cache is where it gets interesting

Cached responses need invalidation, and the reflex is a TTL. Sixty seconds, five minutes, whatever the traffic justifies.

A TTL answers the question "how long since I computed this?" That is not the question. The question is "is the data underneath this still the data I computed it from?" — and time does not know. A five-minute TTL will happily serve a payload built from Tuesday's import for five minutes after Friday's import succeeded, and then serve a fresh one, and nothing about either response tells you which you got.

So the cache key carries a version derived from the data, not from the clock:

```python
SELECT computed_at, covered_end, row_count, risk_range_ok
FROM btc_risk_validation
WHERE validation_key = 'latest'
```

That row is written by the collector at the end of every successful import. Its contents become `X-Cache-Version`, which ships on every cached response alongside `ETag` and `X-Cache`. When an import succeeds, the version changes, and every cached payload built from the old one is unreachable by construction — not expired, *unaddressable*.

The practical difference: with a TTL you eventually converge on correctness and hope the window was short enough. With a version binding you cannot serve a payload that outlived its data, because the key to it no longer exists.

## The broadcast is where it hurts

Then we added a Telegram channel that posts the daily observation, and the same decision came back wearing different clothes.

A page can show a freshness badge next to the number. The reader sees both at once, and the badge does its job. **A channel post has no badge.** It is read alone, hours later, in a feed, by someone scrolling. There is no page around it to qualify anything.

So the publisher's gate is *stricter* than the API's. The API tolerates data up to `max_age_days` old — two days by default — because the page shows its age beside it. The channel does not get that latitude:

```python
if as_of != last_completed_utc_day(now):
    logger.info("telegram_publish_skipped reason=observation_behind ...")
    return False
```

If the observation does not cover the last completed UTC day, nothing is published. Not a late post, not a post with a caveat. Nothing.

I want to be honest about what that costs, because it is a real cost and it does not self-heal. If the upstream source is late one morning, that day gets no post — and the next day's run sees a newer date and moves on. The gap stays a gap. We chose a missed day over a misleading one, and we chose it knowing the missed day is permanent.

The same logic decided a smaller thing. The post shows the price at which the risk band would change. When the underlying snapshot is missing that point, the line disappears instead of showing a zero or the nearest guess. Three places in one short message where absent data means silence.

## What it actually costs

**You have to decide what "current" means, and defend it.** Two days? One? It is a product decision wearing an engineering costume, and no default saves you from making it. We picked two for the API and one for the channel, and the fact that those differ is the interesting admission: freshness is not a property of the data, it is a property of the data *plus how it will be read*.

**Silence becomes a valid output.** This is the uncomfortable one. A monitoring dashboard with a gap looks broken. A channel that skips a day looks abandoned. Both are working exactly as designed, and you will explain that more than once.

**You give up a certain kind of convenience.** Every consumer now has to handle a 503 that is not a bug and a missing post that is not an outage. That is more contract than "here is a number", and some callers will not read it.

The payoff is narrow and, I think, worth it: nobody using this can act on a stale figure believing it is current. Not because they were careful, but because the system would not let them.

## Look at it yourself

Everything above is open, and every claim resolves to something you can read:

- The live endpoint: [`/api/readiness`](https://bitcoinriskbrief.minihub.app/api/readiness)
- How freshness and validation work: [docs.bitcoinriskbrief.minihub.app](https://docs.bitcoinriskbrief.minihub.app/engineering/freshness-and-validation/)
- The code: [github.com/akarazhev/bitcoin-risk-brief](https://github.com/akarazhev/bitcoin-risk-brief) — `backend/app/readiness.py`, `backend/app/public_cache.py`, `collector/collector/publisher.py`

The product is a research and analytics tool, not financial advice — but that is not really what this post was about. The argument generalises to anything that serves derived data on a schedule: a nightly aggregate, a daily report, a model output, a cached rollup. If your system knows the data is old and answers anyway, it is not being helpful. It is guessing on the reader's behalf, and not telling them.
