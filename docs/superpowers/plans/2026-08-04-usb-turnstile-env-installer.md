# USB Turnstile Environment Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one USB-kit command that safely replaces the three Turnstile assignments in the existing production `.env` as `apps`, without deploying or printing secrets.

**Architecture:** A Bash wrapper locates the plaintext Turnstile fragment relative to the mounted USB kit, validates it with the existing Python preflight, and runs an atomic filter-plus-append merge as `apps`. The existing workstation packager ships the wrapper in the checksummed kit, while the user-approved plaintext fragment remains separately in the USB root.

**Tech Stack:** Bash, Python 3.13 `unittest`, existing `turnstile-env-preflight.py`, GNU/Linux `runuser`, `awk`, `cat`, `mktemp`, SHA-256 USB manifest verification.

**Execution status:** Tasks 1 and 2 are implemented in `47a60f5`; Task 3 local tests and shell validation are complete.

## Global Constraints

- The operator command is exactly `sudo bash scripts/08-install-turnstile-env-from-usb.sh` from the mounted kit.
- The production target is `/srv/projects/bitcoin-risk-brief/.env` and target mutation runs as `apps`.
- The fragment is `bitcoin-risk-brief-turnstile.env` in the USB root, outside `bitcoin-risk-brief-server-kit`.
- Exactly `VITE_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET`, and `TURNSTILE_HOSTNAMES` are replaced; unrelated assignments remain unchanged.
- `TURNSTILE_HOSTNAMES` must be exactly `bitcoinriskbrief.minihub.app`.
- Validate before replacement, use a same-directory temporary file, set mode `0600`, and replace atomically.
- Never print credentials, copy the Cloudflare API token, deploy, restart, migrate, back up, or run health checks.
- The separate plaintext fragment is an explicit operator decision and must never be copied into the checksummed kit or Git.

---

### Task 1: Ship the installer in prepared USB kits

**Files:**
- Modify: `server-kit/prepare_usb_kit.py`
- Modify: `server-kit/tests/test_prepare_usb_kit.py`

**Interfaces:**
- Consumes: `REQUIRED_SERVER_SCRIPTS` and the existing `copy_server_scripts(...)` packaging flow.
- Produces: executable `scripts/08-install-turnstile-env-from-usb.sh` in every prepared kit and its entry in `manifest.txt` and `SHA256SUMS`.

- [ ] **Step 1: Write the failing packaging test**

Add `08-install-turnstile-env-from-usb.sh` to the fixture-script tuple in `PrepareUsbKitTests.setUp`, then extend `test_docs_scripts_manifest_and_checksums_are_created`:

```python
installer_script = kit / "scripts" / "08-install-turnstile-env-from-usb.sh"
self.assertTrue(installer_script.is_file())
self.assertTrue(os.access(installer_script, os.X_OK))

manifest = (kit / "manifest.txt").read_text()
self.assertIn("scripts/08-install-turnstile-env-from-usb.sh", manifest)

checksums = (kit / "SHA256SUMS").read_text()
self.assertIn("scripts/08-install-turnstile-env-from-usb.sh", checksums)
```

- [ ] **Step 2: Run the focused packaging test and verify RED**

Run:

```bash
python3 -m unittest server-kit.tests.test_prepare_usb_kit.PrepareUsbKitTests.test_docs_scripts_manifest_and_checksums_are_created -v
```

Expected: FAIL because the packager does not copy `08-install-turnstile-env-from-usb.sh`.

- [ ] **Step 3: Add the installer filename to the required packaging contract**

Append the filename to `REQUIRED_SERVER_SCRIPTS` in `server-kit/prepare_usb_kit.py`:

```python
REQUIRED_SERVER_SCRIPTS = (
    "01-bootstrap-host.sh",
    "02-install-cloudflared-from-usb.sh",
    "03-deploy-bitcoin-risk-brief.sh",
    "04-enable-bitcoin-risk-service.sh",
    "05-health-check.sh",
    "06-debug-bitcoin-risk-service.sh",
    "08-install-turnstile-env-from-usb.sh",
    "turnstile-env-preflight.py",
)
```

