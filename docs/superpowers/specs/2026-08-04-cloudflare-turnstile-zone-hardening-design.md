# Cloudflare Turnstile And Zone Hardening Design

**Date:** 2026-08-04
**Status:** Approved for implementation planning

## Objective

Harden the existing `bitcoinriskbrief.minihub.app` production pilot without expanding the product surface. The change
must force secure transport, reject forged mail claiming to come from `minihub.app`, and require a successful Cloudflare
Turnstile verification before a waitlist contact can be persisted.

This design applies only to `minihub.app`. The misspelled `minhub.app` is outside scope and must not be inspected or
changed further.

## Scope

### In scope

- Enable zone-wide HTTP-to-HTTPS redirects.
- Raise the zone minimum TLS version to TLS 1.2 while retaining TLS 1.3.
- Enable HSTS for six months with subdomains included and preload disabled.
- Publish a strict DMARC policy for `minihub.app`, with aggregate reports sent to the existing
  `dmarc@minihub.app` alias.
- Create a Cloudflare Turnstile Managed widget for `bitcoinriskbrief.minihub.app`.
- Integrate Turnstile into the React waitlist form without a third-party React wrapper.
- Verify every production waitlist token in FastAPI before writing a lead.
- Update CSP, environment templates, Compose/build wiring, tests, privacy copy, API documentation, security docs, and
  deployment instructions.
- Preserve the existing Cloudflare Tunnel, custom firewall rule, rate limit, and cache rules.

### Out of scope

- Adding web DNS records for `minihub.app` or `www.minihub.app`; future landing pages will address those hostnames.
- Changing or redirecting `minhub.app`.
- Adding a second Cloudflare Tunnel connector before a second always-on host exists.
- Enabling HSTS preload.
- Replacing the existing Cloudflare Tunnel or moving the application to Workers or Pages.
- Automating production deployment. The operator will prepare and apply the existing USB update flow.

## Architecture

The implementation uses Cloudflare's official Turnstile client script and canonical Siteverify API. It does not add a
React Turnstile wrapper.

1. The frontend renders the Managed widget explicitly for the selected UI locale.
2. A successful challenge produces a short-lived, single-use token.
3. The frontend sends the token with the existing contact, locale, and source fields to `POST /api/waitlist`.
4. FastAPI sends the token to Cloudflare Siteverify using the server-only secret.
5. FastAPI verifies a successful result, `action=waitlist`, and the configured expected hostname before calling
   `upsert_waitlist_lead`.
6. Invalid, expired, missing, or replayed tokens are rejected without a database write.
7. Siteverify transport failures or unusable upstream responses fail closed with HTTP 503.

The existing edge and application rate limits remain in place. Turnstile validates a submission, while rate limiting
continues to constrain bursts and direct API abuse.

## Frontend Design

### Widget lifecycle

- A small repository-owned React component loads the official Turnstile script and renders the widget explicitly.
- The widget is placed between the contact input and submit button.
- The submit button remains disabled until a token is available.
- Changing the selected UI locale re-renders the widget with that locale.
- Expiry, widget errors, and failed submissions clear the current token and reset the widget.
- A successful waitlist response clears the contact, retains the existing success announcement, and resets the widget.
- A failed response preserves the contact so the user can retry.

### Payload and configuration

`WaitlistRequest` gains a required `turnstile_token` field. The public Turnstile site key is provided through the
`VITE_TURNSTILE_SITE_KEY` Vite build argument and is safe to expose in the generated frontend. The widget sends the
fixed public action `waitlist`. Production builds must fail clearly when the site key is missing rather than producing
an unprotected form.

Local development and automated tests use Cloudflare's documented test keys. Production never disables Turnstile based
on a client-provided value.

### Accessibility and localization

- Existing polite submission status and assertive error announcements remain intact.
- Widget failures and verification failures receive localized messages in all seven supported locales.
- The privacy disclosure in every locale states that Cloudflare Turnstile is used to prevent automated submissions.
- Normal users should usually pass without interaction; Cloudflare may show a checkbox when additional verification is
  required.

## Backend Design

### Configuration

The backend receives the secret through `TURNSTILE_SECRET_KEY` and the expected production hostname through
`TURNSTILE_EXPECTED_HOSTNAME`. The expected action is the repository-owned constant `waitlist`. The secret must not be
committed, printed, placed in command arguments, embedded in frontend assets, or included in a USB package. Environment
example files contain placeholders or documented test values only.

### Verification module

A focused backend module owns Siteverify communication and response validation. It has one responsibility: turn an
untrusted token into either a verified result or a typed verification failure. The verifier uses a bounded timeout,
omits the optional visitor IP to minimize transmitted data, and never logs the token or secret.

The waitlist handler performs verification before contact normalization or persistence. The handler must prove through
tests that `upsert_waitlist_lead` is not called when verification fails.

### Error behavior

- Missing token: request validation failure, no database write.
- Invalid, expired, replayed, or wrong-action token: client-visible verification failure, no database write.
- Siteverify timeout, connection failure, malformed upstream response, or upstream service failure: HTTP 503, no
  database write.
- Successful verification: continue through the existing contact validation and persistence flow.

All waitlist responses, including verification failures, retain `Cache-Control: no-store` and `Pragma: no-cache`.

## Content Security Policy

