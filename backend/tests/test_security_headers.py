from __future__ import annotations

import unittest

from app.security import build_security_headers


class SecurityHeadersTest(unittest.TestCase):
    def test_build_security_headers_for_api_responses(self) -> None:
        headers = build_security_headers(app_env="development")

        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("camera=()", headers["Permissions-Policy"])
        self.assertNotIn("Strict-Transport-Security", headers)

    def test_production_security_headers_include_hsts(self) -> None:
        headers = build_security_headers(app_env="production")

        self.assertIn("max-age=", headers["Strict-Transport-Security"])
        self.assertIn("includeSubDomains", headers["Strict-Transport-Security"])


if __name__ == "__main__":
    unittest.main()
