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

RESPONSE_METADATA_REQUIREMENTS = {
    ("/api/health", "get"): {
        "statuses": {"200"},
        "example_status": "200",
    },
    ("/api/readiness", "get"): {
        "statuses": {"200", "503"},
        "example_status": "200",
        "headers": {"Cache-Control", "Pragma"},
        "header_statuses": {"200", "503"},
    },
    ("/api/risk/latest", "get"): {
        "statuses": {"200", "304", "404"},
        "example_status": "200",
        "headers": {"Cache-Control", "ETag", "X-Cache", "X-Cache-Version"},
        "header_statuses": {"200", "304"},
    },
    ("/api/risk/history", "get"): {
        "statuses": {"200", "304", "400"},
        "example_status": "200",
        "headers": {"Cache-Control", "ETag", "X-Cache", "X-Cache-Version"},
        "header_statuses": {"200", "304"},
    },
    ("/api/risk/levels", "get"): {
        "statuses": {"200", "304", "404"},
        "example_status": "200",
        "headers": {"Cache-Control", "ETag", "X-Cache", "X-Cache-Version"},
        "header_statuses": {"200", "304"},
    },
    ("/api/brief/latest", "get"): {
        "statuses": {"200", "304", "404"},
        "example_status": "200",
        "headers": {"Cache-Control", "ETag", "X-Cache", "X-Cache-Version"},
        "header_statuses": {"200", "304"},
    },
    ("/api/waitlist", "post"): {
        "statuses": {"201", "403", "422", "429", "503"},
        "example_status": "201",
        "headers": {"Cache-Control", "Pragma"},
        "header_statuses": {"201", "403", "422", "429", "503"},
    },
}


def _json_response_has_example(response: dict) -> bool:
    json_content = response.get("content", {}).get("application/json", {})
    return bool(json_content.get("example") or json_content.get("examples"))


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

    def test_every_public_route_description_states_the_advice_boundary(self) -> None:
        paths = app.openapi()["paths"]
        for path in sorted(PUBLIC_PATHS):
            for method, operation in paths[path].items():
                with self.subTest(path=path, method=method):
                    self.assertIn("not financial advice", operation["description"].lower())

    def test_description_states_the_advice_boundary(self) -> None:
        self.assertIn("not financial advice", app.openapi()["info"]["description"].lower())

    def test_public_routes_declare_statuses_headers_and_examples(self) -> None:
        paths = app.openapi()["paths"]
        for (path, method), requirements in sorted(RESPONSE_METADATA_REQUIREMENTS.items()):
            operation = paths[path][method]
            responses = operation["responses"]
            with self.subTest(path=path, method=method, check="statuses"):
                self.assertTrue(requirements["statuses"].issubset(responses.keys()))

            for status in requirements["statuses"]:
                with self.subTest(path=path, method=method, status=status, check="description"):
                    response = responses.get(status)
                    self.assertIsNotNone(response)
                    if response is not None:
                        self.assertTrue(response.get("description"))

            example_status = requirements["example_status"]
            with self.subTest(path=path, method=method, status=example_status, check="example"):
                response = responses.get(example_status)
                self.assertIsNotNone(response)
                if response is not None:
                    self.assertTrue(
                        _json_response_has_example(response),
                        f"{method} {path} {example_status} needs a JSON response example",
                    )

            for status in requirements.get("header_statuses", set()):
                with self.subTest(path=path, method=method, status=status, check="headers"):
                    response = responses.get(status)
                    self.assertIsNotNone(response)
                    if response is not None:
                        headers = response.get("headers", {})
                        self.assertTrue(requirements["headers"].issubset(headers.keys()))

    def test_waitlist_created_example_documents_boolean_created_flag(self) -> None:
        waitlist_post = app.openapi()["paths"]["/api/waitlist"]["post"]
        created_example = waitlist_post["responses"]["201"]["content"]["application/json"]["examples"]["shape"][
            "value"
        ]

        self.assertIsInstance(created_example["data"]["created"], bool)
        self.assertTrue(created_example["data"]["created"])
