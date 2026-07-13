# Cloudflare Analytics CSP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the production console CSP violation caused by Cloudflare Web Analytics beacon injection while preserving the app's strict CSP and no-product-analytics posture.

**Architecture:** Keep `script-src 'self'` and do not allow `static.cloudflareinsights.com`. Make the frontend origin explicitly reject intermediary HTML/script rewriting by serving static frontend responses with `Cache-Control` directives that include `no-transform`, while preserving backend API cache headers. Document the matching Cloudflare dashboard setting: Web Analytics automatic setup must be disabled unless a future analytics/privacy design intentionally changes the product posture.

**Tech Stack:** nginx frontend container, Python `unittest`, Markdown operations docs, Cloudflare Web Analytics dashboard.

---

## Context

GitHub issue #27 reports this browser console error:

```text
Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/v4513226cdae34746b4dedf0b4dfa099e1781791509496' violates the following Content Security Policy directive: "script-src 'self'".
```

The current frontend CSP is in `frontend/nginx.conf` and correctly allows scripts only from the app origin:

```text
script-src 'self'
```

The app source does not include the Cloudflare beacon. Cloudflare Web Analytics automatic setup can inject the Beacon script for proxied sites. Cloudflare's Web Analytics docs say proxied sites use automatic setup by default, and Manage Site can change automatic setup to `Disable` or manual JS snippet installation. The same docs note that `Cache-Control` with `no-transform` prevents Cloudflare from modifying the original payload and automatically injecting the Beacon script.

Reference for the implementing agent: https://developers.cloudflare.com/web-analytics/get-started/

## File Structure

- Create: `backend/tests/test_frontend_security_headers.py`
  - Owns static assertions for the frontend nginx security and cache-control posture.
- Modify: `frontend/nginx.conf`
  - Keeps API proxy behavior unchanged.
  - Keeps strict CSP.
  - Adds `no-transform` cache-control to non-API static frontend responses.
- Modify: `docs/security-and-privacy.md`
  - Records that Cloudflare Web Analytics automatic Beacon injection is intentionally disabled for the pilot.
- Modify: `docs/deploy-ubuntu-cloudflare.md`
  - Adds the Cloudflare dashboard setting and public verification commands.

Do not add Cloudflare Web Analytics scripts to `frontend/index.html`.
Do not add `https://static.cloudflareinsights.com` to any CSP directive.
Do not change backend API cache-control behavior.

---

### Task 1: Add Failing Frontend Security Header Tests

**Files:**
- Create: `backend/tests/test_frontend_security_headers.py`

- [ ] **Step 1: Create the failing test file**

Create `backend/tests/test_frontend_security_headers.py` with this exact content:

```python
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
NGINX_CONF = ROOT / "frontend" / "nginx.conf"


def _read_nginx_conf() -> str:
    return NGINX_CONF.read_text()


def _add_header_values(config: str, header_name: str) -> list[str]:
    pattern = re.compile(
        r"add_header\s+" + re.escape(header_name) + r'\s+"([^"]+)"\s+always;'
    )
    return pattern.findall(config)


def _location_block(config: str, location: str) -> str:
    pattern = re.compile(
        r"location\s+" + re.escape(location) + r"\s*\{(?P<body>.*?)\n\s*\}",
        re.DOTALL,
    )
    match = pattern.search(config)
    if match is None:
        raise AssertionError(f"location {location} block not found")
    return match.group("body")


def _csp_directives(csp: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for directive in csp.split(";"):
        parts = directive.strip().split()
        if parts:
            directives[parts[0]] = parts[1:]
    return directives


class FrontendSecurityHeaderTests(unittest.TestCase):
    def test_all_frontend_csp_headers_keep_scripts_self_only(self) -> None:
        headers = _add_header_values(_read_nginx_conf(), "Content-Security-Policy")

        self.assertGreaterEqual(len(headers), 1)
        for csp in headers:
            directives = _csp_directives(csp)
            self.assertEqual(["'self'"], directives["script-src"])
            self.assertNotIn("script-src-elem", directives)
            self.assertEqual(["'none'"], directives["frame-ancestors"])
            self.assertNotIn("static.cloudflareinsights.com", csp)
            self.assertNotIn("cloudflareinsights.com", csp)

    def test_static_frontend_responses_prevent_edge_script_injection(self) -> None:
        config = _read_nginx_conf()

        for location in ("/assets/", "/"):
            block = _location_block(config, location)
            cache_headers = _add_header_values(block, "Cache-Control")
            self.assertEqual(1, len(cache_headers), location)

            directives = {part.strip() for part in cache_headers[0].split(",")}
            self.assertIn("public", directives, location)
            self.assertIn("no-transform", directives, location)

    def test_api_proxy_does_not_replace_backend_cache_headers(self) -> None:
        block = _location_block(_read_nginx_conf(), "/api/")

        self.assertEqual([], _add_header_values(block, "Cache-Control"))
        self.assertIn("proxy_pass http://backend:8000/api/;", block)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the targeted test and verify it fails**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_frontend_security_headers -v
```

