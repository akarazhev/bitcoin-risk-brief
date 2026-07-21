from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGER = REPO_ROOT / "server-kit" / "prepare-usb-kit.sh"
KIT_NAME = "bitcoin-risk-brief-server-kit"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class PrepareUsbKitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.target = self.root / "usb"
        self.source.mkdir()
        self.target.mkdir()

        write_file(
            self.source / ".gitignore",
            "*.tsbuildinfo\ncollector/btc-csv/incoming/*.csv\nscratch-output/\n",
        )
        write_file(self.source / "podman-compose.yml", "services: {}\n")
        write_file(self.source / ".env.production.example", "APP_ENV=production\n")
        write_file(self.source / "scripts" / "manage.sh", "#!/usr/bin/env bash\necho manage\n")
        make_executable(self.source / "scripts" / "manage.sh")
        write_file(self.source / "scripts" / "export_waitlist.sh", "#!/usr/bin/env bash\necho waitlist\n")
        make_executable(self.source / "scripts" / "export_waitlist.sh")
        write_file(self.source / "backend" / "app" / "main.py", "print('backend')\n")
        write_file(self.source / "frontend" / "src" / "App.tsx", "export default function App() { return null }\n")
        write_file(self.source / "frontend" / "tsconfig.tsbuildinfo", "build cache\n")
        write_file(self.source / "collector" / "btc-csv" / "btc_usd_daily.csv", "timeOpen;open\n")
        write_file(self.source / "collector" / "btc-csv" / "incoming" / ".gitkeep", "")
        write_file(self.source / "collector" / "btc-csv" / "incoming" / "local-download.csv", "local state\n")
        write_file(self.source / "migrations" / "001_initial_schema.sql", "select 1;\n")
        write_file(self.source / "scratch-output" / "local-report.txt", "ignored local report\n")
        write_file(self.source / ".venv" / "bin" / "activate", "local venv\n")
        write_file(self.source / ".superpowers" / "brainstorm" / "state", "local agent state\n")
        write_file(self.source / "notes" / "ai-process.md", "local notes\n")
        write_file(self.source / "backend" / "app" / "._main.py", "mac metadata\n")

        write_file(self.source / "docs" / "server-msi-cubi5-ubuntu-26.04.md", "# server\n")
        write_file(self.source / "docs" / "deploy-ubuntu-cloudflare.md", "# deploy\n")
        write_file(self.source / "docs" / "operations.md", "# ops\n")
        write_file(self.source / "docs" / "production-readiness.md", "# readiness\n")
        write_file(
            self.source / "docs" / "superpowers" / "specs" / "2026-07-01-usb-update-install-kit-v2-design.md",
            "# design\n",
        )
        write_file(self.source / "server-kit" / "README-RUN-ON-SERVER.md", "# run\n")
        write_file(self.source / "server-kit" / "deploy-from-usb.sh", "#!/usr/bin/env bash\necho deploy\n")
        make_executable(self.source / "server-kit" / "deploy-from-usb.sh")
        for name in (
            "01-bootstrap-host.sh",
            "02-install-cloudflared-from-usb.sh",
            "03-deploy-bitcoin-risk-brief.sh",
            "04-enable-bitcoin-risk-service.sh",
            "05-health-check.sh",
            "06-debug-bitcoin-risk-service.sh",
            "07-update-bitcoin-risk-brief-from-usb.sh",
        ):
            script = self.source / "server-kit" / "scripts" / name
            write_file(script, "#!/usr/bin/env bash\necho script\n")
            make_executable(script)

        forbidden_files = [
            ".env",
            ".env.local",
            "backups/20260705T000000Z/postgres.dump",
            "data/timescaledb/PG_VERSION",
            "frontend/node_modules/vite/index.js",
            "frontend/dist/index.html",
            "frontend/playwright-report/index.html",
            "frontend/test-results/result.json",
            ".pytest_cache/CACHEDIR.TAG",
            ".mypy_cache/state.json",
            ".ruff_cache/state.json",
            ".cache/tool/state",
            "backend/app/__pycache__/main.cpython-313.pyc",
            "backend/app/._brief.py",
            "podman-images/frontend.tar",
            "image.oci",
            ".DS_Store",
            ".vscode/settings.json",
        ]
        for relative in forbidden_files:
            write_file(self.source / relative, "forbidden\n")

        subprocess.run(["git", "init"], cwd=self.source, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "add", "."], cwd=self.source, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture"],
            cwd=self.source,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.source, text=True).strip()

    def run_packager(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(PACKAGER), str(self.target), str(self.source)],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_project_snapshot_excludes_forbidden_local_state(self) -> None:
        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)
        project = self.target / KIT_NAME / "project" / "bitcoin-risk-brief"

        forbidden_paths = [
            ".env",
            ".env.local",
            ".git",
            "backups",
            "data",
            "frontend/node_modules",
            "frontend/dist",
            "frontend/playwright-report",
            "frontend/test-results",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".cache",
            "backend/app/__pycache__",
            "backend/app/._brief.py",
            "backend/app/._main.py",
            "podman-images/frontend.tar",
            "image.oci",
            ".DS_Store",
            ".vscode",
        ]
        for relative in forbidden_paths:
            self.assertFalse((project / relative).exists(), relative)

        self.assertTrue((project / "podman-compose.yml").is_file())
        self.assertTrue((project / ".env.production.example").is_file())
        self.assertTrue((project / "collector" / "btc-csv" / "btc_usd_daily.csv").is_file())
        self.assertTrue(os.access(project / "scripts" / "export_waitlist.sh", os.X_OK))

    def test_project_snapshot_excludes_git_ignored_local_artifacts(self) -> None:
        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)
        project = self.target / KIT_NAME / "project" / "bitcoin-risk-brief"

        self.assertTrue((project / "collector" / "btc-csv" / "incoming" / ".gitkeep").is_file())
        self.assertFalse((project / "frontend" / "tsconfig.tsbuildinfo").exists())
        self.assertFalse((project / "collector" / "btc-csv" / "incoming" / "local-download.csv").exists())
        self.assertFalse((project / "scratch-output").exists())

    def test_project_snapshot_excludes_local_tooling_directories(self) -> None:
        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)
        project = self.target / KIT_NAME / "project" / "bitcoin-risk-brief"

        for relative in (".venv", ".superpowers", "notes"):
            self.assertFalse((project / relative).exists(), relative)

    def test_project_snapshot_excludes_apple_double_metadata_files(self) -> None:
        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)
        kit = self.target / KIT_NAME

        apple_double_files = [path for path in kit.rglob("._*")]
        self.assertEqual(apple_double_files, [])

    def test_generated_apple_double_files_are_removed_before_validation(self) -> None:
        import importlib.util

        module_path = REPO_ROOT / "server-kit" / "prepare_usb_kit.py"
        spec = importlib.util.spec_from_file_location("prepare_usb_kit", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        original_copy_project_snapshot = module.copy_project_snapshot

        def copy_project_snapshot_with_generated_metadata(source_root: Path, project_dir: Path) -> None:
            original_copy_project_snapshot(source_root, project_dir)
            write_file(project_dir / "backend" / "app" / "._main.py", "generated metadata\n")

        module.copy_project_snapshot = copy_project_snapshot_with_generated_metadata
        try:
            kit = module.build_kit(self.target, self.source)
        finally:
            module.copy_project_snapshot = original_copy_project_snapshot

        self.assertFalse((kit / "project" / "bitcoin-risk-brief" / "backend" / "app" / "._main.py").exists())

    def test_project_snapshot_does_not_follow_source_symlinks(self) -> None:
        outside_secret = self.root / "outside-secret.txt"
        outside_secret.write_text("do-not-copy\n")
        (self.source / "linked-secret.txt").symlink_to(outside_secret)

        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)

        project = self.target / KIT_NAME / "project" / "bitcoin-risk-brief"
        self.assertFalse((project / "linked-secret.txt").exists())

    def test_docs_scripts_manifest_and_checksums_are_created(self) -> None:
        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)
        kit = self.target / KIT_NAME

        self.assertTrue((kit / "README-RUN-ON-SERVER.md").is_file())
        deploy_script = kit / "deploy-from-usb.sh"
        self.assertTrue(deploy_script.is_file())
        self.assertTrue(os.access(deploy_script, os.X_OK))
        self.assertTrue((kit / "docs" / "operations.md").is_file())
        self.assertTrue((kit / "docs" / "production-readiness.md").is_file())
        update_script = kit / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh"
        self.assertTrue(update_script.is_file())
        self.assertTrue(os.access(update_script, os.X_OK))

        manifest = (kit / "manifest.txt").read_text()
        self.assertIn(f"source_commit={self.commit}", manifest)
        self.assertIn(f"source_path={self.source.resolve()}", manifest)
        self.assertIn(f"kit_path={kit.resolve()}", manifest)
        self.assertIn("copied_categories=server-kit-readme,server-entrypoints,server-scripts,deployment-docs,project-snapshot", manifest)
        self.assertIn("project_snapshot=project/bitcoin-risk-brief", manifest)
        self.assertIn("entrypoints=deploy-from-usb.sh", manifest)

        checksums = (kit / "SHA256SUMS").read_text()
        self.assertIn("manifest.txt", checksums)
        self.assertIn("README-RUN-ON-SERVER.md", checksums)
        self.assertIn("deploy-from-usb.sh", checksums)
        verify = subprocess.run(
            ["shasum", "-a", "256", "-c", "SHA256SUMS"],
            cwd=kit,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(verify.returncode, 0, verify.stderr)

    def test_missing_future_update_script_does_not_block_packaging(self) -> None:
        update_script = self.source / "server-kit" / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh"
        update_script.unlink()

        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)

        kit = self.target / KIT_NAME
        self.assertTrue((kit / "scripts" / "01-bootstrap-host.sh").is_file())
        self.assertFalse((kit / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").exists())
        manifest = (kit / "manifest.txt").read_text()
        self.assertIn("scripts/01-bootstrap-host.sh", manifest)
        self.assertNotIn("scripts/07-update-bitcoin-risk-brief-from-usb.sh", manifest)

    def test_forbidden_staged_env_or_git_fails_validation(self) -> None:
        import importlib.util

        module_path = REPO_ROOT / "server-kit" / "prepare_usb_kit.py"
        self.assertTrue(module_path.is_file(), f"missing packager module: {module_path}")
        spec = importlib.util.spec_from_file_location("prepare_usb_kit", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        staged_project = self.root / "staged-project"
        write_file(staged_project / ".env", "secret\n")
        write_file(staged_project / ".git" / "config", "git\n")

        with self.assertRaises(SystemExit):
            module.verify_no_forbidden_staged_files(staged_project)

    def test_forbidden_staged_local_tooling_fails_validation(self) -> None:
        import importlib.util

        module_path = REPO_ROOT / "server-kit" / "prepare_usb_kit.py"
        spec = importlib.util.spec_from_file_location("prepare_usb_kit", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        staged_project = self.root / "staged-local-tooling"
        write_file(staged_project / ".venv" / "bin" / "activate", "local venv\n")

        with self.assertRaises(SystemExit):
            module.verify_no_forbidden_staged_files(staged_project)


if __name__ == "__main__":
    unittest.main()
