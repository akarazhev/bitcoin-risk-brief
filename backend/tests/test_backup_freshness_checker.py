from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_backup_freshness.py"
spec = importlib.util.spec_from_file_location("check_backup_freshness", SCRIPT_PATH)
check_backup_freshness = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(check_backup_freshness)


class BackupFreshnessCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.backup_root = self.root / "backups"
        self.off_server_root = self.root / "off-server"
        self.now = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)

    def _timestamp(self, *, hours_ago: int) -> str:
        return (self.now - timedelta(hours=hours_ago)).strftime("%Y%m%dT%H%M%SZ")

    def _write_backup(
        self,
        root: Path,
        timestamp: str,
        *,
        dump_bytes: bytes = b"postgres dump\n",
        csv_bytes: bytes = b"timeOpen;open;high;low;close\n2026-07-10;1;2;1;2\n",
        manifest_text: str = "created_at_utc=20260711T110000Z\n",
    ) -> Path:
        backup_dir = root / timestamp
        backup_dir.mkdir(parents=True)
        files = {
            f"postgres_{timestamp}.dump": dump_bytes,
            f"btc_usd_daily_{timestamp}.csv": csv_bytes,
            "manifest.txt": manifest_text.encode(),
        }
        checksum_lines = []
        for filename, contents in files.items():
            (backup_dir / filename).write_bytes(contents)
            checksum_lines.append(f"{hashlib.sha256(contents).hexdigest()}  {filename}\n")
        (backup_dir / "SHA256SUMS").write_text("".join(checksum_lines))
        return backup_dir

    def _run_checker(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = check_backup_freshness.main([*args], now_utc=self.now)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_fresh_valid_local_backup_passes(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        self._write_backup(self.backup_root, timestamp)

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--max-age-hours",
            "24",
        )

        self.assertEqual(0, status, stderr)
        self.assertIn(timestamp, stdout)
        self.assertIn("OK", stdout)
        self.assertEqual("", stderr)

    def test_stale_backup_fails(self) -> None:
        timestamp = self._timestamp(hours_ago=49)
        self._write_backup(self.backup_root, timestamp)

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--max-age-hours",
            "24",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn(timestamp, stderr)
        self.assertIn("stale", stderr)

    def test_missing_required_artifact_fails(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        backup_dir = self._write_backup(self.backup_root, timestamp)
        (backup_dir / f"btc_usd_daily_{timestamp}.csv").unlink()

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--max-age-hours",
            "24",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("btc_usd_daily_*.csv", stderr)

    def test_checksum_mismatch_fails(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        backup_dir = self._write_backup(self.backup_root, timestamp)
        (backup_dir / f"postgres_{timestamp}.dump").write_bytes(b"changed dump\n")

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--max-age-hours",
            "24",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn(timestamp, stderr)
        self.assertIn("checksum", stderr)

    def test_off_server_copy_required_and_present_passes(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        self._write_backup(self.backup_root, timestamp)
        self._write_backup(self.off_server_root, timestamp)

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--off-server-root",
            str(self.off_server_root),
            "--max-age-hours",
            "24",
        )

        self.assertEqual(0, status, stderr)
        self.assertIn(timestamp, stdout)
        self.assertIn("off-server", stdout)

    def test_off_server_copy_required_but_missing_fails(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        self._write_backup(self.backup_root, timestamp)
        self.off_server_root.mkdir()

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--off-server-root",
            str(self.off_server_root),
            "--max-age-hours",
            "24",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn(timestamp, stderr)
        self.assertIn("off-server", stderr)

    def test_off_server_copy_required_but_checksum_fails(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        self._write_backup(self.backup_root, timestamp)
        off_server_backup = self._write_backup(self.off_server_root, timestamp)
        (off_server_backup / "manifest.txt").write_text("changed\n")

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--off-server-root",
            str(self.off_server_root),
            "--max-age-hours",
            "24",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("off-server", stderr)
        self.assertIn("checksum", stderr)

    def test_no_backup_directories_fails(self) -> None:
        self.backup_root.mkdir()

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--max-age-hours",
            "24",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("no timestamped backup directories", stderr)

    def test_invalid_freshness_option_fails(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        self._write_backup(self.backup_root, timestamp)

        status, stdout, stderr = self._run_checker(
            "--backup-root",
            str(self.backup_root),
            "--max-age-hours",
            "soon",
        )

        self.assertEqual(2, status)
        self.assertEqual("", stdout)
        self.assertIn("max age", stderr)

    def test_non_finite_freshness_option_fails_without_traceback(self) -> None:
        timestamp = self._timestamp(hours_ago=1)
        self._write_backup(self.backup_root, timestamp)

        for max_age_hours in ("NaN", "Infinity"):
            with self.subTest(max_age_hours=max_age_hours):
                status, stdout, stderr = self._run_checker(
                    "--backup-root",
                    str(self.backup_root),
                    "--max-age-hours",
                    max_age_hours,
                )

                self.assertEqual(2, status)
                self.assertEqual("", stdout)
                self.assertIn("CONFIG:", stderr)
                self.assertIn("max age", stderr)
                self.assertNotIn("Traceback", stderr)


if __name__ == "__main__":
    unittest.main()
