# Operator Launch Decision Packet Template

This template helps the operator collect the missing first-traffic governance decisions for Bitcoin Risk Brief in a
safe, consistent format.

This file is a template, not completed evidence. It does not prove that any launch decision has been made, that any
operator record exists, or that first traffic is allowed. Do not treat example wording as a decision.

## Purpose And Safety Rules

Use this packet to prepare sanitized launch-governance answers before updating the launch register in
[Production Readiness](production-readiness.md). The packet should make each decision explicit without committing
private operational details to Git.

Safety rules:

- Do not invent decisions.
- Record only sanitized final outcomes, accepted limitations, or pending/blocked status.
- Keep private operational details outside Git.
- Do not record names, emails, handles, phone numbers, dashboard URLs, account IDs, tokens, private paths, raw logs, raw
  waitlist contacts, raw backup contents, `.env` values, or secret locations.
- Keep status language conservative when evidence is incomplete.
- Do not change a blocker to `passed` unless real sanitized operator evidence exists.
- Do not use this template as launch evidence by itself.

## How To Use This Packet

1. Copy this template into an operator-controlled location outside Git.
2. Fill the copy with real decisions, sanitized evidence summaries, or explicit accepted limitations.
3. Review the completed copy for forbidden private data before anything is copied into the repository.
4. Copy only the final sanitized decisions into [Production Readiness](production-readiness.md).
5. Keep private operational details, private source records, account recovery details, raw waitlist data, and private
   evidence artifacts outside Git.

## Status Values

Each decision area must use one of these exact status values:

- `passed`
- `accepted limitation`
- `partial`
- `pending`
- `blocked`

Use `passed` only when the required decision is complete and sanitized evidence can be recorded. Use
`accepted limitation` when the operator deliberately accepts a known gap for an operator-watched pilot. Use `partial`
when some required fields are real but incomplete. Use `pending` when the decision has not been made. Use `blocked` when
the decision cannot be made without missing external access, evidence, or operator action.

## Waitlist Handling

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Exact sanitized fields the operator must provide:

- Status.
- Owner role, not a person name.
- Review cadence.
- Retention period or explicit retention deferral.
- Deletion request handling status.
- Unsubscribe or stop-contact handling status.
- Operator access scope by role category.
- Public copy/update needed, if any.
- Sanitized evidence date or decision date.

Acceptable sanitized wording examples:

- `Status: passed. Owner role: operations maintainer. Review cadence: weekly during the pilot. Retention: delete
  unresolved leads 90 days after pilot close. Deletion and unsubscribe requests are handled through the public contact
  path. Access is limited to operator roles that handle pilot outreach.`
- `Status: accepted limitation. Retention period is deferred until the pilot ends; deletion and unsubscribe handling are
  still available through the chosen public contact path.`
- `Status: pending. Owner role and retention period are not yet chosen.`

Do not record:

- Waitlist contact values, normalized contacts, raw database rows, raw exports, raw request bodies, or screenshots with
  contacts.
- Names, emails, handles, phone numbers, private inboxes, private chat links, or personal contact details.
- Private deletion request details or private outreach notes.
- Dashboard URLs, account IDs, private paths, raw logs, tokens, or `.env` values.

## Support/Contact Path

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Exact sanitized fields the operator must provide:

- Status.
- Public contact path type.
- Covered request types.
- Publication status for the path.
- No-paid-SLA posture or explicit support limitation.
- Escalation owner role, not a person name.
- Sanitized evidence date or decision date.

Acceptable sanitized wording examples:

- `Status: passed. Public contact path type: dedicated project contact address. Covered requests: deletion, unsubscribe,
  product questions, bug reports, professional/API interest, and license interest. No paid support SLA is promised.`
- `Status: accepted limitation. Public contact path is intentionally deferred for first traffic; the pilot remains
  operator-watched and no paid support SLA is offered.`
- `Status: partial. No paid support SLA is recorded, but the public contact path is still pending.`

Do not record:

- Actual email addresses, handles, phone numbers, names, personal profiles, private aliases, or recipient lists.
- Private support inbox URLs, helpdesk dashboard URLs, account IDs, routing rules, or escalation paths.
- Raw support messages, waitlist contacts, logs, tokens, or `.env` values.

## Credential/Account Recovery

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Exact sanitized fields the operator must provide:

- Status.
- Account categories covered, using categories only.
- Outside-Git owner/recovery record status.
- Recovery coverage status.
- Missing categories, if any.
- Accepted limitation, if any.
- Sanitized evidence date or decision date.

Acceptable sanitized wording examples:

- `Status: passed. Outside-Git owner/recovery record exists for GitHub, Cloudflare, production environment values,
  backup storage, server access, and optional data-source credentials. Recovery coverage is recorded outside Git.`
- `Status: partial. Outside-Git recovery record exists for repository and server access; domain and backup storage
  recovery status remain pending.`
- `Status: pending. No sanitized statement confirms that an outside-Git owner/recovery record exists.`

Do not record:

- Account holder names, emails, handles, phone numbers, account IDs, dashboard URLs, tenant IDs, zone IDs, repository
  invite lists, or domain registrar details.
- Secret locations, recovery codes, 2FA setup details, password manager paths, token names, token values, or `.env`
  values.
- Private server paths, backup paths, raw account exports, screenshots, or raw logs.

## Data-Source Terms And Attribution

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Exact sanitized fields the operator must provide:

- Status.
- Source categories reviewed.
- Retrieval methods covered.
- Attribution requirement status.
- Usage limitation or commercial/portfolio limitation, if any.
- Fallback source posture, if any.
- Sanitized evidence date or decision date.

Acceptable sanitized wording examples:

