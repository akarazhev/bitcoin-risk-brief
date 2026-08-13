# First Article Design: Refusing To Answer

> Status: approved 2026-08-12. First increment of sub-project S6a, tracked by issue #50.
> Covers one article in two languages. The rest of the S6a subject list stays open.

## Goal

Publish the first article of the series: a transferable engineering argument, with this product as the
worked example rather than the subject.

## Publication

| Decision | Choice |
| --- | --- |
| Canonical copy | The documentation site, as plain pages under `Articles` |
| English syndication | [dev.to](https://dev.to), with `canonical_url` pointing home |
| Russian syndication | [Habr](https://habr.com), indicating the original |
| Aggregators | Hacker News, Lobsters, r/programming — submitted, not published to |
| Social | One X thread per article, a pointer rather than a serialisation |
| Languages | Both, written separately rather than translated |
| Byline | Andrey Karazhev. Drafts are prepared for editing, not published as written. |

**Why the canonical lives at home.** An earlier revision of this design put the articles on external
platforms only, reasoning that an own blog starts with no audience. That reasoning holds for human
reach and misses citation: when an AI assistant answers a question by quoting an article, it cites the
URL it found, and a piece published only to dev.to associates the argument with dev.to. Owning the
canonical costs nothing here — two articles are plain pages in the existing navigation, and the blog
plugin with dated indexes and feeds is not worth adding until there are ten.

**Why syndicate anyway.** The reach argument was never wrong, only incomplete. dev.to and Habr carry
the audience; the aggregators carry most of the traffic that reaches technical writing at all. Submit
to them, do not publish there.

**Why not Medium.** A third long-form venue for the same text dilutes rather than multiplies — search
and readers both discount duplicates — and its technical audience has thinned. A third venue is better
spent on a second subject.

**Why written separately.** A direct translation from English reads as a translation on Habr, where the
audience is technical and unforgiving of it. The argument and the evidence are shared; the prose is not.

## The Argument

**Freshness is part of the answer.** An API that returns a number without its freshness state lies by
omission. An API that returns a stale number while knowing it is stale simply lies.

The article generalises past crypto and past this product: any system serving derived data on a schedule
faces the same decision, and most of them answer it by shipping a figure and letting the reader guess how
old it is.

## Approach

Three were considered.

A **case study** — what we built, chronologically — was rejected: an unknown product gives a reader no
reason to start, and the result reads as self-promotion.

A **bug-story** article — the three failures of the past week — is concrete and engaging, but three war
stories without a unifying claim is a changelog.

The chosen approach is **thesis-first with the product as evidence**, using the bug stories as the
material that keeps the thesis from floating. The reader leaves with something portable; the product is
proof, not subject.

## Structure

1. **A daily data product.** The value is worth exactly what its date is worth.
2. **What most dashboards do.** Show the figure, leave the age to be inferred. Name the failure mode:
   a reader acting on yesterday's number believing it is today's.
3. **Readiness as an endpoint.** `/api/readiness` with its real payload, and HTTP 503 when the data is
   stale or validation failed. The check names, not a summary of them.
4. **The cache is harder.** `X-Cache-Version` is derived from the validation row, not from a clock. Why
   a TTL is the wrong instrument: time does not know whether the underlying import succeeded, so a
   cache can outlive the data it describes while still being "fresh" by its own reckoning.
5. **The broadcast is hardest.** A channel post is read hours later, alone, with no freshness badge
   beside it. So its gate is stricter than the API's: publish only when the observation covers the last
   completed UTC day. The consequence is stated plainly — missed days become possible and do not
   self-heal.
6. **What it costs.** You must decide what "current" means and defend it. Silence becomes a valid
   output, which is uncomfortable to ship and harder to explain than a number.
7. **Open it yourself.** Repository, the freshness and validation reference, the live endpoint.

## Evidence Used

Every claim resolves to something the reader can open.

- `https://bitcoinriskbrief.minihub.app/api/readiness` — the live payload, including a `503` example
  described rather than fabricated.
- `https://docs.bitcoinriskbrief.minihub.app/engineering/freshness-and-validation/`
- `https://github.com/akarazhev/bitcoin-risk-brief` — `backend/app/readiness.py`,
  `backend/app/public_cache.py`, `collector/collector/publisher.py`.

Three incidents from implementation supply the concrete turns:

- the claim-then-confirm race, where `ON CONFLICT DO NOTHING` protected the table but not the channel;
- the publisher gate that prefers a missed post to a late one;
- the CI that reported green on two dependency updates while building none of the images they changed.

The third belongs in this article only as a single line about verification being narrower than it looks.
It is the seed of a separate piece and should not be spent here.

## Constraints

- Roughly 1200-1800 words. Long enough for the cache and broadcast sections to earn their place; short
  enough to be read once.
- **No claim the reader cannot verify.** Every assertion links to code, a live endpoint, or a document.
- **No financial framing.** The product is analytics and research context, and the article says so once,
  in passing, without turning into a disclaimer.
- No claims about adoption, accuracy, traffic, or product-market fit. There are five waitlist leads and
  a channel a day old; the article's authority comes from the engineering, not from an audience.
- Code samples are real, copied from the repository, not illustrative rewrites.
- The Russian version carries the same argument, structure, and evidence, in native prose.

## Non-Goals

- The remaining S6a subjects. Each gets its own increment.
- A blog section on the documentation site.
- Medium, and any further duplicate of the same text.
- A blog plugin, dated indexes, tags or feeds — plain pages until the volume justifies more.
- Writing for the product audience. This is an engineering piece and it brings engineers; a article for
  Bitcoin holders is a different subject under a different goal, and that audience stays deprioritised.
- Video, threads, or promotion mechanics — publication is the deliverable here.
- Any change to product code. If writing exposes a defect, it becomes an issue, not an edit inside this
  work.

## Acceptance Criteria

- The English draft is publishable on dev.to and the Russian draft on Habr, each in its own voice.
- Every external claim resolves to a repository path, a live URL, or a documentation page.
- A reader who has never heard of this product can restate the thesis after one read.
- Nothing in either draft asserts adoption, accuracy, or investment value.
- The three incidents appear as evidence for the argument, not as a narrative of the week.
