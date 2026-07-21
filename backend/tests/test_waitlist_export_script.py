from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "export_waitlist.sh"


class WaitlistExportScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.sql_capture = self.root / "captured.sql"
        self.args_capture = self.root / "captured-args.txt"
        self.fake_compose = self.root / "fake-compose"
        self.fake_compose.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "printf '%s\\n' \"$@\" > \"${ARGS_CAPTURE}\"\n"
            "cat > \"${SQL_CAPTURE}\"\n"
            "if grep -qxF '\\copy (' \"${SQL_CAPTURE}\"; then\n"
            "  printf '\\\\copy: parse error at end of line\\n' >&2\n"
            "  exit 3\n"
            "fi\n"
            "if grep -q '^COPY ' \"${SQL_CAPTURE}\"; then\n"
            "  printf 'id,contact,normalized_contact,contact_type,locale,source,status,created_at,updated_at\\n'\n"
            "  printf 'lead-1,user@example.com,user@example.com,email,en,landing,active,2026-07-20T12:00:00Z,2026-07-20T12:00:00Z\\n'\n"
            "else\n"
            "  printf 'masked report\\n'\n"
            "fi\n"
        )
        self.fake_compose.chmod(0o755)

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "COMPOSE": str(self.fake_compose),
                "ARGS_CAPTURE": str(self.args_capture),
                "SQL_CAPTURE": str(self.sql_capture),
            }
        )
        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_default_report_uses_masked_contacts_and_compose_exec(self) -> None:
        result = self.run_script("--recent", "7")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("masked report", result.stdout)
        args = self.args_capture.read_text()
        self.assertIn("exec\n-T\ntimescaledb\npsql", args)
        sql = self.sql_capture.read_text()
        self.assertIn("masked_contact", sql)
        self.assertIn("left(contact, 1) || '***@***'", sql)
        self.assertIn("left(contact, 2) || '***'", sql)
        self.assertIn("LIMIT :'recent_limit'", sql)
        self.assertNotIn("\\copy", sql)

    def test_full_contact_export_requires_output_path(self) -> None:
        result = self.run_script("--include-contacts")

        self.assertEqual(result.returncode, 2)
        self.assertIn("--output is required", result.stderr)
        self.assertFalse(self.sql_capture.exists())

    def test_full_contact_export_rejects_repo_local_output_path(self) -> None:
        output_path = REPO_ROOT / "waitlist-export-test.csv"
        self.addCleanup(lambda: output_path.unlink(missing_ok=True))

        result = self.run_script("--include-contacts", "--output", str(output_path))

        self.assertEqual(result.returncode, 2)
        self.assertIn("outside the repository checkout", result.stderr)
        self.assertFalse(output_path.exists())
        self.assertFalse(self.sql_capture.exists())

    def test_full_contact_export_refuses_to_overwrite_existing_file(self) -> None:
        output_path = self.root / "waitlist.csv"
        output_path.write_text("existing private export\n")
        output_path.chmod(0o600)

        result = self.run_script("--include-contacts", "--output", str(output_path))

        self.assertEqual(result.returncode, 2)
        self.assertIn("Output file already exists", result.stderr)
        self.assertEqual(output_path.read_text(), "existing private export\n")
        self.assertFalse(self.sql_capture.exists())

    def test_full_contact_export_writes_private_csv_file(self) -> None:
        output_path = self.root / "waitlist.csv"

        result = self.run_script("--include-contacts", "--output", str(output_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            output_path.read_text(),
            (
                "id,contact,normalized_contact,contact_type,locale,source,status,created_at,updated_at\n"
                "lead-1,user@example.com,user@example.com,email,en,landing,active,"
                "2026-07-20T12:00:00Z,2026-07-20T12:00:00Z\n"
            ),
        )
        mode = stat.S_IMODE(output_path.stat().st_mode)
        self.assertEqual(mode, 0o600)
        sql = self.sql_capture.read_text()
        self.assertIn("COPY (", sql)
        self.assertNotIn("\\copy", sql)
        self.assertIn("contact,", sql)


if __name__ == "__main__":
    unittest.main()
