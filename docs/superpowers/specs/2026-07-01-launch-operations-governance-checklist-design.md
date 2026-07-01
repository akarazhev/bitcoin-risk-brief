# Launch Operations And Governance Checklist Design

> Status: future-facing launch completeness checklist. Last reviewed 2026-07-01. This complements production readiness,
> security, operations, and portfolio presentation docs; it does not add product scope.

## Goal

Capture the non-feature work that should be checked before public traffic or before the project is shown as a mature
private/portfolio product.

The goal is to avoid a technically working product with missing operational, privacy, maintenance, or ownership details.

## Scope

This checklist covers:

- privacy, terms, retention, and disclaimer copy;
- post-waitlist handling;
- dependency and security maintenance;
- disk, cost, resource, and account monitoring;
- credential and account ownership;
- data-source terms and attribution;
- SEO, social preview, favicon, and basic share metadata;
- accessibility checks;
- incident response runbooks.

It should be completed after core implementation stabilizes and before broad external exposure.

## Privacy, Terms, And Disclaimer

Before active traffic, decide whether the public product needs:

- a short privacy policy for waitlist contacts, operational logs, and future analytics;
- a short terms or usage note for the public risk signal;
- a retention policy for waitlist contacts and future raw analytics events;
- contact-removal instructions;
- clear no-financial-advice language in the page, README, and product brief.

If persisted analytics are implemented, the privacy copy must say what is collected, what is not collected, how long raw
events are kept, and whether any data is joined to waitlist contacts.

## Post-Waitlist Workflow

The waitlist should not be a dead end. Before first traffic, define:

- who receives and reviews waitlist leads;
- how often leads are reviewed;
- first outreach message template;
- how users can unsubscribe or request deletion;
- which source values are used for attribution;
- what counts as a strong demand signal versus a weak signal.

The product can still start with manual outreach. Automated email or Telegram delivery is a later feature.

## Dependency And Security Maintenance

Define a maintenance cadence for:

- base container images;
- Python dependencies;
- frontend npm dependencies;
- GitHub Actions versions;
- security advisories;
- vulnerability or secret scans before external sharing.

This can start as a monthly manual review. Dependabot, Renovate, or automated security scanning can be added later if the
project becomes active enough to justify alert noise.

## Monitoring And Resource Ownership

Beyond `/api/readiness`, the operator should know how to monitor:

- disk usage and database volume growth;
- backup directory growth;
- container restart loops;
- Cloudflare Tunnel connector health;
- domain and Cloudflare account renewal or ownership;
- public hostname availability;
- cost or resource limits if the project moves to paid infrastructure.

These checks can be manual for the first pilot, but they should be named in the runbook.

## Credential And Account Ownership

Document ownership and recovery paths for:

- GitHub repository access;
- Cloudflare account, zone, tunnel, and API token;
- domain registration if a custom domain is used;
- production `.env` storage;
- backup storage;
- server login or physical access;
- optional CoinMarketCap API key if configured.

Do not commit secrets. Document where they are managed and who can recover access.

## Data Source Terms And Attribution

Before relying on a source in production or research, record:

- source URL;
- retrieval method;
- observed rate limits or availability limits;
- licensing or terms notes;
- attribution requirements;
- whether commercial or portfolio use is acceptable;
- fallback behavior when the source is unavailable.

This applies to CoinMarketCap public CSV use, optional CoinMarketCap API use, and future methodology research sources
such as Alternative.me or Coin Metrics.

## SEO, Social Preview, And Basic Metadata

If the public page or portfolio link will be shared, verify:

- page title;
- meta description;
- favicon;
- Open Graph title, description, and image;
- readable social share text;
- screenshot or preview image that does not imply financial advice.

This is presentation polish, not a reason to add broad marketing pages.

## Accessibility

Before public traffic, run a focused accessibility pass:

- keyboard navigation;
- visible focus states;
- form labels and error states;
- chart fallbacks or surrounding text that conveys meaning;
- color contrast for risk states and badges;
- mobile text fit without overlap;
- screen-reader labels for language switch, waitlist, readiness, and charts.

The goal is a usable first screen and waitlist flow, not a full accessibility certification.

## Incident Response

Create a short "first 15 minutes" runbook for:

- `/api/readiness` degraded or non-200;
- scheduled data refresh failure;
- CoinMarketCap public download failure;
- waitlist submission failure;
- Cloudflare Tunnel down;
- public cache serving stale data;
- backup failure;
- database volume or disk space pressure.

Each entry should include where to look first, which command or dashboard to check, and what action is safe to take.

## Non-Goals

This checklist does not require:

- a legal review before a small private pilot unless the launch context demands it;
- automated email or Telegram campaigns;
- a full admin dashboard;
- full SOC/security compliance;
- a public support process;
- multi-user account management.

## Acceptance Criteria

- Production readiness docs name the chosen privacy/terms/disclaimer posture.
- Waitlist leads have an owner, manual handling process, and deletion/unsubscribe path.
- Operations docs identify disk/resource checks, account ownership, and first-response runbooks.
- Security docs explain retention and data-source terms checks before adding new data or analytics sources.
- Testing docs include accessibility, metadata, and dependency/security maintenance checks for launch.
- Portfolio presentation docs stay consistent with the implemented product and do not overstate operational maturity.
