from __future__ import annotations

import unittest

from app.main import app

PUBLIC_PATHS = {
    "/api/health",
    "/api/readiness",
    "/api/risk/latest",
    "/api/risk/history",
    "/api/risk/levels",
    "/api/brief/latest",
    "/api/waitlist",
}


class OpenApiContractTests(unittest.TestCase):
    def test_schema_is_served_under_the_api_prefix(self) -> None:
        self.assertEqual(app.openapi_url, "/api/openapi.json")

    def test_interactive_docs_are_disabled(self) -> None:
        self.assertIsNone(app.docs_url, "Swagger UI loads CDN scripts the CSP blocks")
        self.assertIsNone(app.redoc_url)

    def test_every_public_route_is_in_the_schema(self) -> None:
        paths = set(app.openapi()["paths"].keys())
        self.assertEqual(PUBLIC_PATHS, paths & PUBLIC_PATHS)

    def test_schema_declares_the_public_server(self) -> None:
        servers = app.openapi().get("servers", [])
        self.assertIn(
            "https://bitcoinriskbrief.minihub.app",
            {entry.get("url") for entry in servers},
        )

    def test_every_public_route_has_a_summary_and_description(self) -> None:
        paths = app.openapi()["paths"]
        for path in sorted(PUBLIC_PATHS):
            for method, operation in paths[path].items():
                with self.subTest(path=path, method=method):
                    self.assertTrue(operation.get("summary"), f"{method} {path} needs a summary")
                    self.assertTrue(operation.get("description"), f"{method} {path} needs a description")

    def test_description_states_the_advice_boundary(self) -> None:
        self.assertIn("not financial advice", app.openapi()["info"]["description"].lower())
