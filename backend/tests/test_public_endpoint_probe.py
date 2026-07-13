from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
from urllib.error import URLError
from urllib.parse import urlparse
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_public_endpoints.py"
spec = importlib.util.spec_from_file_location("check_public_endpoints", SCRIPT_PATH)
check_public_endpoints = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = check_public_endpoints
spec.loader.exec_module(check_public_endpoints)


class FakeResponse:
    def __init__(
        self,
        status: int,
        body: dict[str, object] | bytes | str,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.headers = headers or {}
        if isinstance(body, bytes):
            self._body = body
        elif isinstance(body, str):
            self._body = body.encode("utf-8")
        else:
            self._body = json.dumps(body).encode("utf-8")

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def close(self) -> None:
        return None


class FakeOpener:
    def __init__(self, responses: dict[str, FakeResponse | BaseException]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, str]] = []

    def __call__(self, request, timeout: float):
        parsed = urlparse(request.full_url)
        self.requests.append((request.get_method(), parsed.path))
        response = self.responses.get(parsed.path)
        if response is None:
            raise AssertionError(f"unexpected request path {parsed.path}")
        if isinstance(response, BaseException):
            raise response
        return response


class PublicEndpointProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)

    def _healthy_responses(self) -> dict[str, FakeResponse]:
        cache_headers = {
            "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
            "ETag": '"abc123"',
            "X-Cache-Version": "validation:2026-07-10",
            "X-Cache": "HIT",
        }
        readiness_headers = {
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        }
        return {
            "/api/health": FakeResponse(200, {"status": "ok"}),
            "/api/readiness": FakeResponse(
                200,
                {
                    "status": "ready",
                    "checks": {
                        "risk_data_available": True,
                        "validation_available": True,
                        "risk_range_ok": True,
                        "validation_has_rows": True,
                        "latest_matches_validation_end": True,
                        "source_is_canonical": True,
                        "data_fresh": True,
                    },
                    "data": {
                        "latest_date": "2026-07-10",
                        "covered_end": "2026-07-10",
                        "data_age_days": 1,
                        "max_age_days": 2,
                        "source": "coinmarketcap_csv",
                        "row_count": 5841,
                        "methodology_version": "crypto-scout-canonical-v1",
                    },
                },
                headers=readiness_headers,
            ),
            "/api/risk/latest": FakeResponse(
                200,
                {
                    "data": {
                        "timestamp": "2026-07-10T00:00:00+00:00",
                        "risk": 0.28,
                        "risk_state": "low",
                    }
                },
                headers=cache_headers,
            ),
        }

    def _run_probe(
        self,
        responses: dict[str, FakeResponse | BaseException],
        *args: str,
    ) -> tuple[int, str, str, FakeOpener]:
        opener = FakeOpener(responses)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = check_public_endpoints.main(
                ["--base-url", "https://monitor-target.test", *args],
                opener=opener,
                now_utc=self.now,
            )
        return status, stdout.getvalue(), stderr.getvalue(), opener

    def test_all_endpoints_healthy_passes(self) -> None:
        status, stdout, stderr, _opener = self._run_probe(
            self._healthy_responses(),
            "--max-data-age-days",
            "2",
        )

        self.assertEqual(0, status, stderr)
        self.assertIn("OK", stdout)
        self.assertIn("latest_date=2026-07-10", stdout)
        self.assertEqual("", stderr)

    def test_health_non_200_fails(self) -> None:
        responses = self._healthy_responses()
        responses["/api/health"] = FakeResponse(503, {"status": "degraded"})

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("GET /api/health returned HTTP 503", stderr)

    def test_readiness_non_ready_fails(self) -> None:
        responses = self._healthy_responses()
        responses["/api/readiness"] = FakeResponse(
            200,
            {
                "status": "degraded",
                "checks": {"data_fresh": True},
                "data": {"latest_date": "2026-07-10", "data_age_days": 1},
            },
        )

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("readiness status is degraded", stderr)

    def test_readiness_data_fresh_false_fails(self) -> None:
        responses = self._healthy_responses()
        responses["/api/readiness"] = FakeResponse(
            200,
            {
                "status": "ready",
                "checks": {
                    "risk_data_available": True,
                    "validation_available": True,
                    "risk_range_ok": True,
                    "validation_has_rows": True,
                    "latest_matches_validation_end": True,
                    "source_is_canonical": True,
                    "data_fresh": False,
                },
                "data": {
                    "latest_date": "2026-07-10",
                    "covered_end": "2026-07-10",
                    "data_age_days": 1,
                    "max_age_days": 2,
                    "source": "coinmarketcap_csv",
                    "row_count": 5841,
                    "methodology_version": "crypto-scout-canonical-v1",
                },
            },
        )

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("checks.data_fresh is not true", stderr)

    def test_readiness_missing_backend_shape_field_fails(self) -> None:
        for field in ("covered_end", "data_age_days", "max_age_days", "source", "row_count", "methodology_version"):
            with self.subTest(field=field):
                responses = self._healthy_responses()
                readiness_body = {
                    "status": "ready",
                    "checks": {
                        "risk_data_available": True,
                        "validation_available": True,
                        "risk_range_ok": True,
                        "validation_has_rows": True,
                        "latest_matches_validation_end": True,
                        "source_is_canonical": True,
                        "data_fresh": True,
                    },
                    "data": {
                        "latest_date": "2026-07-10",
                        "covered_end": "2026-07-10",
                        "data_age_days": 1,
                        "max_age_days": 2,
                        "source": "coinmarketcap_csv",
                        "row_count": 5841,
                        "methodology_version": "crypto-scout-canonical-v1",
                    },
                }
                readiness_body["data"].pop(field)
                responses["/api/readiness"] = FakeResponse(200, readiness_body)

                status, stdout, stderr, _opener = self._run_probe(
                    responses,
                    "--expected-latest-date",
                    "2026-07-10",
                )

                self.assertNotEqual(0, status)
                self.assertEqual("", stdout)
                self.assertIn(field, stderr)

    def test_readiness_missing_backend_check_field_fails(self) -> None:
        responses = self._healthy_responses()
        readiness_body = {
            "status": "ready",
            "checks": {
                "validation_available": True,
                "risk_range_ok": True,
                "validation_has_rows": True,
                "latest_matches_validation_end": True,
                "source_is_canonical": True,
                "data_fresh": True,
            },
            "data": {
                "latest_date": "2026-07-10",
                "covered_end": "2026-07-10",
                "data_age_days": 1,
                "max_age_days": 2,
                "source": "coinmarketcap_csv",
                "row_count": 5841,
                "methodology_version": "crypto-scout-canonical-v1",
            },
        }
        responses["/api/readiness"] = FakeResponse(200, readiness_body)

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("checks.risk_data_available", stderr)

    def test_latest_risk_malformed_timestamp_or_missing_risk_fails(self) -> None:
        for latest_payload, expected_error in (
            ({"data": {"timestamp": "not-a-date", "risk": 0.28}}, "timestamp"),
            ({"data": {"timestamp": "2026-07-10T00:00:00+00:00"}}, "risk"),
        ):
            with self.subTest(expected_error=expected_error):
                responses = self._healthy_responses()
                responses["/api/risk/latest"] = FakeResponse(200, latest_payload)

                status, stdout, stderr, _opener = self._run_probe(
                    responses,
                    "--expected-latest-date",
                    "2026-07-10",
                )

                self.assertNotEqual(0, status)
                self.assertEqual("", stdout)
                self.assertIn(expected_error, stderr)

    def test_expected_latest_date_mismatch_fails(self) -> None:
        status, stdout, stderr, _opener = self._run_probe(
            self._healthy_responses(),
            "--expected-latest-date",
            "2026-07-11",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("expected latest date 2026-07-11 but saw 2026-07-10", stderr)

    def test_max_data_age_stale_latest_date_fails(self) -> None:
        status, stdout, stderr, _opener = self._run_probe(
            self._healthy_responses(),
            "--max-data-age-days",
            "0",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("is stale", stderr)

    def test_cache_header_requirement_passes_and_fails_as_expected(self) -> None:
        status, stdout, stderr, _opener = self._run_probe(
            self._healthy_responses(),
            "--expected-latest-date",
            "2026-07-10",
            "--require-cache-header",
            "ETag",
            "--require-cache-header",
            "X-Cache",
        )
        self.assertEqual(0, status, stderr)
        self.assertIn("cache_headers=ETag,X-Cache", stdout)

        responses = self._healthy_responses()
        responses["/api/risk/latest"] = FakeResponse(
            200,
            responses["/api/risk/latest"]._body,
            headers={"ETag": '"abc123"'},
        )
        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
            "--require-cache-header",
            "X-Cache",
        )
        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("GET /api/risk/latest missing X-Cache", stderr)

        responses = self._healthy_responses()
        responses["/api/readiness"] = FakeResponse(
            200,
            responses["/api/readiness"]._body,
            headers={"Cache-Control": "no-store"},
        )
        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
            "--require-cache-header",
            "X-Cache",
        )
        self.assertEqual(0, status, stderr)
        self.assertIn("cache_headers=X-Cache", stdout)

    def test_readiness_must_be_no_store(self) -> None:
        responses = self._healthy_responses()
        responses["/api/readiness"] = FakeResponse(
            200,
            responses["/api/readiness"]._body,
            headers={"Cache-Control": "public, max-age=60"},
        )

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("GET /api/readiness Cache-Control must include no-store", stderr)

    def test_timeout_failure_returns_nonzero_without_traceback(self) -> None:
        responses: dict[str, FakeResponse | BaseException] = self._healthy_responses()
        responses["/api/readiness"] = URLError("timed out")

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("GET /api/readiness request failed", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_malformed_json_returns_nonzero_without_raw_dump(self) -> None:
        responses = self._healthy_responses()
        responses["/api/risk/latest"] = FakeResponse(200, b'{"data": ')

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("malformed JSON", stderr)
        self.assertNotIn('{"data":', stderr)
        self.assertNotIn("Traceback", stderr)

    def test_no_mutating_endpoints_are_requested(self) -> None:
        status, _stdout, stderr, opener = self._run_probe(
            self._healthy_responses(),
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertEqual(0, status, stderr)
        self.assertEqual(
            [
                ("GET", "/api/health"),
                ("GET", "/api/readiness"),
                ("GET", "/api/risk/latest"),
            ],
            opener.requests,
        )

    def test_missing_explicit_freshness_policy_fails(self) -> None:
        status, stdout, stderr, _opener = self._run_probe(self._healthy_responses())

        self.assertEqual(2, status)
        self.assertEqual("", stdout)
        self.assertIn("provide --max-data-age-days or --expected-latest-date", stderr)


if __name__ == "__main__":
    unittest.main()
