from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
NGINX_CONF = FRONTEND_DIR / "nginx.conf"
COMPOSE_FILE = ROOT / "podman-compose.yml"
FRONTEND_PACKAGE = FRONTEND_DIR / "package.json"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

EXPECTED_CSP = (
    "default-src 'self'; script-src 'self' https://challenges.cloudflare.com; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' "
    "https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)
EXPECTED_CSP_DIRECTIVES = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "https://challenges.cloudflare.com"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:"],
    "connect-src": ["'self'", "https://challenges.cloudflare.com"],
    "frame-src": ["https://challenges.cloudflare.com"],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
}

EXPECTED_FRONTEND_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def _read_nginx_conf() -> str:
    return NGINX_CONF.read_text()


def _read_compose_file() -> str:
    return COMPOSE_FILE.read_text()


def _named_yaml_block(config: str, name: str) -> str:
    pattern = re.compile(
        rf"^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [\w-]+:\n|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(config)
    if match is None:
        raise AssertionError(f"YAML block {name} not found")
    return match.group("body")


def _yaml_block_names(config: str) -> list[str]:
    return re.findall(r"^  ([\w-]+):\n", config, re.MULTILINE)


def _tracked_frontend_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--", "frontend"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / relative_path for relative_path in result.stdout.splitlines()]


def _run_frontend_prebuild(sitekey: str | None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if sitekey is None:
        env.pop("VITE_TURNSTILE_SITE_KEY", None)
    else:
        env["VITE_TURNSTILE_SITE_KEY"] = sitekey
    return subprocess.run(
        ["npm", "run", "prebuild", "--prefix", "frontend"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


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


def _csp_directive_entries(csp: str) -> list[tuple[str, list[str]]]:
    directives: list[tuple[str, list[str]]] = []
    for directive in csp.split(";"):
        parts = directive.strip().split()
        if parts:
            directives.append((parts[0], parts[1:]))
    return directives


def _assert_strict_csp(test_case: unittest.TestCase, csp: str) -> None:
    entries = _csp_directive_entries(csp)
    directive_names = [name for name, _values in entries]
    test_case.assertEqual(len(directive_names), len(set(directive_names)))
    test_case.assertEqual(EXPECTED_CSP_DIRECTIVES, dict(entries))
    test_case.assertNotIn("'unsafe-eval'", csp)
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
    def test_all_frontend_csp_headers_use_four_identical_exact_policies(self) -> None:
        config = _read_nginx_conf()
        self.assertEqual(
            4,
            len(re.findall(r"\badd_header\s+Content-Security-Policy\b", config)),
        )
        headers = _add_header_values(config, "Content-Security-Policy")
        self.assertEqual(
            [EXPECTED_CSP, EXPECTED_CSP, EXPECTED_CSP, EXPECTED_CSP], headers
        )
        for csp in headers:
            _assert_strict_csp(self, csp)

    def test_server_scope_csp_preserves_api_coverage(self) -> None:
        config = _read_nginx_conf()
        server_scope = config.split("location /api/", 1)[0]

        self.assertEqual(
            [EXPECTED_CSP],
            _add_header_values(server_scope, "Content-Security-Policy"),
        )

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

    def test_compose_wires_turnstile_without_exposing_secret_to_frontend_service(
        self,
    ) -> None:
        compose = _read_compose_file()
        backend_block = _named_yaml_block(compose, "backend")
        frontend_block = _named_yaml_block(compose, "frontend")
        frontend_build = frontend_block.split("\n    restart:", 1)[0]

        self.assertIn("TURNSTILE_SECRET: ${TURNSTILE_SECRET:-}", backend_block)
        self.assertIn("TURNSTILE_HOSTNAMES: ${TURNSTILE_HOSTNAMES:-}", backend_block)
        self.assertIn(
            "VITE_TURNSTILE_SITE_KEY: "
            "${VITE_TURNSTILE_SITE_KEY:?VITE_TURNSTILE_SITE_KEY is required}",
            frontend_build,
        )
        self.assertNotIn("TURNSTILE_SECRET", frontend_block)

    def test_frontend_prebuild_hook_invokes_repository_guard(self) -> None:
        package = json.loads(FRONTEND_PACKAGE.read_text())

        self.assertEqual(
            "node scripts/require-turnstile-sitekey.mjs",
            package["scripts"]["prebuild"],
        )

    def test_frontend_build_guard_rejects_unset_and_blank_sitekeys(self) -> None:
        expected_error = "VITE_TURNSTILE_SITE_KEY is required for frontend builds"

        for label, sitekey in (("unset", None), ("empty", ""), ("whitespace", "   ")):
            with self.subTest(sitekey=label):
                result = _run_frontend_prebuild(sitekey)
                output = result.stdout + result.stderr
                self.assertNotEqual(0, result.returncode, output)
                self.assertIn(expected_error, output)

    def test_frontend_source_scripts_and_config_never_reference_backend_secret(
        self,
    ) -> None:
        for path in _tracked_frontend_files():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("TURNSTILE_SECRET", path.read_text(errors="ignore"))

    def test_frontend_ci_jobs_never_receive_or_log_backend_secret(self) -> None:
        workflow = CI_WORKFLOW.read_text()
        workflow_prelude = workflow.split("\njobs:\n", 1)[0]
        frontend_jobs = [
            job for job in _yaml_block_names(workflow) if job.startswith("frontend-")
        ]

        self.assertNotIn("TURNSTILE_SECRET", workflow_prelude)
        self.assertIn("frontend-tests", frontend_jobs)
        for job in (*frontend_jobs, "compose-validation"):
            with self.subTest(job=job):
                self.assertNotIn("TURNSTILE_SECRET", _named_yaml_block(workflow, job))


if __name__ == "__main__":
    unittest.main()
