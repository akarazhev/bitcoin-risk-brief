# Cloudflare Zone And Email Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the active `minihub.app` zone HTTPS-only with TLS 1.2+, HSTS, and a verified strict DMARC policy while preserving the existing Tunnel, DNS, and rulesets.

**Architecture:** Treat Cloudflare as externally managed production state. Every mutation is preceded by an exact-state read and followed by API plus public-network verification; account IDs, zone IDs, mail headers, and DMARC reports remain outside Git.

**Tech Stack:** Cloudflare Zone Settings API, Cloudflare DNS API, public DNS, curl/OpenSSL, Zoho Mail.

## Global Constraints

- Work only on `minihub.app`; never inspect or mutate `minhub.app`.
- Do not add apex or `www` web records.
- Preserve the proxied `bitcoinriskbrief.minihub.app` Tunnel record and every existing managed/custom ruleset.
- Enable HSTS immediately with `max_age=15552000`, `include_subdomains=true`, `preload=false`, and `nosniff=true`.
- Set `always_use_https=on`, `min_tls_version=1.2`, and retain `tls_1_3=on`.
- Publish exactly `v=DMARC1; p=reject; rua=mailto:dmarc@minihub.app; pct=100` only after Zoho alignment preflight passes.
- Never commit account IDs, zone IDs, raw `Authentication-Results`, DMARC XML reports, tokens, or private mailbox details.

---

### Task 1: Establish the mutation gate and mail-alignment preflight

**Files:**
- Read: `docs/superpowers/specs/2026-08-04-cloudflare-turnstile-zone-hardening-design.md`
- Modify: none

**Interfaces:**
- Consumes: the authenticated Cloudflare account connector and the existing Zoho sender for `minihub.app`.
- Produces: confirmed zone identity, exact rollback values held only in the active execution context, and a pass/fail Zoho alignment decision.

- [ ] **Step 1: Re-read the active zone and abort on ambiguity**

Use the Cloudflare API schema search tool for `GET /zones` and `GET /zones/{zone_id}/settings/{setting_id}`, then run a read-only API call equivalent to:

```js
async () => {
  const zones = await cloudflare.request({
    method: 'GET',
    path: '/zones',
    query: { name: 'minihub.app', per_page: 20 },
  });
  if (!zones.success || zones.result.length !== 1) throw new Error('expected one minihub.app zone');
  const zone = zones.result[0];
  if (zone.name !== 'minihub.app' || zone.status !== 'active' || zone.paused) {
    throw new Error('minihub.app zone is not active and unpaused');
  }
  return { id: zone.id, name: zone.name, status: zone.status, paused: zone.paused };
}
```

Expected: exactly one active, unpaused `minihub.app` zone. Keep the returned zone ID in execution memory only.

- [ ] **Step 2: Capture exact rollback values without writing them to Git**

Read `always_use_https`, `min_tls_version`, `tls_1_3`, and `security_header`; read all DNS records and filter `_dmarc.minihub.app`.

Expected pre-change state from the 2026-08-04 audit:

```json
{
  "always_use_https": "off",
  "min_tls_version": "1.0",
  "tls_1_3": "on",
  "security_header": {
    "strict_transport_security": {
      "enabled": false,
      "max_age": 0,
      "include_subdomains": false,
      "preload": false,
      "nosniff": false
    }
  },
  "dmarc_record_count": 0
}
```

If current state differs, report the drift and stop before mutation unless the new state already equals the target.

- [ ] **Step 3: Verify Zoho alignment before publishing `p=reject`**

The operator sends one message from an existing `@minihub.app` Zoho mailbox to a mailbox that exposes full authentication results. Accept the gate only when the recipient shows at least one aligned pass:

```text
dkim=pass with header.d=minihub.app
```

or:

```text
spf=pass with an RFC5321.MailFrom domain aligned to minihub.app
```

Do not copy the full header or recipient address into Git. Record only `Zoho alignment preflight: pass` in the active execution update.

Expected: pass. On failure, stop and repair Zoho SPF/DKIM before Task 3.

### Task 2: Enforce HTTPS, TLS 1.2, and HSTS

**Files:**
- Modify: none

**Interfaces:**
- Consumes: the exact `minihub.app` zone ID resolved in Task 1.
- Produces: zone settings `always_use_https=on`, `min_tls_version=1.2`, `tls_1_3=on`, and the approved HSTS object.

- [ ] **Step 1: Retrieve the current edit-setting schema**

Search the Cloudflare OpenAPI schema for `PATCH /zones/{zone_id}/settings/{setting_id}` immediately before mutation.

Expected: the endpoint accepts an object containing `value` for all three settings used below.

- [ ] **Step 2: Apply the three setting changes**

Run the following through the authenticated Cloudflare API executor. It resolves and validates the zone again inside the same operation before applying changes:

```js
async () => {
  const zones = await cloudflare.request({
    method: 'GET',
    path: '/zones',
    query: { name: 'minihub.app', per_page: 20 },
  });
  if (!zones.success || zones.result.length !== 1) {
    throw new Error('expected one minihub.app zone');
  }
  const zone = zones.result[0];
  if (zone.name !== 'minihub.app' || zone.status !== 'active' || zone.paused) {
    throw new Error('minihub.app zone is not active and unpaused');
  }
  const zoneId = zone.id;
  const changes = [
    ['always_use_https', { value: 'on' }],
    ['min_tls_version', { value: '1.2' }],
    ['security_header', {
      value: {
        strict_transport_security: {
          enabled: true,
          max_age: 15552000,
          include_subdomains: true,
          preload: false,
          nosniff: true,
        },
      },
    }],
  ];
  const applied = [];
  for (const [settingId, body] of changes) {
    const response = await cloudflare.request({
      method: 'PATCH',
      path: `/zones/${zoneId}/settings/${settingId}`,
      body,
    });
    if (!response.success) throw new Error(`${settingId} update failed`);
    applied.push({ id: settingId, value: response.result.value });
  }
  return applied;
}
```

