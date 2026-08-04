from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
NGINX_CONF = ROOT / "frontend" / "nginx.conf"
COMPOSE_FILE = ROOT / "podman-compose.yml"

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
    test_case.assertEqual(
        ["'self'", "https://challenges.cloudflare.com"], directives["script-src"]
    )
    test_case.assertNotIn("script-src-elem", directives)
    test_case.assertEqual(
        ["https://challenges.cloudflare.com"], directives["frame-src"]
    )
    test_case.assertEqual(
        ["'self'", "https://challenges.cloudflare.com"], directives["connect-src"]
    )
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
    def test_all_frontend_csp_headers_allow_only_required_turnstile_origin(self) -> None:
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

    def test_compose_wires_turnstile_without_exposing_secret_to_frontend_build(
        self,
    ) -> None:
        compose = _read_compose_file()
        backend_block = compose.split("\n  backend:\n", 1)[1].split(
            "\n  frontend:\n", 1
        )[0]
        frontend_block = compose.split("\n  frontend:\n", 1)[1].split(
            "\n  data-collector:\n", 1
        )[0]
        frontend_build = frontend_block.split("\n    restart:", 1)[0]

        self.assertIn(
            "TURNSTILE_SECRET: ${TURNSTILE_SECRET:-}", backend_block
        )
        self.assertIn(
            "TURNSTILE_HOSTNAMES: ${TURNSTILE_HOSTNAMES:-}", backend_block
        )
        self.assertIn(
            "VITE_TURNSTILE_SITE_KEY: "
            "${VITE_TURNSTILE_SITE_KEY:?VITE_TURNSTILE_SITE_KEY is required}",
            frontend_build,
        )
        self.assertNotIn("TURNSTILE_SECRET", frontend_build)


if __name__ == "__main__":
    unittest.main()
