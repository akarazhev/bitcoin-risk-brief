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