- [ ] **Step 4: Run the focused packaging test and verify GREEN**

Run the Step 2 command again.

Expected: PASS, with the installer present, executable, manifested, and checksummed.

### Task 2: Implement the atomic `apps`-owned environment merge with TDD

**Files:**
- Create: `server-kit/scripts/08-install-turnstile-env-from-usb.sh`
- Modify: `server-kit/tests/test_server_kit_scripts.py`

**Interfaces:**
- Consumes: the fragment path derived as `${kit_dir}/../bitcoin-risk-brief-turnstile.env`, `PROJECT_DEST`, `APP_USER`, and `turnstile-env-preflight.py`.
- Produces: an atomically replaced `${PROJECT_DEST}/.env` with exactly one assignment for each Turnstile key, all unrelated lines retained, and mode `0600`.

- [ ] **Step 1: Write the failing successful-merge test**

Add this helper and test to `ServerKitScriptTests`:

```python
def _stage_turnstile_installer(self, tmp_path: Path, fragment: str) -> tuple[Path, Path]:
    usb_root = tmp_path / "usb"
    scripts = usb_root / "bitcoin-risk-brief-server-kit" / "scripts"
    scripts.mkdir(parents=True)
    installer = scripts / "08-install-turnstile-env-from-usb.sh"
    installer_source = ROOT / "scripts" / installer.name
    self.assertTrue(installer_source.is_file(), f"missing installer: {installer_source}")
    installer.write_bytes(installer_source.read_bytes())
    installer.chmod(0o755)
    validator = scripts / "turnstile-env-preflight.py"
    validator.write_bytes((ROOT / "scripts" / validator.name).read_bytes())
    validator.chmod(0o755)
    (usb_root / "bitcoin-risk-brief-turnstile.env").write_text(fragment)

    project = tmp_path / "project"
    project.mkdir()
    env_file = project / ".env"
    env_file.write_text(
        "APP_ENV=production\n"
        "VITE_TURNSTILE_SITE_KEY=old-sitekey-value\n"
        "TURNSTILE_SECRET=old-secret-value\n"
        "TURNSTILE_HOSTNAMES=localhost\n"
        "CORS_ORIGINS=https://bitcoinriskbrief.minihub.app\n"
    )
    return installer, env_file

def test_turnstile_installer_replaces_only_turnstile_values_as_app_without_printing_them(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        installer, env_file = self._stage_turnstile_installer(tmp_path, self._turnstile_env())
        app_user = subprocess.run(["id", "-un"], check=True, capture_output=True, text=True).stdout.strip()
        env = os.environ.copy()
        env.update({"APP_USER": app_user, "PROJECT_DEST": str(env_file.parent)})

        completed = subprocess.run(
            ["bash", str(installer)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        installed = env_file.read_text()
        self.assertIn("APP_ENV=production\n", installed)
        self.assertIn("CORS_ORIGINS=https://bitcoinriskbrief.minihub.app\n", installed)
        self.assertEqual(installed.count("VITE_TURNSTILE_SITE_KEY="), 1)
        self.assertEqual(installed.count("TURNSTILE_SECRET="), 1)
        self.assertEqual(installed.count("TURNSTILE_HOSTNAMES="), 1)
        self.assertIn(self._turnstile_env(), installed)
        self.assertEqual(env_file.stat().st_mode & 0o777, 0o600)
        output = completed.stdout + completed.stderr
        self.assertNotIn(VALID_SITEKEY, output)
        self.assertNotIn(VALID_SECRET, output)
        self.assertNotIn("deploy", output.lower())
```

- [ ] **Step 2: Run the focused installer test and verify RED**

Run:

```bash
python3 -m unittest server-kit.tests.test_server_kit_scripts.ServerKitScriptTests.test_turnstile_installer_replaces_only_turnstile_values_as_app_without_printing_them -v
```

Expected: FAIL because `server-kit/scripts/08-install-turnstile-env-from-usb.sh` does not exist.

- [ ] **Step 3: Implement the minimal installer**