Expected result: failure in `test_static_frontend_responses_prevent_edge_script_injection` because the current `frontend/nginx.conf` has no `location /assets/` block and no static frontend `Cache-Control` header containing `no-transform`.

---

### Task 2: Add Origin Guardrails In Frontend nginx

**Files:**
- Modify: `frontend/nginx.conf`
- Test: `backend/tests/test_frontend_security_headers.py`

- [ ] **Step 1: Replace the frontend nginx config**

Replace the full contents of `frontend/nginx.conf` with:

```nginx
server {
  listen 3000;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  add_header X-Content-Type-Options "nosniff" always;
  add_header X-Frame-Options "DENY" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
  add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;

  location /api/ {
    proxy_pass http://backend:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /assets/ {
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;
    add_header Cache-Control "public, max-age=31536000, immutable, no-transform" always;
    try_files $uri =404;
  }

  location / {
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;
    add_header Cache-Control "public, max-age=0, must-revalidate, no-transform" always;
    try_files $uri $uri/ /index.html;
  }
}
```

Reason for repeated security headers: nginx `add_header` directives are inherited only when a child block has no `add_header` directives. Because the static locations need `Cache-Control`, they must repeat the security headers to keep the same CSP and browser protections.

- [ ] **Step 2: Run the targeted test and verify it passes**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_frontend_security_headers -v
```

Expected result:

```text
Ran 3 tests

OK
```

- [ ] **Step 3: Commit the nginx guardrail and test**

Run:

```bash
git add frontend/nginx.conf backend/tests/test_frontend_security_headers.py
git commit -m "fix: prevent frontend edge script injection"
```

---

### Task 3: Document Analytics And Cloudflare Dashboard Posture

**Files:**
- Modify: `docs/security-and-privacy.md`
- Modify: `docs/deploy-ubuntu-cloudflare.md`

- [ ] **Step 1: Update product analytics privacy documentation**

In `docs/security-and-privacy.md`, find this paragraph:

```markdown
As of the 2026-07-10 local source inspection, frontend and backend application code did not contain product analytics or
tracking-cookie code. Future source changes must recheck this before making any public no-analytics or no-cookie claim.
```

Replace it with:

```markdown
As of the 2026-07-10 local source inspection, frontend and backend application code did not contain product analytics or
tracking-cookie code. Future source changes must recheck this before making any public no-analytics or no-cookie claim.
Cloudflare Web Analytics automatic setup and Beacon injection are intentionally disabled for the production pilot. The
frontend CSP must not allow `static.cloudflareinsights.com` unless a later analytics/privacy design updates the public UI
copy, retention rules, and operator runbooks. Static frontend responses include `Cache-Control` directives with
`no-transform` so the Cloudflare proxy should not rewrite the HTML to inject third-party scripts.
```

- [ ] **Step 2: Update Cloudflare deployment guidance**

In `docs/deploy-ubuntu-cloudflare.md`, under `## Cloudflare Edge Settings`, find the `Recommended initial settings:` list.

After this existing bullet:

```markdown
- Bot/spam controls: enable the Cloudflare bot protection available on the active plan and start in a low-friction mode.
```

Insert:

```markdown
- Web Analytics automatic setup: disabled for this hostname unless a separate analytics/privacy design has been approved.
  In Cloudflare Web Analytics > Manage site, set automatic setup to `Disable` or use manual JS snippet installation with
  no snippet installed. Do not use automatic Beacon injection for the production pilot.
```

- [ ] **Step 3: Add public verification commands**

In `docs/deploy-ubuntu-cloudflare.md`, find this paragraph after the first public curl verification commands:

```markdown
Readiness should include `Cache-Control: no-store`. Cacheable product read responses should include `Cache-Control`,
`ETag`, and `X-Cache-Version`.
```

Replace it with:

```markdown
Readiness should include `Cache-Control: no-store`. Cacheable product read responses should include `Cache-Control`,
`ETag`, and `X-Cache-Version`.

Verify that the public frontend keeps the strict CSP and that Cloudflare did not inject the Web Analytics Beacon:

```bash
curl -sD /tmp/bitcoin-risk-root.headers -o /tmp/bitcoin-risk-root.html https://risk.example.com/
rg -i "^content-security-policy:|^cache-control:" /tmp/bitcoin-risk-root.headers
if rg -q "static\\.cloudflareinsights\\.com|beacon\\.min\\.js" /tmp/bitcoin-risk-root.html; then
  echo "unexpected Cloudflare Web Analytics beacon"
  exit 1
fi
```

The root headers should include `script-src 'self'` and a `Cache-Control` value with `no-transform`. The Beacon check
should exit successfully with no match.
```

- [ ] **Step 4: Review the documentation diff**

Run:

```bash
git diff -- docs/security-and-privacy.md docs/deploy-ubuntu-cloudflare.md
```