- `Status: passed. CoinMarketCap public CSV use and optional API use were reviewed for pilot usage. Attribution
  requirement status is recorded outside Git, and public copy needs no additional attribution change for the pilot.`
- `Status: accepted limitation. Public CSV pilot use is accepted for the controlled first-traffic window; commercial,
  portfolio, or redistribution claims remain blocked until a fuller source-rights review is complete.`
- `Status: pending. No completed source terms or attribution review outcome is recorded.`

Do not record:

- Private account terms, paid-plan details, account IDs, dashboard URLs, API keys, token names, or `.env` values.
- Raw terms text copied from a private account, private legal advice, or private source-provider correspondence.
- Raw source files, raw CSV rows, private archive paths, or raw import logs.

## Cloudflare Free-Plan First-Traffic Decision

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Exact sanitized fields the operator must provide:

- Status.
- Decision: accept current Free-plan subset for first traffic or require upgrade before first traffic.
- Covered controls in the accepted subset.
- Missing Free-plan controls or upgrade requirements.
- Operator watch requirement for first traffic.
- Sanitized evidence date or decision date.

Acceptable sanitized wording examples:

- `Status: accepted limitation. The current Free-plan-compatible subset is accepted for one operator-watched first-traffic
  window. The limitation is that managed WAF execution, broader /api/* burst limiting, multiple rate-limit rules, and
  longer rate-limit windows are not available in the current subset.`
- `Status: blocked. First traffic requires a plan upgrade or equivalent controls before the launch window.`
- `Status: pending. No operator decision has accepted the Free-plan subset or required an upgrade.`

Do not record:

- Cloudflare account IDs, zone IDs, tunnel IDs, dashboard URLs, API tokens, rule IDs, private screenshots, or private
  event logs.
- Internal IP addresses, connector names tied to private infrastructure, private routing details, or `.env` values.
- Any claim that broader controls are active unless sanitized evidence proves it.

## Accessibility Launch Decision

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Exact sanitized fields the operator must provide:

- Status.
- Evidence categories accepted as sufficient for first traffic.
- Missing manual/native/assistive-technology categories.
- Decision: require more evidence before first traffic or accept limitations for the pilot.
- Follow-up owner role, not a person name.
- Sanitized evidence date or decision date.

Acceptable sanitized wording examples:

- `Status: accepted limitation. Local automated axe, chart alternative, live-region, and keyboard/focus evidence are
  accepted for an operator-watched first-traffic window. Manual keyboard, screen-reader/assistive-tech,
  physical-device/native browser, and production-host accessibility evidence remain follow-up items.`
- `Status: blocked. First traffic requires manual keyboard and screen-reader checks before the launch window.`
- `Status: partial. Automated local evidence exists, but no operator decision accepts the remaining manual/native gaps.`

Do not record:

- Tester names, personal device identifiers, private browser profiles, screenshots with private data, raw assistive-tech
  logs, or private issue reports.
- Private account details, dashboard URLs, raw logs, waitlist contacts, tokens, or `.env` values.
- Full compliance claims unless an actual accessibility/WCAG review supports them.

## Restore Drill Status

Allowed status values: `passed`, `accepted limitation`, `partial`, `pending`, `blocked`.

Exact sanitized fields the operator must provide:

- Status.
- Restore target type.
- Restore drill result.
- Backup artifact category coverage.
- Checksum verification status.
- Readiness result after restore, if a drill was run.
- Deferred reason, if no safe target exists.
- Sanitized evidence date or decision date.

Acceptable sanitized wording examples:

- `Status: accepted limitation. Restore drill is deferred because only the live production server exists. A restore drill
  must wait for a staging project or intentionally empty restore target; no live-production restore testing is allowed.`
- `Status: passed. Restore drill completed on an intentionally empty target. PostgreSQL dump, canonical BTC CSV,
  manifest, and checksum categories were verified, and readiness passed after restore.`
- `Status: blocked. Backup artifacts exist, but no safe restore target is available and no accepted limitation has been
  recorded.`

Do not record:

- Private backup paths, raw backup contents, raw dump contents, raw CSV contents, raw restore logs, database connection
  strings, credentials, or `.env` values.
- Server hostnames, account IDs, storage dashboard URLs, private mount paths, names, emails, handles, or phone numbers.
- Any restore-drill pass claim from live production testing.

## Ready To Record?

Launch governance can be updated only when each required area has a real sanitized answer or an explicit accepted
limitation.

Before copying final decisions into [Production Readiness](production-readiness.md), verify:

- Each decision area uses one allowed status value.
- Every `passed` status is backed by real sanitized operator evidence.
- Every `accepted limitation` names the limitation and why it is acceptable for the operator-watched pilot.
- Every `partial`, `pending`, or `blocked` status keeps launch governance partial/blocked.
- Waitlist handling has a real owner role, cadence, retention or deferral, deletion handling, and unsubscribe handling,
  or an explicit accepted limitation.
- Support/contact path has a real public path decision or an explicit accepted limitation.
- Credential/account recovery has a sanitized outside-Git record status or remains pending/blocked.
- Data-source terms and attribution has a sanitized review outcome or remains pending/blocked.
- Cloudflare first-traffic posture either accepts the Free-plan subset with the documented limitations or requires an
  upgrade before first traffic.
- Accessibility launch posture either accepts the remaining manual/native gaps for the pilot or blocks first traffic
  until the missing checks are done.
- Restore drill status either records a real safe-target drill or explicitly defers the drill because no safe target
  exists.
- The final repository note contains no names, emails, handles, phone numbers, dashboard URLs, account IDs, tokens,
  private paths, raw logs, raw waitlist contacts, raw backup contents, `.env` values, or secret locations.
