# USB Update And Install Kit V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible USB update and install kit workflow for `bitcoin-risk-brief` without putting secrets, local state, backups, dependency caches, build output, or container images on the USB drive.

**Architecture:** Keep workstation packaging separate from server execution. Add a workstation-side packager that creates `bitcoin-risk-brief-server-kit/` with a filtered project snapshot, server scripts, deployment docs, `manifest.txt`, and `SHA256SUMS`; add a server-side update wrapper that requires a verified backup and off-server or USB backup copy before it calls the existing deploy, service, and health-check scripts. Preserve the existing production `.env` at `/srv/projects/bitcoin-risk-brief/.env`.

**Tech Stack:** Python 3.13 `unittest` for packaging behavior, Bash for server-run scripts and thin workstation wrapper, SHA-256 checksums through `sha256sum` or `shasum -a 256`, Podman Compose, systemd user services, existing `scripts/backup.sh`, existing `server-kit/scripts/*.sh`.

---

## Context

- Local cache warmup implementation baseline exists as tag `cache-warmup-local-complete-2026-07-05`.
- Production deploy is not available from this session. This plan does not deploy or modify production.
- Active production path is `/srv/projects/bitcoin-risk-brief`.
- Deployment mode is USB/local-server, not direct production Git pull.
- Do not commit or push during implementation unless the operator gives a separate explicit command.

## Exact Files Likely To Create Or Modify

- Create: `server-kit/prepare_usb_kit.py`
  - Workstation packaging implementation. Builds the kit directory, copies allowlisted docs and scripts, copies a filtered project snapshot, writes `manifest.txt`, writes `SHA256SUMS`, and verifies forbidden files after staging.
- Create: `server-kit/prepare-usb-kit.sh`
  - Executable Bash wrapper for `python3 server-kit/prepare_usb_kit.py`.
- Create: `server-kit/tests/test_prepare_usb_kit.py`
  - Python `unittest` coverage for filtering, docs/scripts copy, script mode bits, manifest contents, checksums, and forbidden staged `.env` or `.git` detection.
- Create: `server-kit/scripts/07-update-bitcoin-risk-brief-from-usb.sh`
  - Server-side update flow. Creates and verifies a backup, copies it to USB or another off-server mount, deploys the project snapshot, preserves production `.env`, restarts/enables the service, and runs health/readiness checks.
- Modify: `server-kit/tests/test_server_kit_scripts.py`
  - Add static and behavior-oriented checks for the new update script sequence and script safety contracts.
- Modify: `server-kit/README-RUN-ON-SERVER.md`
  - Add V2 package layout, fresh install command, update command, backup-copy destination, and troubleshooting notes.
- Modify: `docs/operations.md`
  - Replace manual USB copy guidance with the packager command and backup-before-update flow.
- Modify: `docs/deploy-ubuntu-cloudflare.md`
  - Point USB/local-server deployments to the V2 kit flow and keep direct Git workflow separate.
- Modify: `docs/production-readiness.md`
  - Update the USB kit status after implementation and name the verification evidence required before production promotion.
- Modify if repository index docs need status updates: `docs/superpowers/README.md`, `docs/testing-and-quality.md`, `docs/production-roadmap.md`.

## Non-Goals

- No secrets on USB: never copy `.env`, API keys, Cloudflare tokens, database passwords, waitlist contacts, browser profiles, private account exports, or operator-owned secret archives.
- No container images on USB: do not package Podman/Docker image tarballs or OCI archives.
- No offline apt, npm, Python, or Podman mirror.
- No automatic restore into a live production database.
- No production deploy from the implementation session.
- No changes to product behavior, risk methodology, public API contracts, Cloudflare edge rules, or cache warmup behavior.

## Packaging Contract

The workstation command should be:

```bash
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

It should create:

```text
/Volumes/USB/bitcoin-risk-brief-server-kit/
  README-RUN-ON-SERVER.md
  manifest.txt
  SHA256SUMS
  docs/
    server-msi-cubi5-ubuntu-26.04.md
    deploy-ubuntu-cloudflare.md
    operations.md
    production-readiness.md
    superpowers/specs/2026-07-01-usb-update-install-kit-v2-design.md
  scripts/
    01-bootstrap-host.sh
    02-install-cloudflared-from-usb.sh
    03-deploy-bitcoin-risk-brief.sh
    04-enable-bitcoin-risk-service.sh
    05-health-check.sh
    06-debug-bitcoin-risk-service.sh
    07-update-bitcoin-risk-brief-from-usb.sh
  project/
    bitcoin-risk-brief/
      filtered repository snapshot