Create `server-kit/scripts/08-install-turnstile-env-from-usb.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kit_dir="$(cd "${script_dir}/.." && pwd)"
usb_root="$(cd "${kit_dir}/.." && pwd)"
fragment="${TURNSTILE_FRAGMENT:-${usb_root}/bitcoin-risk-brief-turnstile.env}"
env_file="${PROJECT_DEST}/.env"
validator="${script_dir}/turnstile-env-preflight.py"
current_user="$(id -un)"

run_as_app() {
  if [[ "${current_user}" == "${APP_USER}" ]]; then
    "$@"
  elif [[ "${EUID}" -eq 0 ]]; then
    runuser -u "${APP_USER}" -- "$@"
  else
    sudo -u "${APP_USER}" "$@"
  fi
}

if [[ "${current_user}" != "${APP_USER}" && "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

if ! id "${APP_USER}" >/dev/null 2>&1; then
  echo "User ${APP_USER} does not exist. Run 01-bootstrap-host.sh first." >&2
  exit 1
fi
if [[ ! -f "${env_file}" ]]; then
  echo "Production environment file not found: ${env_file}" >&2
  exit 1
fi
if [[ ! -f "${fragment}" ]]; then
  echo "Turnstile environment fragment not found: ${fragment}" >&2
  exit 1
fi
if [[ ! -f "${validator}" ]]; then
  echo "Turnstile validator not found: ${validator}" >&2
  exit 1
fi
if ! python3 "${validator}" --env-file "${fragment}"; then
  echo "Turnstile fragment validation failed." >&2
  exit 1
fi

run_as_app bash -c '
set -euo pipefail
env_file="$1"
fragment="$2"
validator="$3"
tmp_file="$(mktemp "${env_file}.turnstile.XXXXXX")"
cleanup() { rm -f "${tmp_file}"; }
trap cleanup EXIT

awk '\''!/^[[:space:]]*(export[[:space:]]+)?(VITE_TURNSTILE_SITE_KEY|TURNSTILE_SECRET|TURNSTILE_HOSTNAMES)[[:space:]]*=/'\'' \
  "${env_file}" > "${tmp_file}"
cat "${fragment}" >> "${tmp_file}"
python3 "${validator}" --env-file "${tmp_file}"
chmod 600 "${tmp_file}"
mv "${tmp_file}" "${env_file}"
trap - EXIT
' _ "${env_file}" "${fragment}" "${validator}"

printf 'Turnstile configuration installed in %s as %s.\n' "${env_file}" "${APP_USER}"
```

- [ ] **Step 4: Run the focused installer test and verify GREEN**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Write the failing invalid-fragment atomicity test**

Add:

```python
def test_turnstile_installer_rejects_invalid_fragment_without_changing_env(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        installer, env_file = self._stage_turnstile_installer(
            tmp_path,
            self._turnstile_env(secret=OFFICIAL_DUMMY_SECRETS[0]),
        )
        original = env_file.read_bytes()
        app_user = subprocess.run(["id", "-un"], check=True, capture_output=True, text=True).stdout.strip()
        env = os.environ.copy()
        env.update({"APP_USER": app_user, "PROJECT_DEST": str(env_file.parent)})

        completed = subprocess.run(
            ["bash", str(installer)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(env_file.read_bytes(), original)
        self.assertNotIn(OFFICIAL_DUMMY_SECRETS[0], completed.stdout + completed.stderr)
```

- [ ] **Step 6: Run the atomicity test and verify GREEN**

Run:

```bash
python3 -m unittest server-kit.tests.test_server_kit_scripts.ServerKitScriptTests.test_turnstile_installer_rejects_invalid_fragment_without_changing_env -v
```

Expected: PASS because the implementation validates the fragment before creating the temporary target.

- [ ] **Step 7: Verify shell syntax and the focused server-kit module**

Run:

```bash
bash -n server-kit/scripts/08-install-turnstile-env-from-usb.sh
python3 -m unittest server-kit.tests.test_server_kit_scripts -v
```

Expected: shell syntax exits 0 and all server-kit script tests pass.

