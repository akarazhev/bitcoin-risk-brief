from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "launch_snapshot_packet.py"
spec = importlib.util.spec_from_file_location("launch_snapshot_packet", SCRIPT_PATH)
launch_snapshot_packet = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(launch_snapshot_packet)


class LaunchSnapshotPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.packet_path = self.root / "launch-snapshot-packet.json"
        for filename in (
            "readiness.json",
            "risk-latest.json",
            "public-endpoint-probe.txt",
            "import-provenance.json",
            "backup-freshness.txt",
            "browser-accessibility-metadata.txt",
        ):
            (self.root / filename).write_text("sanitized evidence summary\n", encoding="utf-8")

    def _run_helper(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = launch_snapshot_packet.main([*args])
        return status, stdout.getvalue(), stderr.getvalue()

    def _create_minimal_packet(self, *extra_args: str) -> tuple[int, str, str]:
        return self._run_helper(
            "create",
            "--output",
            str(self.packet_path),
            "--packet-created-at-utc",
            "2026-07-11T12:00:00Z",
            "--production-commit",
            "f8134c74b859663a6ada4b43768bea2c220da3ce",
            "--base-url",
            "https://bitcoinriskbrief.minihub.app",
            "--readiness-evidence",
            str(self.root / "readiness.json"),
            "--readiness-status",
            "present",
            "--readiness-latest-date",
            "2026-07-09",
            "--readiness-data-fresh",
            "true",
            "--latest-risk-evidence",
            str(self.root / "risk-latest.json"),
            "--latest-risk-status",
            "present",
            "--latest-risk-timestamp",
            "2026-07-09T00:00:00Z",
            "--latest-risk-state",
            "low",
            "--public-endpoint-monitor-probe-evidence",
            str(self.root / "public-endpoint-probe.txt"),
            "--public-endpoint-monitor-probe-status",
            "present",
            "--public-endpoint-monitor-probe-summary",
            "health readiness latest-risk assertions passed in local sanitized evidence",
            "--waitlist-smoke-status",
            "present",
            "--waitlist-smoke-summary",
            "HTTP 201 no-store aggregate-only storage verification",
            "--import-provenance-packet",
            str(self.root / "import-provenance.json"),
            "--import-provenance-status",
            "present",
            "--backup-freshness-evidence",
            str(self.root / "backup-freshness.txt"),
            "--backup-freshness-status",
            "present",
            "--accessibility-status",
            "present",
            "--browser-status",
            "present",
            "--metadata-status",
            "present",
            *extra_args,
        )

    def _operator_decision_args(self) -> list[str]:
        decisions = (
            "waitlist_owner",
            "waitlist_review_cadence",
            "waitlist_retention",
            "deletion_unsubscribe_path",
            "support_contact_identity",
            "credential_account_ownership",
            "data_source_terms_review",
        )
        args: list[str] = []
        for decision in decisions:
            args.extend(["--operator-decision", f"{decision}=present"])
        return args

    def test_valid_minimal_pre_traffic_packet_creates_and_validates_not_run(self) -> None:
        status, stdout, stderr = self._create_minimal_packet()

        self.assertEqual(0, status, stderr)
        self.assertIn("PENDING", stdout)
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        self.assertEqual("not_run", packet["first_traffic_status"])
        self.assertEqual("pending", packet["launch_readiness_status"])
        self.assertIn("operator_decisions", packet["blocked_or_pending_gates"][0])

        status, stdout, stderr = self._run_helper("validate", "--packet", str(self.packet_path))

        self.assertEqual(0, status, stderr)
        self.assertIn("PENDING", stdout)
        self.assertIn("first_traffic_status=not_run", stdout)

    def test_packet_with_absolute_or_private_path_is_rejected(self) -> None:
        status, _stdout, stderr = self._create_minimal_packet()
        self.assertEqual(0, status, stderr)
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        packet["evidence"]["readiness"]["private_path"] = "/" + "Users" + "/" + "operator" + "/" + "readiness.json"
        self.packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

        status, stdout, stderr = self._run_helper("validate", "--packet", str(self.packet_path))

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("unsafe", stderr)

    def test_sensitive_values_are_rejected(self) -> None:
        unsafe_values = (
            ("--accepted-limitation", "operator" + "@" + "example.invalid"),
            ("--accepted-limitation", "call " + "+1 " + "555 " + "123 " + "4567"),
            ("--accepted-limitation", "API_" + "TO" + "KEN" + "=" + "redacted"),
            (
                "--public-endpoint-monitor-probe-summary",
                "dashboard " + "URL " + "https" + "://" + "dash" + "." + "internal.example/checks/1",
            ),
            ("--waitlist-smoke-summary", "raw " + "log dump line included"),
            ("--waitlist-smoke-summary", "raw contacts copied into summary"),
        )

        for option, value in unsafe_values:
            with self.subTest(option=option):
                status, stdout, stderr = self._create_minimal_packet(option, value)

                self.assertNotEqual(0, status)
                self.assertEqual("", stdout)
                self.assertIn("unsafe", stderr)

    def test_embedded_dashboard_url_is_rejected(self) -> None:
        status, stdout, stderr = self._create_minimal_packet(
            "--accepted-limitation",
            "dashboard at " + "https" + "://" + "dash" + "." + "cloudflare.com/checks/1",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("unsafe", stderr)

    def test_private_ipv6_base_url_is_rejected(self) -> None:
        status, stdout, stderr = self._run_helper(
            "create",
            "--packet-created-at-utc",
            "2026-07-11T12:00:00Z",
            "--base-url",
            "https://[::1]",
        )

        self.assertEqual(2, status)
        self.assertEqual("", stdout)
        self.assertIn("private", stderr)

    def test_first_traffic_passed_claim_requires_explicit_evidence(self) -> None:
        status, stdout, stderr = self._create_minimal_packet(
            "--accepted-limitation",
            "first traffic passed in notes",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("first traffic", stderr)

    def test_first_traffic_status_passed_requires_explicit_evidence_file(self) -> None:
        status, stdout, stderr = self._create_minimal_packet(
            "--first-traffic-status",
            "passed",
        )

        self.assertEqual(2, status)
        self.assertEqual("", stdout)
        self.assertIn("first_traffic_status=passed requires --first-traffic-evidence", stderr)

    def test_hyphenated_first_traffic_passed_claim_is_rejected(self) -> None:
        status, stdout, stderr = self._create_minimal_packet(
            "--accepted-limitation",
            "first-traffic completed in notes",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("first", stderr)

    def test_missing_required_evidence_category_is_reported_as_pending(self) -> None:
        status, _stdout, stderr = self._create_minimal_packet()
        self.assertEqual(0, status, stderr)
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        packet["evidence"].pop("backup_freshness")
        self.packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

        status, stdout, stderr = self._run_helper("validate", "--packet", str(self.packet_path))

        self.assertEqual(0, status, stderr)
        self.assertIn("PENDING", stdout)
        self.assertIn("backup_freshness", stdout)

    def test_present_evidence_without_required_details_keeps_packet_pending(self) -> None:
        status, stdout, stderr = self._run_helper(
            "create",
            "--output",
            str(self.packet_path),
            "--packet-created-at-utc",
            "2026-07-11T12:00:00Z",
            "--production-commit",
            "f8134c74b859663a6ada4b43768bea2c220da3ce",
            "--base-url",
            "https://bitcoinriskbrief.minihub.app",
            "--readiness-status",
            "present",
            "--latest-risk-status",
            "present",
            "--public-endpoint-monitor-probe-status",
            "present",
            "--waitlist-smoke-status",
            "present",
            "--import-provenance-status",
            "present",
            "--backup-freshness-status",
            "present",
            "--accessibility-status",
            "present",
            "--browser-status",
            "present",
            "--metadata-status",
            "present",
            *self._operator_decision_args(),
        )

        self.assertEqual(0, status, stderr)
        self.assertIn("PENDING", stdout)
        self.assertIn("readiness missing", stdout)
        self.assertIn("latest_risk missing", stdout)
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        self.assertEqual("pending", packet["launch_readiness_status"])

    def test_basenames_are_emitted_for_evidence_files(self) -> None:
        status, _stdout, stderr = self._create_minimal_packet()
        self.assertEqual(0, status, stderr)

        packet_text = self.packet_path.read_text(encoding="utf-8")
        packet = json.loads(packet_text)

        self.assertEqual("readiness.json", packet["evidence"]["readiness"]["basename"])
        self.assertEqual("risk-latest.json", packet["evidence"]["latest_risk"]["basename"])
        self.assertEqual(
            "public-endpoint-probe.txt",
            packet["evidence"]["public_endpoint_monitor_probe"]["basename"],
        )
        self.assertNotIn(str(self.root), packet_text)

    def test_accepted_limitations_are_preserved_without_launch_passed_status(self) -> None:
        status, _stdout, stderr = self._create_minimal_packet(
            "--accepted-limitation",
            "restore drill deferred until a separate restore target exists",
        )

        self.assertEqual(0, status, stderr)
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        self.assertEqual(
            ["restore drill deferred until a separate restore target exists"],
            packet["accepted_limitations"],
        )
        self.assertEqual("pending", packet["launch_readiness_status"])
        self.assertNotEqual("passed", packet["launch_readiness_status"])


if __name__ == "__main__":
    unittest.main()