Expected result: the diff only documents the Cloudflare Web Analytics disabled posture, origin `no-transform` behavior, and public verification commands.

- [ ] **Step 5: Commit the documentation**

Run:

```bash
git add docs/security-and-privacy.md docs/deploy-ubuntu-cloudflare.md
git commit -m "docs: document Cloudflare analytics posture"
```

---

### Task 4: Run Full Local Verification

**Files:**
- Verify: `frontend/nginx.conf`
- Verify: `backend/tests/test_frontend_security_headers.py`
- Verify: `docs/security-and-privacy.md`
- Verify: `docs/deploy-ubuntu-cloudflare.md`

- [ ] **Step 1: Run the full Python test command**

Run:

```bash
./scripts/manage.sh test-python
```

Expected result: backend and collector unittest discovery both pass.

- [ ] **Step 2: Validate compose configuration**

Run:

```bash
./scripts/manage.sh validate
```

Expected result: compose configuration validates without errors.

- [ ] **Step 3: Check whitespace and markdown/code diff hygiene**

Run:

```bash
git diff --check
```

Expected result: no trailing whitespace or whitespace error output.

---

### Task 5: Production Operator Verification For Issue #27

**Files:**
- No repository files changed in this task.

- [ ] **Step 1: Disable Cloudflare Web Analytics automatic setup**

In the Cloudflare dashboard for the production hostname:

1. Open Web Analytics.
2. Open the site card for the Bitcoin Risk Brief hostname.
3. Open Manage site.
4. Set automatic setup to `Disable`, or set it to manual JS snippet installation and keep the snippet out of this repository.
5. Save the change.

If the implementing agent does not have Cloudflare dashboard access, do not mark GitHub issue #27 fixed. Leave a handoff note that the repo guardrail is merged but the operator setting still needs to be checked.

- [ ] **Step 2: Deploy the updated frontend**

Use the normal production deployment path for this repository. For the USB server-kit path, deploy the updated repository to `/srv/projects/bitcoin-risk-brief` and restart the stack using the documented server-kit update flow. For the direct git path, deploy under `/opt/bitcoin-risk-brief` and run the documented compose restart.

- [ ] **Step 3: Verify the public root response**

Run with the real production hostname:

```bash
PUBLIC_BASE_URL=https://risk.example.com
curl -sD /tmp/bitcoin-risk-root.headers -o /tmp/bitcoin-risk-root.html "${PUBLIC_BASE_URL}/"
rg -i "^content-security-policy:|^cache-control:" /tmp/bitcoin-risk-root.headers
if rg -q "static\\.cloudflareinsights\\.com|beacon\\.min\\.js" /tmp/bitcoin-risk-root.html; then
  echo "unexpected Cloudflare Web Analytics beacon"
  exit 1
fi
```

Expected result:

```text
content-security-policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
cache-control: public, max-age=0, must-revalidate, no-transform
```

The final `rg` check should find no Cloudflare beacon script.

- [ ] **Step 4: Verify the API cache headers were not overridden**

Run:

```bash
PUBLIC_BASE_URL=https://risk.example.com
curl -sD /tmp/bitcoin-risk-readiness.headers -o /tmp/bitcoin-risk-readiness.json "${PUBLIC_BASE_URL}/api/readiness"
curl -sD /tmp/bitcoin-risk-latest.headers -o /tmp/bitcoin-risk-latest.json "${PUBLIC_BASE_URL}/api/risk/latest"
rg -i "^cache-control:" /tmp/bitcoin-risk-readiness.headers /tmp/bitcoin-risk-latest.headers
```

Expected result:

```text
/tmp/bitcoin-risk-readiness.headers:cache-control: no-store
/tmp/bitcoin-risk-latest.headers:cache-control: public, max-age=60, stale-while-revalidate=300
```

The exact `max-age` may follow the configured production cache value, but readiness must remain `no-store` and latest risk must not inherit the frontend app-shell `max-age=0` header.

- [ ] **Step 5: Close or update GitHub issue #27**

If the public verification passes and browser DevTools no longer shows the blocked `static.cloudflareinsights.com/beacon.min.js` script, close issue #27 with a note that:

- CSP remains strict with `script-src 'self'`;
- origin static responses now include `no-transform`;
- Cloudflare Web Analytics automatic injection is disabled for the pilot;
- public root HTML contains no Cloudflare Beacon script.

If the public verification cannot be run, keep the issue open and comment that local repo verification passed but production Cloudflare dashboard/deploy verification remains.

---

## Self-Review Checklist

- The plan covers the reported console error without weakening CSP.
- The plan preserves the app's current no-product-analytics public posture.
- Tests fail before the nginx change and pass after the nginx change.
- Static frontend cache-control changes do not override backend API cache headers.
- Docs tell operators exactly how to configure Cloudflare and verify production.
- No task requires adding Cloudflare scripts to source code.
