from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "import_provenance_packet.py"
spec = importlib.util.spec_from_file_location("import_provenance_packet", SCRIPT_PATH)
import_provenance_packet = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(import_provenance_packet)


class ImportProvenancePacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.source_csv = self.root / "bitcoin-historical-data.csv"
        self.canonical_csv = self.root / "btc_usd_daily.csv"
        self.manifest_path = self.root / "manifest.json"
        self.source_csv.write_text(
            "\n".join(
                [
                    "Date,Open,High,Low,Close,Volume,Market Cap",
                    "Jul 09, 2026,100.11,105.22,99.33,104.44,\"2,000,000\",\"1,976,000,000\"",
                    "Jul 10, 2026,104.44,106.55,103.66,105.77,\"2,500,000\",\"2,010,000,000\"",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.canonical_csv.write_text(
            "\n".join(
                [
                    "timeOpen;timeClose;timeHigh;timeLow;open;high;low;close;volume;marketCap;circulatingSupply;timestamp",
                    "2026-07-09T00:00:00.000Z;2026-07-09T23:59:59.999Z;2026-07-09T00:00:00.000Z;2026-07-09T00:00:00.000Z;100;105;99;104;2000000;1976000000;19000000;2026-07-09T23:59:59.999Z",
                    "2026-07-10T00:00:00.000Z;2026-07-10T23:59:59.999Z;2026-07-10T00:00:00.000Z;2026-07-10T00:00:00.000Z;104;106;103;105;2500000;2010000000;19000000;2026-07-10T23:59:59.999Z",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (self.root / "readiness-origin.json").write_text('{"status":"ready"}\n', encoding="utf-8")
        (self.root / "validation-summary.json").write_text('{"risk_range_ok":true}\n', encoding="utf-8")
        (self.root / "risk-latest-public.headers").write_text("HTTP/2 200\n", encoding="utf-8")

    def _run_helper(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = import_provenance_packet.main([*args])
        return status, stdout.getvalue(), stderr.getvalue()

    def _create_manifest(self, *extra_args: str) -> tuple[int, str, str]:
        return self._run_helper(
            "create",
            "--source-type",
            "manual_cmc_csv",
            "--source-csv",
            str(self.source_csv),
            "--canonical-csv",
            str(self.canonical_csv),
            "--output",
            str(self.manifest_path),
            "--evidence-created-at-utc",
            "2026-07-11T12:00:00Z",
            "--retrieval-started-at-utc",
            "2026-07-11T11:58:00Z",
            "--retrieval-completed-at-utc",
            "2026-07-11T11:59:00Z",
            "--expected-start-date",
            "2026-07-09",
            "--expected-end-date",
            "2026-07-10",
            "--readiness-evidence",
            str(self.root / "readiness-origin.json"),
            "--validation-evidence",
            str(self.root / "validation-summary.json"),
            "--cache-evidence",
            str(self.root / "risk-latest-public.headers"),
            "--production-commit",
            "7aa5e4aabffd6da181a2f124f9ee5e2860f6f179",
            "--note",
            "local helper test packet only",
            *extra_args,
        )

    def test_valid_coinmarketcap_source_csv_creates_sanitized_manifest(self) -> None:
        status, stdout, stderr = self._create_manifest()

        self.assertEqual(0, status, stderr)
        self.assertIn("OK", stdout)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("manual_cmc_csv", manifest["source_type"])
        self.assertEqual(self.source_csv.name, manifest["source_basename"])
        self.assertEqual(hashlib.sha256(self.source_csv.read_bytes()).hexdigest(), manifest["source_sha256"])
        self.assertEqual(2, manifest["observed_row_count"])
        self.assertEqual("2026-07-09", manifest["observed_start_date"])
        self.assertEqual("2026-07-10", manifest["observed_end_date"])
        self.assertEqual("2026-07-10", manifest["canonical_csv_tail_date"])
        self.assertEqual(
            {
                "readiness": "readiness-origin.json",
                "validation": "validation-summary.json",
                "cache": "risk-latest-public.headers",
            },
            manifest["evidence_file_basenames"],
        )
        manifest_text = json.dumps(manifest, sort_keys=True)
        self.assertNotIn(str(self.source_csv), manifest_text)
        self.assertNotIn(str(self.canonical_csv), manifest_text)
        self.assertNotIn(str(self.root), manifest_text)

    def test_validation_accepts_well_formed_manifest(self) -> None:
        status, _stdout, stderr = self._create_manifest()
        self.assertEqual(0, status, stderr)

        status, stdout, stderr = self._run_helper("validate", "--manifest", str(self.manifest_path))

        self.assertEqual(0, status, stderr)
        self.assertIn("OK", stdout)

    def test_unsupported_source_type_fails(self) -> None:
        status, stdout, stderr = self._run_helper(
            "create",
            "--source-type",
            "spreadsheet_export",
            "--source-csv",
            str(self.source_csv),
            "--output",
            str(self.manifest_path),
            "--evidence-created-at-utc",
            "2026-07-11T12:00:00Z",
        )

        self.assertEqual(2, status)
        self.assertEqual("", stdout)
        self.assertIn("unsupported source_type", stderr)

    def test_malformed_csv_fails(self) -> None:
        self.source_csv.write_text("Date,Open,High\nnot-a-date,1,2\n", encoding="utf-8")

        status, stdout, stderr = self._create_manifest()

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("malformed CSV", stderr)

    def test_expected_checksum_mismatch_fails(self) -> None:
        status, stdout, stderr = self._create_manifest("--expected-source-sha256", "0" * 64)

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("checksum mismatch", stderr)

    def test_expected_date_range_mismatch_fails(self) -> None:
        status, stdout, stderr = self._create_manifest("--expected-end-date", "2026-07-11")

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("expected_end_date", stderr)

    def test_private_paths_are_not_emitted_and_unsafe_manifest_paths_fail_validation(self) -> None:
        status, _stdout, stderr = self._create_manifest()
        self.assertEqual(0, status, stderr)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(self.source_csv.name, manifest["source_basename"])
        manifest["staged_source_path"] = "/tmp/operator/source.csv"
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        status, stdout, stderr = self._run_helper("validate", "--manifest", str(self.manifest_path))

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("unsafe", stderr)

    def test_raw_source_rows_are_not_copied_to_manifest(self) -> None:
        status, _stdout, stderr = self._create_manifest()
        self.assertEqual(0, status, stderr)

        manifest_text = self.manifest_path.read_text(encoding="utf-8")

        self.assertNotIn("Jul 09, 2026,100.11,105.22,99.33,104.44", manifest_text)
        self.assertNotIn("105.77", manifest_text)
        self.assertNotIn("2,010,000,000", manifest_text)

    def test_unsafe_operator_supplied_notes_and_limitations_fail(self) -> None:
        unsafe_cases = (
            ("--note", "Jul 09, 2026,100.11,105.22,99.33,104.44"),
            ("--note", "2026-07-09,100.11,105.22,99.33,104.44,2000000,1976000000"),
            (
                "--limitation",
                "2026-07-09T00:00:00.000Z;2026-07-09T23:59:59.999Z;100;105;99;104;2000000",
            ),
            ("--limitation", "collector log dump marker"),
            ("--note", "operator token placeholder"),
            ("--note", "source:/Users/operator/source.csv"),
            ("--note", "Call +1 555 123 4567"),
        )

        for option, value in unsafe_cases:
            with self.subTest(option=option, value=value):
                status, stdout, stderr = self._create_manifest(option, value)

                self.assertNotEqual(0, status)
                self.assertEqual("", stdout)
                self.assertIn("unsafe", stderr)

    def test_validation_rejects_source_basename_mismatch_when_source_file_is_supplied(self) -> None:
        status, _stdout, stderr = self._create_manifest()
        self.assertEqual(0, status, stderr)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest["source_basename"] = "claimed-source.csv"
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        status, stdout, stderr = self._run_helper(
            "validate",
            "--manifest",
            str(self.manifest_path),
            "--source-csv",
            str(self.source_csv),
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("source_basename", stderr)

    def test_validation_rejects_malformed_canonical_tail_without_expected_end_date(self) -> None:
        status, _stdout, stderr = self._create_manifest()
        self.assertEqual(0, status, stderr)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest.pop("expected_end_date")
        manifest["canonical_csv_tail_date"] = "not-a-date"
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        status, stdout, stderr = self._run_helper("validate", "--manifest", str(self.manifest_path))

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("canonical_csv_tail_date", stderr)


if __name__ == "__main__":
    unittest.main()