Expected: all three updates return `success=true`.

- [ ] **Step 3: Verify API state and preserved neighboring configuration**

Re-read the four settings plus the zone's DNS records, Worker routes, Tunnel list, and custom rulesets.

Expected:

```json
{
  "always_use_https": "on",
  "min_tls_version": "1.2",
  "tls_1_3": "on",
  "hsts_enabled": true,
  "hsts_max_age": 15552000,
  "hsts_include_subdomains": true,
  "hsts_preload": false,
  "hsts_nosniff": true
}
```

Also expect the `bitcoinriskbrief.minihub.app` proxied Tunnel CNAME, three custom Bitcoin Risk Brief rulesets, and healthy `cubi-prod-01` Tunnel to remain present.

- [ ] **Step 4: Verify public HTTP/TLS behavior**

Run:

```bash
curl -sSI --max-time 15 http://bitcoinriskbrief.minihub.app
curl -sSI --max-time 15 https://bitcoinriskbrief.minihub.app
curl -sS --tls-max 1.1 -o /dev/null --max-time 15 https://bitcoinriskbrief.minihub.app
curl -sS --tlsv1.2 -o /dev/null -w '%{http_code}\n' --max-time 15 https://bitcoinriskbrief.minihub.app
```

Expected:

- HTTP returns a 301 or 308 redirect to the same HTTPS URL.
- HTTPS returns 200 and `Strict-Transport-Security: max-age=15552000; includeSubDomains`.
- TLS 1.1-or-lower connection fails.
- TLS 1.2 connection returns 200.

### Task 3: Publish and verify strict DMARC

**Files:**
- Modify: none

**Interfaces:**
- Consumes: Task 1 Zoho alignment pass and exact absence of an existing `_dmarc.minihub.app` record.
- Produces: one public DMARC TXT record and a post-change `dmarc=pass` check.

- [ ] **Step 1: Recheck for a concurrent DMARC record**

Call `GET /zones/{zone_id}/dns_records?name=_dmarc.minihub.app&type=TXT`.

Expected: zero records. If one exists, compare it with the desired value and stop rather than create a duplicate.

- [ ] **Step 2: Create the record**

After retrieving the current `POST /zones/{zone_id}/dns_records` schema, create exactly:

```json
{
  "type": "TXT",
  "name": "_dmarc.minihub.app",
  "content": "v=DMARC1; p=reject; rua=mailto:dmarc@minihub.app; pct=100",
  "ttl": 3600,
  "proxied": false,
  "comment": "Strict DMARC policy; aggregate reports to the dedicated Zoho alias"
}
```

Expected: `success=true` and one created TXT record. Do not include the returned record or zone IDs in Git.

- [ ] **Step 3: Verify authoritative and public DNS**

Run:

```bash
dig +short _dmarc.minihub.app TXT @ned.ns.cloudflare.com
dig +short _dmarc.minihub.app TXT @zelda.ns.cloudflare.com
dig +short _dmarc.minihub.app TXT
```

Expected from each resolver:

```text
"v=DMARC1; p=reject; rua=mailto:dmarc@minihub.app; pct=100"
```

- [ ] **Step 4: Verify post-change DMARC pass**

The operator sends a second approved message from Zoho and checks the recipient's authentication summary.

Expected:

```text
dmarc=pass header.from=minihub.app
```

Do not commit the header, recipient, message content, or DMARC XML reports.

### Task 4: Document the applied state

**Files:**
- Modify: `docs/deploy-ubuntu-cloudflare.md:183-205`
- Modify: `docs/security-and-privacy.md:1-35`
- Modify: `docs/operations.md:896-909`

**Interfaces:**
- Consumes: verified results from Tasks 2 and 3.
- Produces: sanitized operational truth without IDs, secrets, addresses beyond the intentional DMARC alias, or private evidence.

- [ ] **Step 1: Update the documentation**

Record these exact public facts:

```markdown
- Always Use HTTPS is enabled for the `minihub.app` zone.
- Minimum TLS is 1.2 and TLS 1.3 remains enabled.
- HSTS is enabled for six months with subdomains included and preload disabled.
- `_dmarc.minihub.app` uses `p=reject`; aggregate reports go to the dedicated `dmarc@minihub.app` alias.
- Apex and `www` web records remain intentionally absent until future landing pages are deployed.
```

Retain the warning that cached HSTS cannot be immediately rolled back.

- [ ] **Step 2: Verify the documentation diff**

Run:

```bash
git diff --check
rg -n "Always Use HTTPS|TLS 1\.2|HSTS|p=reject|dmarc@minihub\.app|apex|www" docs/deploy-ubuntu-cloudflare.md docs/security-and-privacy.md docs/operations.md
```

Expected: no whitespace errors and all applied settings documented.

- [ ] **Step 3: Commit**

```bash
git add docs/deploy-ubuntu-cloudflare.md docs/security-and-privacy.md docs/operations.md
git commit -m "docs: record Cloudflare zone hardening"
```

Expected: one documentation-only commit after the external settings are publicly verified.
