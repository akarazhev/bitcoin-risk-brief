# Cloudflare CSP Review Follow-Ups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address the two minor post-merge review findings from PR #37 without changing product behavior or reopening the repo-side issue #27 fix.

**Architecture:** Keep the existing nginx security posture unchanged. Strengthen the static nginx regression test so child locations must repeat all security headers required by nginx `add_header` inheritance, and make the Cloudflare production verification snippet portable on a fresh Ubuntu host by using POSIX-available `grep` instead of `rg`.

**Tech Stack:** Python `unittest`, nginx config static parsing, Markdown deployment docs, shell snippets using `grep`.

---

## Context

PR #37 merged the repo-side fix for issue #27 in commit `c8cdb2452ee715db7ba7c0c1d63de3813aaeca8d`. A follow-up review found no Critical or Important issues. It found two Minor issues:

- `backend/tests/test_frontend_security_headers.py` verifies child-location CSP and `Cache-Control`, but does not assert that `/assets/` and `/` repeat the non-CSP security headers required because nginx child `add_header` directives stop inheriting parent `add_header` directives.
- `docs/deploy-ubuntu-cloudflare.md` uses `rg` in a production verification snippet, but the host preparation package list does not install ripgrep. The snippet should use `grep -Ei` and `grep -Eq` instead.

Do not change `frontend/nginx.conf` unless the strengthened test reveals a real mismatch. The current merged config already repeats the headers in both static child locations.

Do not close issue #27. Production deploy and Cloudflare dashboard verification remain separate production-state work.

## File Structure

- Modify: `backend/tests/test_frontend_security_headers.py`
  - Adds explicit assertions for `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy` in `/assets/` and `/`.
- Modify: `docs/deploy-ubuntu-cloudflare.md`
  - Replaces `rg` in the Cloudflare Web Analytics verification snippet with `grep`.

---

### Task 1: Strengthen Static Frontend Security Header Tests

**Files:**
- Modify: `backend/tests/test_frontend_security_headers.py`
- Verify: `frontend/nginx.conf`

- [ ] **Step 1: Replace the test file with stricter assertions**

Replace the full contents of `backend/tests/test_frontend_security_headers.py` with:

```python
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
NGINX_CONF = ROOT / "frontend" / "nginx.conf"

EXPECTED_FRONTEND_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


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


def _server_block_before_locations(config: str) -> str:
    match = re.search(r"\n\s*location\s+", config)
    if match is None:
        raise AssertionError("server location blocks not found")
    return config[: match.start()]


def _csp_directives(csp: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for directive in csp.split(";"):
        parts = directive.strip().split()
        if parts:
            directives[parts[0]] = parts[1:]
    return directives


def _assert_strict_csp(test_case: unittest.TestCase, csp: str) -> None:
    directives = _csp_directives(csp)
    test_case.assertEqual(["'self'"], directives["script-src"])
    test_case.assertNotIn("script-src-elem", directives)
    test_case.assertEqual(["'none'"], directives["frame-ancestors"])
    test_case.assertNotIn("static.cloudflareinsights.com", csp)
    test_case.assertNotIn("cloudflareinsights.com", csp)


def _assert_security_headers_repeated(
    test_case: unittest.TestCase, config: str, location: str
) -> None:
    block = _location_block(config, location)
    for header_name, expected_value in EXPECTED_FRONTEND_SECURITY_HEADERS.items():
        test_case.assertEqual(
            [expected_value],
            _add_header_values(block, header_name),
            f"{location} {header_name}",
        )


class FrontendSecurityHeaderTests(unittest.TestCase):
    def test_all_frontend_csp_headers_keep_scripts_self_only(self) -> None:
        config = _read_nginx_conf()
        server_headers = _add_header_values(
            _server_block_before_locations(config), "Content-Security-Policy"
        )
        self.assertEqual(1, len(server_headers), "server")
        _assert_strict_csp(self, server_headers[0])

        headers = _add_header_values(config, "Content-Security-Policy")
        self.assertGreaterEqual(len(headers), 1)
        for csp in headers:
            _assert_strict_csp(self, csp)

    def test_static_frontend_locations_repeat_security_headers(self) -> None:
        config = _read_nginx_conf()

        for location in ("/assets/", "/"):
            _assert_security_headers_repeated(self, config, location)

    def test_static_frontend_responses_prevent_edge_script_injection(self) -> None:
        config = _read_nginx_conf()

        for location in ("/assets/", "/"):
            block = _location_block(config, location)
            csp_headers = _add_header_values(block, "Content-Security-Policy")
            self.assertEqual(1, len(csp_headers), location)
            _assert_strict_csp(self, csp_headers[0])

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

- [ ] **Step 2: Run the targeted test and verify it passes on current main**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_frontend_security_headers -v
```

Expected result:

```text
Ran 4 tests

OK
```

- [ ] **Step 3: Mutation-check the new assertion**