- [ ] **Step 8: Commit the packaging contract and installer behavior**

```bash
git add server-kit/prepare_usb_kit.py server-kit/tests/test_prepare_usb_kit.py \
  server-kit/scripts/08-install-turnstile-env-from-usb.sh server-kit/tests/test_server_kit_scripts.py
git commit -m "feat: install Turnstile env from USB"
```

### Task 3: Document, verify, publish, and refresh the physical USB kit

**Files:**
- Modify: `server-kit/README-RUN-ON-SERVER.md`
- Modify: `docs/superpowers/plans/2026-08-04-usb-turnstile-env-installer.md`
- Write outside Git: `/Volumes/USB/bitcoin-risk-brief-server-kit/`
- Preserve outside Git: `/Volumes/USB/bitcoin-risk-brief-turnstile.env`

**Interfaces:**
- Consumes: the verified installer, packager, attached `/Volumes/USB`, and existing three-key plaintext fragment.
- Produces: a checksummed server kit whose manifest revision equals `origin/main`, plus one simple operator command in the README.

- [ ] **Step 1: Add the operator command to the fresh-install instructions**

After creating the production `.env`, document:

```bash
sudo bash scripts/08-install-turnstile-env-from-usb.sh
```

State that the command only replaces the three Turnstile assignments, does not deploy, and expects
`bitcoin-risk-brief-turnstile.env` beside the `bitcoin-risk-brief-server-kit` directory.

- [ ] **Step 2: Run complete local verification**

Run:

```bash
python3 -m unittest discover -s server-kit/tests -v
bash -n server-kit/scripts/*.sh
git diff --check
git status --short --branch
```

Expected: every server-kit test passes, all shell scripts parse, the diff is clean, and only intended files are modified.

- [ ] **Step 3: Commit documentation and plan tracking**

```bash
git add server-kit/README-RUN-ON-SERVER.md docs/superpowers/plans/2026-08-04-usb-turnstile-env-installer.md
git commit -m "docs: add USB Turnstile env command"
```

- [ ] **Step 4: Push `main` and tag the verified revision**

```bash
git push origin main
git tag -a usb-turnstile-env-installer-2026-08-04 -m "USB Turnstile env installer"
git push origin usb-turnstile-env-installer-2026-08-04
```

Expected: `origin/main` and the annotated tag point to the verified implementation revision.

- [ ] **Step 5: Wait for GitHub checks and require all success**

Use `gh api repos/akarazhev/bitcoin-risk-brief/commits/HEAD/check-runs` until every returned check is `completed/success`.

Expected: all repository checks succeed; any failure blocks USB preparation.

- [ ] **Step 6: Rebuild the attached USB kit**

Run:

```bash
bash server-kit/prepare-usb-kit.sh /Volumes/USB
```

Expected: `/Volumes/USB/bitcoin-risk-brief-server-kit/scripts/08-install-turnstile-env-from-usb.sh` exists and the separate `/Volumes/USB/bitcoin-risk-brief-turnstile.env` is preserved.

- [ ] **Step 7: Verify USB provenance and checksums without printing secrets**

Run:

```bash
test "$(awk -F= '$1 == "source_commit" { print $2 }' /Volumes/USB/bitcoin-risk-brief-server-kit/manifest.txt)" = "$(git rev-parse HEAD)"
test -f /Volumes/USB/bitcoin-risk-brief-turnstile.env
python3 server-kit/scripts/turnstile-env-preflight.py --env-file /Volumes/USB/bitcoin-risk-brief-turnstile.env
cd /Volumes/USB/bitcoin-risk-brief-server-kit
shasum -a 256 -c SHA256SUMS
```

Expected: manifest revision matches `HEAD`, the three-key fragment passes no-output validation, and every checksum is `OK`.

- [ ] **Step 8: Report the one server command**

From the mounted kit directory on the server, the operator runs:

```bash
sudo bash scripts/08-install-turnstile-env-from-usb.sh
```

Report the verified commit/tag and test/checksum counts. Do not claim production deployment; this script only updates the server `.env`.
