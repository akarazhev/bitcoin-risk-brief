# Articles

Drafts and published pieces about the engineering behind this product.

These files live outside `docs/` on purpose: the documentation site builds everything under `docs/`,
and an unfinished draft has no business on a published site.

## The two locations are the status

| Location | Meaning |
| --- | --- |
| `articles/` | Draft. Not on the site, not published anywhere. |
| `docs/articles/` | Canonical published version, live on the documentation site. |

A piece is promoted by **moving** it, never by copying. One file, one location, and the path says
whether it is published. Two copies of the same text would drift, and the drift would be invisible
until a reader found both.

## Promoting a draft

1. The author rewrites the draft in their own voice. This is a rewrite, not a proofread — a piece that
   reads as machine-written costs more than no piece at all.
2. `git mv` it from `articles/` to `docs/articles/`, and delete the draft header comment.
3. Add it to the `Articles` section of `mkdocs.yml`. Create that section if it is the first one.
4. Syndicate: dev.to with `canonical_url` pointing at the documentation site, Habr indicating the
   original. Then submit to Hacker News, Lobsters and r/programming, and post one X thread pointing at
   the canonical.
5. Update the table below with the live URLs.

Each draft carries a header comment stating its status, its intended venue, and the design document it
follows. A draft is raw material — structure, facts and verified links — prepared for the author to
rewrite in their own voice before publication.

Every claim in a published piece must resolve to code, a live endpoint, or a documentation page. No
piece asserts adoption, accuracy, or investment value, and none frames the product as financial advice.

| Draft | Venue | Status |
| --- | --- | --- |
| [Your API should refuse to answer](2026-08-12-refusing-to-answer.en.md) | dev.to | Awaiting rewrite |
| [API, который отказывается отвечать](2026-08-12-refusing-to-answer.ru.md) | Habr | Awaiting rewrite |