Temporarily remove this line from only the `location /assets/` block in `frontend/nginx.conf`:

```nginx
    add_header X-Frame-Options "DENY" always;
```

Do not remove the server-level line or the `location /` line.

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_frontend_security_headers.FrontendSecurityHeaderTests.test_static_frontend_locations_repeat_security_headers -v
```

Expected result: the test fails with an assertion mentioning `/assets/ X-Frame-Options`.

- [ ] **Step 4: Restore the mutation**

Re-add the removed line inside the `location /assets/` block, immediately after:

```nginx
    add_header X-Content-Type-Options "nosniff" always;
```

The restored block should include:

```nginx
  location /assets/ {
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;
    add_header Cache-Control "public, max-age=31536000, immutable, no-transform" always;
    try_files $uri =404;
  }
```

- [ ] **Step 5: Re-run the targeted test after restoring nginx**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_frontend_security_headers -v
```

Expected result:

```text
Ran 4 tests

OK
```

- [ ] **Step 6: Commit the test hardening**

Run:

```bash
git add backend/tests/test_frontend_security_headers.py frontend/nginx.conf
git diff --cached --stat
git commit -m "test: harden frontend security header coverage"
```

Expected staged stat: `backend/tests/test_frontend_security_headers.py` changed. `frontend/nginx.conf` should not show a diff after the mutation is restored. If `frontend/nginx.conf` appears in the staged stat, inspect it and restore the accidental mutation before committing.

---

### Task 2: Make Cloudflare Verification Snippet Portable

**Files:**
- Modify: `docs/deploy-ubuntu-cloudflare.md`

- [ ] **Step 1: Replace `rg` with `grep` in the Beacon verification snippet**

In `docs/deploy-ubuntu-cloudflare.md`, find this snippet:

```bash
curl -sD /tmp/bitcoin-risk-root.headers -o /tmp/bitcoin-risk-root.html https://risk.example.com/
rg -i "^content-security-policy:|^cache-control:" /tmp/bitcoin-risk-root.headers
if rg -q "static\\.cloudflareinsights\\.com|beacon\\.min\\.js" /tmp/bitcoin-risk-root.html; then
  echo "unexpected Cloudflare Web Analytics beacon"
  exit 1
fi
```

Replace it with:

```bash
curl -sD /tmp/bitcoin-risk-root.headers -o /tmp/bitcoin-risk-root.html https://risk.example.com/
grep -Ei "^(content-security-policy|cache-control):" /tmp/bitcoin-risk-root.headers
if grep -Eq "static\\.cloudflareinsights\\.com|beacon\\.min\\.js" /tmp/bitcoin-risk-root.html; then
  echo "unexpected Cloudflare Web Analytics beacon"
  exit 1
fi
```

- [ ] **Step 2: Verify no `rg` remains in the changed Cloudflare Beacon section**

Run:

```bash
grep -n "static\\\\.cloudflareinsights\\\\.com\\|beacon\\\\.min\\\\.js\\|grep -E\\|rg " docs/deploy-ubuntu-cloudflare.md
```

Expected result: the Beacon verification section uses `grep -Ei` for headers and `grep -Eq` for the Beacon check. It should not show `rg -i` or `rg -q` in that section.

- [ ] **Step 3: Review the documentation diff**

Run:

```bash
git diff -- docs/deploy-ubuntu-cloudflare.md
```

Expected result: only the Beacon verification snippet changes from `rg` commands to `grep` commands.

- [ ] **Step 4: Commit the documentation portability fix**

Run:

```bash
git add docs/deploy-ubuntu-cloudflare.md
git commit -m "docs: use grep in Cloudflare verification snippet"
```

---

### Task 3: Final Verification

**Files:**
- Verify: `backend/tests/test_frontend_security_headers.py`
- Verify: `docs/deploy-ubuntu-cloudflare.md`
- Verify: `frontend/nginx.conf`

- [ ] **Step 1: Run the targeted Python test**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_frontend_security_headers -v
```

Expected result:

```text
Ran 4 tests

OK
```

- [ ] **Step 2: Run whitespace validation**

Run:

```bash
git diff --check HEAD~2..HEAD
```

Expected result: no output and exit code `0`.

- [ ] **Step 3: Confirm the final diff scope**

Run:

```bash
git diff --stat HEAD~2..HEAD
```

Expected result: only these files changed:

```text
backend/tests/test_frontend_security_headers.py
docs/deploy-ubuntu-cloudflare.md
```

- [ ] **Step 4: Confirm worktree cleanliness**

Run:

```bash
git status --short
```

Expected result: no output.

---

## Self-Review Checklist

- The plan fixes only the two Minor review findings.
- No production behavior changes are requested.
- `frontend/nginx.conf` remains unchanged after the mutation check.
- Issue #27 remains open for production deployment and Cloudflare dashboard verification.
- The documentation snippet uses commands available after the existing Ubuntu host-prep package install.