The frontend CSP must allow only the Turnstile resources required by Cloudflare under
`https://challenges.cloudflare.com`. The implementation updates the required script, frame, and connection directives
without adding `unsafe-eval`, weakening `frame-ancestors`, or permitting Cloudflare Web Analytics. Existing
`no-transform` behavior remains in place.

Security-header tests will assert the exact Turnstile allowance and continue rejecting unrelated Cloudflare analytics
origins.

## Cloudflare Zone Configuration

The Cloudflare zone remains `minihub.app` on the Free plan.

- Enable `Always Use HTTPS` for the zone.
- Set the minimum TLS version to 1.2 and leave TLS 1.3 enabled.
- Enable HSTS with a six-month max age, `includeSubDomains` enabled, and preload disabled.
- Keep the current SSL mode unchanged. The active application reaches its local HTTP origin through an encrypted
  Cloudflare Tunnel.
- Keep the current proxied Tunnel DNS record for `bitcoinriskbrief.minihub.app`.
- Keep existing managed and custom rulesets, including waitlist challenge, waitlist rate limit, and API cache rules.
- Do not create apex or `www` web records.

HSTS is intentionally applied immediately. Rollback cannot remove a cached browser HSTS policy before its max age
expires, so HTTPS availability for every future served subdomain is an operational requirement.

## Email Authentication

Publish one DMARC TXT record at `_dmarc.minihub.app` with:

```text
v=DMARC1; p=reject; rua=mailto:dmarc@minihub.app; pct=100
```

The `dmarc@minihub.app` Zoho alias already exists. SPF and DKIM remain unchanged. Before publishing the immediate
`p=reject` policy, the operator must send an approved test message through Zoho and confirm that the recipient reports
aligned SPF or DKIM. After publication, a second approved message must report `dmarc=pass`. Aggregate DMARC XML reports
are operational mail and must not be committed.

## Build And Deployment

The site key is a frontend build input. Compose and the frontend Docker build must pass it explicitly at build time.
The Turnstile secret is a backend runtime environment value. The production `.env` stays on the server and is preserved
by the existing USB update process.

Deployment sequence:

1. Create the Turnstile Managed widget and record its public site key and private secret in operator-controlled storage.
2. Verify current Zoho SPF or DKIM alignment with an approved outbound message.
3. Apply the agreed HTTPS, TLS, HSTS, and DMARC zone changes.
4. Add the production site key, secret, and expected hostname to the server's existing `.env` through the documented
   operator workflow.
5. Build and validate the USB update from the implementation revision.
6. Apply the update with the existing backup-gated USB process.
7. Run local-origin and public-host verification before declaring the waitlist protected.

The USB package must not contain the production `.env`, Turnstile secret, raw DMARC reports, or test waitlist contacts.

## Testing And Verification

### Automated tests

- Backend verifier: success, invalid token, expired/replayed result, wrong action, timeout, connection failure, malformed
  response, and upstream failure.
- Waitlist handler: no persistence on every verification failure, persistence after success, and no-store headers on
  all outcomes.
- Frontend component: script/widget lifecycle, selected locale, token acquisition, expiry/error reset, and cleanup.
- Waitlist form: disabled-before-token behavior, token in payload, preserved contact on failure, reset on success, and
  accessible status/error announcements.
- Localization: Turnstile and privacy copy exists in every supported locale.
- CSP: only the required Turnstile origin is added and Cloudflare analytics remains disallowed.
- Configuration: environment and Compose/build wiring is complete without exposing the secret.

Required local verification commands include the repository's Python test suite, frontend tests, frontend production
build, and Compose validation.

### Public verification after USB deployment

- Plain HTTP redirects to HTTPS.
- TLS versions below 1.2 are rejected.
- HTTPS responses include the intended HSTS policy.
- `_dmarc.minihub.app` publishes the strict DMARC record.
- `GET /api/health` and `GET /api/readiness` remain healthy.
- A missing token and a documented invalid test token are rejected without persistence.
- One operator-approved test contact succeeds with a fresh valid token.
- Replaying that token is rejected.
- No request or application logs contain the token, secret, or raw contact value.

No production waitlist mutation may be performed without an operator-approved test contact.

## Failure And Rollback

- A misconfigured or unavailable Siteverify integration intentionally makes waitlist submission unavailable rather than
  storing unverified contacts.
- Application rollback uses the previous verified USB revision and preserved production `.env`.
- Turnstile can be removed only by rolling back both frontend token requirements and backend enforcement together.
- HTTPS redirect and TLS settings can be reverted in Cloudflare if necessary.
- HSTS cannot be immediately revoked for browsers that already cached it.
- DMARC can be changed through DNS, but cached records remain effective until their TTL expires.

## Success Criteria

- Every production waitlist write is preceded by a successful, expected-action Turnstile Siteverify result.
- Direct, missing-token, invalid-token, expired-token, and replay attempts do not persist leads.
- Existing waitlist validation, privacy constraints, rate limiting, and no-store behavior remain intact.
- The public site is HTTPS-only, refuses TLS below 1.2, and serves HSTS for the zone's hostnames.
- Mail claiming to originate from `minihub.app` is governed by a published `p=reject` DMARC policy with reports reaching
  the dedicated alias.
- The operator can build and deploy the implementation through the existing USB workflow without placing production
  secrets in Git or the USB package.