```

The project snapshot must exclude these paths and file classes:

```text
.env
.env.*
.git
backups
data
data/timescaledb
server-kit
frontend/node_modules
frontend/dist
frontend/build
frontend/playwright-report
frontend/test-results
node_modules
dist
build
coverage
playwright-report
test-results
.pytest_cache
.mypy_cache
.ruff_cache
.vite
.cache
__pycache__
*.pyc
*.log
*.tmp
*.tar
*.tar.gz
*.tgz
*.oci
*.img
.DS_Store
.idea
.vscode
```

`manifest.txt` must include these keys:

```text
created_at_utc=2026-07-05T00:00:00Z
source_commit=fe458ac28b3ba99367dcd64cc9fd14c1925a48bd
source_path=/Users/andrey.karazhev/Developer/startups/bitcoin-risk-brief
kit_path=/Volumes/USB/bitcoin-risk-brief-server-kit
project_snapshot=project/bitcoin-risk-brief
copied_categories=server-kit-readme,server-scripts,deployment-docs,project-snapshot
docs=docs/server-msi-cubi5-ubuntu-26.04.md,docs/deploy-ubuntu-cloudflare.md,docs/operations.md,docs/production-readiness.md,docs/superpowers/specs/2026-07-01-usb-update-install-kit-v2-design.md
scripts=scripts/01-bootstrap-host.sh,scripts/02-install-cloudflared-from-usb.sh,scripts/03-deploy-bitcoin-risk-brief.sh,scripts/04-enable-bitcoin-risk-service.sh,scripts/05-health-check.sh,scripts/06-debug-bitcoin-risk-service.sh,scripts/07-update-bitcoin-risk-brief-from-usb.sh
```

The manifest values above are examples from the current repository and default USB path. The implementation must write
the actual UTC timestamp, commit, source path, and kit path for each package run.

## Task 1: Add Failing Workstation Packager Tests

**Files:**
- Create: `server-kit/tests/test_prepare_usb_kit.py`
- Read: `server-kit/tests/test_server_kit_scripts.py`

- [ ] **Step 1: Add the packaging test module**

Create `server-kit/tests/test_prepare_usb_kit.py` with tests that exercise a temporary Git source repository and a temporary USB mount directory:

```python
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

        write_file(self.source / "podman-compose.yml", "services: {}\n")
        write_file(self.source / ".env.production.example", "APP_ENV=production\n")
        write_file(self.source / "scripts" / "manage.sh", "#!/usr/bin/env bash\necho manage\n")
        make_executable(self.source / "scripts" / "manage.sh")
        write_file(self.source / "backend" / "app" / "main.py", "print('backend')\n")
        write_file(self.source / "frontend" / "src" / "App.tsx", "export default function App() { return null }\n")
        write_file(self.source / "collector" / "btc-csv" / "btc_usd_daily.csv", "timeOpen;open\n")
        write_file(self.source / "migrations" / "001_initial_schema.sql", "select 1;\n")

        write_file(self.source / "docs" / "server-msi-cubi5-ubuntu-26.04.md", "# server\n")
        write_file(self.source / "docs" / "deploy-ubuntu-cloudflare.md", "# deploy\n")
        write_file(self.source / "docs" / "operations.md", "# ops\n")
        write_file(self.source / "docs" / "production-readiness.md", "# readiness\n")
        write_file(
            self.source / "docs" / "superpowers" / "specs" / "2026-07-01-usb-update-install-kit-v2-design.md",
            "# design\n",
        )
        write_file(self.source / "server-kit" / "README-RUN-ON-SERVER.md", "# run\n")
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
            ".git/config",
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

    def test_docs_scripts_manifest_and_checksums_are_created(self) -> None:
        result = self.run_packager()
        self.assertEqual(result.returncode, 0, result.stderr)
        kit = self.target / KIT_NAME

        self.assertTrue((kit / "README-RUN-ON-SERVER.md").is_file())
        self.assertTrue((kit / "docs" / "operations.md").is_file())
        self.assertTrue((kit / "docs" / "production-readiness.md").is_file())
        update_script = kit / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh"
        self.assertTrue(update_script.is_file())
        self.assertTrue(os.access(update_script, os.X_OK))

        manifest = (kit / "manifest.txt").read_text()
        self.assertIn(f"source_commit={self.commit}", manifest)
        self.assertIn(f"source_path={self.source.resolve()}", manifest)
        self.assertIn(f"kit_path={kit.resolve()}", manifest)
        self.assertIn("copied_categories=server-kit-readme,server-scripts,deployment-docs,project-snapshot", manifest)
        self.assertIn("project_snapshot=project/bitcoin-risk-brief", manifest)

        checksums = (kit / "SHA256SUMS").read_text()
        self.assertIn("manifest.txt", checksums)
        self.assertIn("README-RUN-ON-SERVER.md", checksums)
        verify = subprocess.run(
            ["shasum", "-a", "256", "-c", "SHA256SUMS"],
            cwd=kit,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(verify.returncode, 0, verify.stderr)

    def test_forbidden_staged_env_or_git_fails_validation(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("prepare_usb_kit", REPO_ROOT / "server-kit" / "prepare_usb_kit.py")
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        staged_project = self.root / "staged-project"
        write_file(staged_project / ".env", "secret\n")
        write_file(staged_project / ".git" / "config", "git\n")

        with self.assertRaises(SystemExit):
            module.verify_no_forbidden_staged_files(staged_project)
```

- [ ] **Step 2: Run the new focused test and confirm it fails**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest server-kit/tests/test_prepare_usb_kit.py -v
```

Expected: FAIL because `server-kit/prepare-usb-kit.sh` and `server-kit/prepare_usb_kit.py` do not exist.

## Task 2: Implement The Workstation Packager

**Files:**
- Create: `server-kit/prepare_usb_kit.py`
- Create: `server-kit/prepare-usb-kit.sh`
- Modify: `server-kit/tests/test_prepare_usb_kit.py`

- [ ] **Step 1: Add the executable Bash wrapper**

Create `server-kit/prepare-usb-kit.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${script_dir}/prepare_usb_kit.py" "$@"
```

Run:

```bash
chmod +x server-kit/prepare-usb-kit.sh
bash -n server-kit/prepare-usb-kit.sh
```

Expected: `bash -n` exits with code 0.

- [ ] **Step 2: Add the packager implementation**

Create `server-kit/prepare_usb_kit.py` with these behavior boundaries:

```python
KIT_NAME = "bitcoin-risk-brief-server-kit"
PROJECT_NAME = "bitcoin-risk-brief"
COPIED_CATEGORIES = ("server-kit-readme", "server-scripts", "deployment-docs", "project-snapshot")
DOCS_TO_COPY = (
    "docs/server-msi-cubi5-ubuntu-26.04.md",
    "docs/deploy-ubuntu-cloudflare.md",
    "docs/operations.md",
    "docs/production-readiness.md",
    "docs/superpowers/specs/2026-07-01-usb-update-install-kit-v2-design.md",
)
SERVER_SCRIPTS = (
    "01-bootstrap-host.sh",
    "02-install-cloudflared-from-usb.sh",
    "03-deploy-bitcoin-risk-brief.sh",
    "04-enable-bitcoin-risk-service.sh",
    "05-health-check.sh",
    "06-debug-bitcoin-risk-service.sh",
    "07-update-bitcoin-risk-brief-from-usb.sh",
)
EXCLUDED_NAMES = {
    ".env",
    ".git",
    "backups",
    "data",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "playwright-report",
    "test-results",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vite",
    ".cache",
    "__pycache__",
    ".DS_Store",
    ".idea",
    ".vscode",
    "server-kit",
}
EXCLUDED_SUFFIXES = (".pyc", ".log", ".tmp", ".tar", ".tar.gz", ".tgz", ".oci", ".img")
```

Implement functions with these public names so tests can import them:

```python
def should_exclude(path: Path, source_root: Path) -> bool:
    relative_parts = path.relative_to(source_root).parts
    name = path.name
    return (
        name in EXCLUDED_NAMES
        or name.startswith(".env")
        or any(name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)
        or "node_modules" in relative_parts
        or "playwright-report" in relative_parts
        or "test-results" in relative_parts
    )


def verify_no_forbidden_staged_files(project_dir: Path) -> None:
    forbidden = []
    for candidate in project_dir.rglob("*"):
        if candidate.name == ".git" or candidate.name == ".env" or candidate.name.startswith(".env."):
            forbidden.append(candidate)
    if forbidden:
        for path in forbidden:
            print(f"Forbidden staged file: {path}", file=sys.stderr)
        raise SystemExit(1)
```

The implementation should:

- require one argument, the USB mount or target directory;
- accept an optional second argument, the source repository root, for tests;
- resolve `kit_dir` as `${target_dir}/bitcoin-risk-brief-server-kit`;
- remove and recreate only `kit_dir`, never the target mount itself;
- copy `server-kit/README-RUN-ON-SERVER.md` to the kit root;
- copy allowlisted docs under `kit_dir/docs/`;
- copy allowlisted server scripts under `kit_dir/scripts/` and set executable bits;
- copy the filtered project snapshot to `kit_dir/project/bitcoin-risk-brief`;
- fail if `podman-compose.yml` or `.env.production.example` is missing from the staged project;
- fail if `.env`, `.env.*`, or `.git` appears anywhere inside the staged project;
- write `manifest.txt` with actual UTC timestamp, full commit SHA, source path, kit path, project snapshot path, copied categories, doc list, and script list;
- write `SHA256SUMS` for every regular file under the kit except `SHA256SUMS` itself.

- [ ] **Step 3: Run the focused packaging tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest server-kit/tests/test_prepare_usb_kit.py -v
```

Expected: PASS.

- [ ] **Step 4: Run a local package smoke check from the real repository**

Run:

```bash
rm -rf /tmp/bitcoin-risk-brief-usb-kit-smoke
mkdir -p /tmp/bitcoin-risk-brief-usb-kit-smoke
bash server-kit/prepare-usb-kit.sh /tmp/bitcoin-risk-brief-usb-kit-smoke
test -f /tmp/bitcoin-risk-brief-usb-kit-smoke/bitcoin-risk-brief-server-kit/manifest.txt
test -f /tmp/bitcoin-risk-brief-usb-kit-smoke/bitcoin-risk-brief-server-kit/SHA256SUMS
find /tmp/bitcoin-risk-brief-usb-kit-smoke/bitcoin-risk-brief-server-kit/project/bitcoin-risk-brief \( -name '.env' -o -name '.env.*' -o -name '.git' \) -print
```

Expected: the `test` commands pass and the `find` command prints no paths.

## Task 3: Add The Server Update Flow

**Files:**
- Create: `server-kit/scripts/07-update-bitcoin-risk-brief-from-usb.sh`
- Modify: `server-kit/tests/test_server_kit_scripts.py`
- Read: `scripts/backup.sh`
- Read: `server-kit/scripts/03-deploy-bitcoin-risk-brief.sh`
- Read: `server-kit/scripts/04-enable-bitcoin-risk-service.sh`
- Read: `server-kit/scripts/05-health-check.sh`

- [ ] **Step 1: Add failing tests for the update script contract**

Extend `server-kit/tests/test_server_kit_scripts.py`:

```python
    def test_update_script_requires_backup_before_deploy(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        backup_index = script.index("./scripts/backup.sh")
        deploy_index = script.index("03-deploy-bitcoin-risk-brief.sh")
        self.assertLess(backup_index, deploy_index)
        self.assertIn("Backup complete:", script)
        self.assertIn("sha256sum -c SHA256SUMS", script)
        self.assertIn("BACKUP_COPY_DEST", script)

    def test_update_script_preserves_existing_env_and_runs_health_checks(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        self.assertIn('test -f "${PROJECT_DEST}/.env"', script)
        self.assertIn("03-deploy-bitcoin-risk-brief.sh", script)
        self.assertIn("04-enable-bitcoin-risk-service.sh", script)
        self.assertIn("05-health-check.sh", script)
        self.assertNotIn("rm -f \"${PROJECT_DEST}/.env\"", script)
```

- [ ] **Step 2: Run the server-kit tests and confirm they fail**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s server-kit/tests -v
```

Expected: FAIL because `07-update-bitcoin-risk-brief-from-usb.sh` does not exist.

- [ ] **Step 3: Implement the update script**

Create `server-kit/scripts/07-update-bitcoin-risk-brief-from-usb.sh` with this flow:

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"
PUBLIC_URL="${PUBLIC_URL:-${1:-}}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kit_dir="$(cd "${script_dir}/.." && pwd)"
PROJECT_SRC="${PROJECT_SRC:-${kit_dir}/project/${PROJECT_NAME}}"
BACKUP_COPY_DEST="${BACKUP_COPY_DEST:-${kit_dir}/backups-from-server}"
```

The script should:

- refuse `PROJECT_DEST` values outside `/srv/projects/*`;
- require `PROJECT_DEST` to exist for an update;
- require `PROJECT_DEST/.env` to exist before deploying, so updates do not silently create a new production environment;
- require `PROJECT_SRC/podman-compose.yml` to exist;
- run `./scripts/backup.sh` from the current `PROJECT_DEST` as the `apps` user;
- save backup command output to `/tmp/bitcoin-risk-update-backup-${timestamp}.log`;
- parse the backup path from the `Backup complete: ${backup_path}` output line;
- require the backup directory to contain `postgres_*.dump`, `btc_usd_daily_*.csv`, `manifest.txt`, and `SHA256SUMS`;
- verify the backup directory with `sha256sum -c SHA256SUMS`;
- copy the verified backup directory to `BACKUP_COPY_DEST` with `rsync -a`;
- verify the copied backup with `sha256sum -c SHA256SUMS`;
- run `03-deploy-bitcoin-risk-brief.sh`, which already excludes `.env` and preserves existing production `.env`;
- run `04-enable-bitcoin-risk-service.sh`;
- run `05-health-check.sh`, passing `PUBLIC_URL` when provided.

- [ ] **Step 4: Run syntax and server-kit tests**

Run:

```bash
find server-kit/scripts -type f -name '*.sh' -print -exec bash -n {} \;
PYTHONPATH=backend:collector python3 -m unittest discover -s server-kit/tests -v
```

Expected: all scripts pass `bash -n`, and server-kit tests pass.

## Task 4: Update Operator Documentation

**Files:**
- Modify: `server-kit/README-RUN-ON-SERVER.md`
- Modify: `docs/operations.md`
- Modify: `docs/deploy-ubuntu-cloudflare.md`
- Modify: `docs/production-readiness.md`
- Modify if needed: `docs/superpowers/README.md`
- Modify if needed: `docs/testing-and-quality.md`
- Modify if needed: `docs/production-roadmap.md`

- [ ] **Step 1: Document workstation packaging**

In `server-kit/README-RUN-ON-SERVER.md`, add a short "Prepare The USB On The Workstation" section:

```bash
cd /path/to/bitcoin-risk-brief
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

Expected documentation facts:

- the command creates `/Volumes/USB/bitcoin-risk-brief-server-kit`;
- the kit contains docs, scripts, a filtered project snapshot, `manifest.txt`, and `SHA256SUMS`;
- the kit does not contain local `.env`, `.git`, backups, dependency caches, build output, browser artifacts, or container images;
- the workstation command is safe to rerun because it replaces only the kit directory.

- [ ] **Step 2: Document fresh install and update as separate paths**

Keep the fresh install sequence:

```bash
bash scripts/01-bootstrap-host.sh
bash scripts/02-install-cloudflared-from-usb.sh
bash scripts/03-deploy-bitcoin-risk-brief.sh
sudoedit /srv/projects/bitcoin-risk-brief/.env
bash scripts/04-enable-bitcoin-risk-service.sh
bash scripts/05-health-check.sh
```

Add the update sequence:

```bash
cd /mnt/deploy-usb/bitcoin-risk-brief-server-kit
bash scripts/07-update-bitcoin-risk-brief-from-usb.sh
```

For a public readiness check after Cloudflare Tunnel is configured:

```bash
PUBLIC_URL=https://bitcoinriskbrief.minihub.app bash scripts/07-update-bitcoin-risk-brief-from-usb.sh
```

Expected documentation facts:

- update requires the existing `/srv/projects/bitcoin-risk-brief/.env`;
- update runs backup before copying new code;
- update copies the verified backup to USB or the operator-provided `BACKUP_COPY_DEST`;
- update preserves production `.env`;
- update runs local health/readiness and optional public readiness.

- [ ] **Step 3: Update operations and deployment docs**

In `docs/operations.md` and `docs/deploy-ubuntu-cloudflare.md`, replace manual USB copy instructions with the V2 packaging command and the update script. Keep restore guidance separate and repeat that automatic live restore is not part of the kit.

- [ ] **Step 4: Update readiness/status docs**

In `docs/production-readiness.md`, record implementation status only after tests and local package smoke pass. The note should say production benefit remains pending until a real USB package is prepared and the update flow is run on the production host.

## Task 5: Full Verification

**Files:**
- Verify: `server-kit/prepare_usb_kit.py`
- Verify: `server-kit/prepare-usb-kit.sh`
- Verify: `server-kit/scripts/*.sh`
- Verify: `server-kit/tests/*.py`
- Verify: docs touched in Task 4

- [ ] **Step 1: Run packaging and server-kit tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s server-kit/tests -v
```

Expected: PASS, including packaging tests and existing server-kit tests.

- [ ] **Step 2: Run Python compile check for the packager**

Run:

```bash
python3 -m py_compile server-kit/prepare_usb_kit.py
```

Expected: PASS with no output.

- [ ] **Step 3: Run Bash syntax checks**

Run:

```bash
bash -n server-kit/prepare-usb-kit.sh
find server-kit/scripts -type f -name '*.sh' -print -exec bash -n {} \;
```

Expected: all commands exit with code 0.

- [ ] **Step 4: Run real-repo local packaging smoke**

Run:

```bash
rm -rf /tmp/bitcoin-risk-brief-usb-kit-smoke
mkdir -p /tmp/bitcoin-risk-brief-usb-kit-smoke
bash server-kit/prepare-usb-kit.sh /tmp/bitcoin-risk-brief-usb-kit-smoke
cd /tmp/bitcoin-risk-brief-usb-kit-smoke/bitcoin-risk-brief-server-kit
shasum -a 256 -c SHA256SUMS
test -f manifest.txt
test -x scripts/01-bootstrap-host.sh
test -x scripts/07-update-bitcoin-risk-brief-from-usb.sh
test -f docs/operations.md
test -f project/bitcoin-risk-brief/podman-compose.yml
find project/bitcoin-risk-brief \( -name '.env' -o -name '.env.*' -o -name '.git' -o -path '*/node_modules/*' -o -path '*/frontend/dist/*' -o -path '*/playwright-report/*' -o -name '*.tar' -o -name '*.oci' \) -print
```

Expected: checksum verification passes, file tests pass, and `find` prints no paths.

- [ ] **Step 5: Run repository docs/script diff checks**

Run:

```bash
git diff --check
git status --short --branch
```

Expected: no whitespace errors. Git status shows only intended uncommitted files.

## Implementation Completion Criteria

- Workstation packager creates a complete `bitcoin-risk-brief-server-kit` directory from the repository root.
- Filtered project snapshot excludes `.env`, `.env.*`, `.git`, backups, data volumes, dependency caches, build output, browser artifacts, local caches, logs, and container image artifacts.
- Server docs and server scripts are copied into the kit.
- Server scripts in the kit are executable.
- `manifest.txt` records commit, UTC timestamp, source path, kit path, project snapshot path, copied categories, docs, and scripts.
- `SHA256SUMS` verifies every regular file in the kit except itself.
- Packaging fails if the staged project contains `.env`, `.env.*`, or `.git`.
- Server update flow requires backup before deploy.
- Server update flow copies and verifies the backup off-server or onto the USB before promotion.
- Server update flow deploys the project snapshot while preserving existing production `.env`.
- Server update flow runs local health/readiness and optional public readiness checks.
- `PYTHONPATH=backend:collector python3 -m unittest discover -s server-kit/tests -v` passes.
- `bash -n server-kit/prepare-usb-kit.sh` passes.
- `find server-kit/scripts -type f -name '*.sh' -print -exec bash -n {} \;` passes.
- Local package smoke verifies manifest, checksums, executable scripts, copied docs, copied project, and absence of forbidden artifacts.
