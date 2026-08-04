import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
OFFICIAL_DUMMY_SITEKEYS = (
    "1x00000000000000000000AA",
    "2x00000000000000000000AB",
    "1x00000000000000000000BB",
    "2x00000000000000000000BB",
    "3x00000000000000000000FF",
)
OFFICIAL_DUMMY_SECRETS = (
    "1x0000000000000000000000000000000AA",
    "2x0000000000000000000000000000000AA",
    "3x0000000000000000000000000000000AA",
)
VALID_SITEKEY = "0x4AAAAAAABbCcDdEeFfGgHhIi"
VALID_SECRET = "0x4AAAAAAAJjKkLlMmNnOoPpQqRrSsTtUuVvWw"
EXPECTED_HOSTNAME = "bitcoinriskbrief.minihub.app"


class ServerKitScriptTests(unittest.TestCase):
    def _turnstile_env(self, sitekey: str = VALID_SITEKEY, secret: str = VALID_SECRET, hostname: str = EXPECTED_HOSTNAME) -> str:
        return (
            f"VITE_TURNSTILE_SITE_KEY={sitekey}\n"
            f"TURNSTILE_SECRET={secret}\n"
            f"TURNSTILE_HOSTNAMES={hostname}\n"
        )

    def _run_turnstile_preflight(self, script_name: str, env_text: str, *, preflight_only: bool) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project = tmp_path / "project"
            project.mkdir()
            (project / "podman-compose.yml").write_text("services: {}\n")
            scripts = project / "scripts"
            scripts.mkdir()
            (scripts / "backup.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
            fixture_env = tmp_path / "fixture.env"
            fixture_env.write_text(env_text)
            fake_bin = tmp_path / "bin"
            fake_bin.mkdir()
            log_path = tmp_path / "calls.log"
            (fake_bin / "sudo").write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$1\" >> \"${PREFLIGHT_LOG:?}\"\n"
                "if [[ \"$1\" == \"-u\" ]]; then exit 73; fi\n"
                "command=\"$1\"\n"
                "shift\n"
                "case \"${command}\" in\n"
                "  test)\n"
                "    if [[ \"$1\" == \"-f\" && \"$2\" == */.env ]]; then test -f \"${PREFLIGHT_FIXTURE_ENV:?}\"; else exit 0; fi\n"
                "    ;;\n"
                "  realpath) printf '%s\\n' \"$1\" ;;\n"
                "  python3)\n"
                "    arguments=()\n"
                "    for argument in \"$@\"; do\n"
                "      if [[ \"${argument}\" == /srv/projects/*/.env ]]; then argument=\"${PREFLIGHT_FIXTURE_ENV:?}\"; fi\n"
                "      arguments+=(\"${argument}\")\n"
                "    done\n"
                "    exec python3 \"${arguments[@]}\"\n"
                "    ;;\n"
                "  mkdir|rsync|chown|chmod|find) exit 73 ;;\n"
                "  *) exit 74 ;;\n"
                "esac\n"
            )
            (fake_bin / "sudo").chmod(0o755)
            app_user = subprocess.run(["id", "-un"], check=True, capture_output=True, text=True).stdout.strip()
            env = os.environ.copy()
            env.update({
                "APP_USER": app_user,
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "PREFLIGHT_FIXTURE_ENV": str(fixture_env),
                "PREFLIGHT_LOG": str(log_path),
                "PROJECT_DEST": "/srv/projects/turnstile-fixture",
                "PROJECT_SRC": str(project),
                "TURNSTILE_PREFLIGHT_ONLY": "true" if preflight_only else "false",
            })
            completed = subprocess.run(
                ["bash", str(ROOT / "scripts" / script_name)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            calls = log_path.read_text().splitlines() if log_path.exists() else []
            return completed, calls

    def test_turnstile_preflight_rejects_invalid_effective_values_without_mutating_or_printing_credentials(self) -> None:
        invalid_envs = [
            ("missing sitekey", "TURNSTILE_SECRET=secret\nTURNSTILE_HOSTNAMES=bitcoinriskbrief.minihub.app\n"),
            ("blank sitekey", self._turnstile_env(sitekey="")),
            ("quoted blank sitekey", self._turnstile_env(sitekey='""')),
            ("commented blank sitekey", self._turnstile_env(sitekey=" # comment")),
            ("duplicate sitekey", self._turnstile_env() + f"VITE_TURNSTILE_SITE_KEY={VALID_SITEKEY}\n"),
            ("invalid sitekey assignment", self._turnstile_env().replace(f"VITE_TURNSTILE_SITE_KEY={VALID_SITEKEY}", "VITE_TURNSTILE_SITE_KEY")),
            ("placeholder sitekey", self._turnstile_env(sitekey="replace-with-public-turnstile-sitekey")),
            ("placeholder secret", self._turnstile_env(secret="replace-with-private-turnstile-secret")),
            ("localhost hostname", self._turnstile_env(hostname="localhost")),
            ("hostname list", self._turnstile_env(hostname=f"{EXPECTED_HOSTNAME},localhost")),
            ("loopback hostname", self._turnstile_env(hostname="127.0.0.1")),
        ]
        invalid_envs.extend((f"dummy sitekey {sitekey}", self._turnstile_env(sitekey=sitekey)) for sitekey in OFFICIAL_DUMMY_SITEKEYS)
        invalid_envs.extend((f"quoted dummy sitekey {sitekey}", self._turnstile_env(sitekey=f'"{sitekey}"')) for sitekey in OFFICIAL_DUMMY_SITEKEYS)
        invalid_envs.extend((f"dummy secret {secret}", self._turnstile_env(secret=secret)) for secret in OFFICIAL_DUMMY_SECRETS)
        invalid_envs.extend((f"quoted dummy secret {secret}", self._turnstile_env(secret=f'"{secret}"')) for secret in OFFICIAL_DUMMY_SECRETS)
        invalid_envs.extend((f"placeholder sitekey {sitekey}", self._turnstile_env(sitekey=sitekey)) for sitekey in (
            "replace-with-turnstile-sitekey",
            "example-turnstile-sitekey",
            "placeholder-turnstile-sitekey",
            "your-real-sitekey",
        ))
        invalid_envs.extend((f"placeholder secret {secret}", self._turnstile_env(secret=secret)) for secret in (
            "replace-with-turnstile-secret",
            "example-turnstile-secret",
            "placeholder-turnstile-secret",
            "your-real-secret-key",
        ))

        for label, env_text in invalid_envs:
            with self.subTest(label=label):
                completed, calls = self._run_turnstile_preflight("03-deploy-bitcoin-risk-brief.sh", env_text, preflight_only=True)
                self.assertEqual(completed.returncode, 1, completed.stderr)
                self.assertNotIn("mkdir", calls)
                self.assertNotIn("rsync", calls)
                output = completed.stdout + completed.stderr
                for credential in (VALID_SITEKEY, VALID_SECRET, *OFFICIAL_DUMMY_SITEKEYS, *OFFICIAL_DUMMY_SECRETS):
                    self.assertNotIn(credential, output)

    def test_turnstile_preflight_accepts_unquoted_and_quoted_production_shaped_values_without_printing_them(self) -> None:
        for env_text in (
            self._turnstile_env(),
            self._turnstile_env(sitekey=f'"{VALID_SITEKEY}"', secret=f"'{VALID_SECRET}'", hostname=f'"{EXPECTED_HOSTNAME}" # production'),
            f"VITE_TURNSTILE_SITE_KEY: {VALID_SITEKEY}\nTURNSTILE_SECRET: {VALID_SECRET}\nTURNSTILE_HOSTNAMES: {EXPECTED_HOSTNAME}\n",
        ):
            with self.subTest(env_text=env_text):
                completed, calls = self._run_turnstile_preflight("03-deploy-bitcoin-risk-brief.sh", env_text, preflight_only=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("python3", calls)
                self.assertNotIn(VALID_SITEKEY, completed.stdout + completed.stderr)
                self.assertNotIn(VALID_SECRET, completed.stdout + completed.stderr)

    def test_fresh_and_update_preflights_run_before_their_first_mutation(self) -> None:
        fresh, fresh_calls = self._run_turnstile_preflight("03-deploy-bitcoin-risk-brief.sh", self._turnstile_env(), preflight_only=False)
        update, update_calls = self._run_turnstile_preflight("07-update-bitcoin-risk-brief-from-usb.sh", self._turnstile_env(), preflight_only=False)

        self.assertEqual(fresh.returncode, 73, fresh.stderr)
        self.assertLess(fresh_calls.index("python3"), fresh_calls.index("mkdir"))
        self.assertNotIn("rsync", fresh_calls)
        self.assertEqual(update.returncode, 73, update.stderr)
        self.assertLess(update_calls.index("python3"), update_calls.index("-u"))
        self.assertNotIn("rsync", update_calls)

    def test_deploy_from_usb_defaults_to_deploy_without_backup_gate(self) -> None:
        script = (ROOT / "deploy-from-usb.sh").read_text()

        deploy_index = script.index('bash "${script_dir}/scripts/03-deploy-bitcoin-risk-brief.sh"')
        enable_index = script.index('bash "${script_dir}/scripts/04-enable-bitcoin-risk-service.sh"')
        restart_index = script.index('restart "${SERVICE_NAME}.service"')
        migrate_index = script.index("  run_migrations\n")
        health_index = script.index('bash "${script_dir}/scripts/05-health-check.sh"')

        self.assertIn("--with-backup", script)
        self.assertIn("WITH_BACKUP=false", script)
        self.assertNotIn("./scripts/backup.sh", script)
        self.assertLess(deploy_index, enable_index)
        self.assertLess(enable_index, restart_index)
        self.assertLess(restart_index, migrate_index)
        self.assertLess(migrate_index, health_index)
        self.assertIn('cd \'${PROJECT_DEST}\' && ./scripts/manage.sh migrate', script)

    def test_deploy_from_usb_verifies_kit_checksums_before_default_deploy(self) -> None:
        script = (ROOT / "deploy-from-usb.sh").read_text()

        checksum_index = script.index("sha256sum -c SHA256SUMS")
        deploy_index = script.index("03-deploy-bitcoin-risk-brief.sh")
        backup_index = script.index("07-update-bitcoin-risk-brief-from-usb.sh")

        self.assertLess(checksum_index, deploy_index)
        self.assertLess(checksum_index, backup_index)

    def test_service_script_checks_project_directory_with_privileged_helper(self) -> None:
        script = (ROOT / "scripts" / "04-enable-bitcoin-risk-service.sh").read_text()

        self.assertIn('if ! as_root test -d "${PROJECT_DEST}"; then', script)
        self.assertNotIn('if [[ ! -d "${PROJECT_DEST}" ]]; then', script)

    def test_service_script_starts_apps_user_manager_before_user_systemctl(self) -> None:
        script = (ROOT / "scripts" / "04-enable-bitcoin-risk-service.sh").read_text()

        self.assertIn('as_root systemctl start "user@${app_uid}.service"', script)

    def test_service_script_sets_home_for_user_systemctl(self) -> None:
        script = (ROOT / "scripts" / "04-enable-bitcoin-risk-service.sh").read_text()

        self.assertIn('HOME="/home/${APP_USER}"', script)

    def test_debug_script_collects_user_and_system_service_evidence(self) -> None:
        script = (ROOT / "scripts" / "06-debug-bitcoin-risk-service.sh").read_text()

        self.assertIn("systemctl --user", script)
        self.assertIn('run_user_systemctl status "${SERVICE_NAME}.service"', script)
        self.assertIn('systemctl status "${SERVICE_NAME}.service"', script)
        self.assertIn('journalctl --user -u "${SERVICE_NAME}.service"', script)
        self.assertIn('journalctl -u "${SERVICE_NAME}.service"', script)
        self.assertIn('podman-compose ps', script)

    def test_debug_script_masks_environment_secrets(self) -> None:
        script = (ROOT / "scripts" / "06-debug-bitcoin-risk-service.sh").read_text()

        self.assertIn("mask_env_file()", script)
        self.assertIn("mask_secret_stream()", script)
        self.assertIn("DB_PASSWORD", script)
        self.assertIn("TOKEN", script)
        self.assertIn("API_KEY", script)
        self.assertIn("podman-compose config", script)
        self.assertIn("mask_secret_stream", script)

    def test_update_script_requires_backup_before_deploy(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        backup_index = script.index('"${PROJECT_SRC}/scripts/backup.sh"')
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

    def test_update_script_restarts_service_before_health_checks(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        enable_index = script.index("04-enable-bitcoin-risk-service.sh")
        restart_index = script.find('restart "${SERVICE_NAME}.service"')
        migrate_index = script.index("\nrun_migrations\n")
        health_index = script.index("05-health-check.sh")
        self.assertNotEqual(restart_index, -1)
        self.assertLess(enable_index, restart_index)
        self.assertLess(restart_index, migrate_index)
        self.assertLess(migrate_index, health_index)
        self.assertIn('cd \'${PROJECT_DEST}\' && ./scripts/manage.sh migrate', script)

    def test_update_script_validates_canonical_project_dest_before_backup(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        realpath_index = script.find('project_dest_real="$(as_root realpath "${PROJECT_DEST}")"')
        validation_index = script.find('case "${project_dest_real}" in')
        export_index = script.find('PROJECT_DEST="${project_dest_real}"')
        backup_index = script.index('"${PROJECT_SRC}/scripts/backup.sh"')
        self.assertNotEqual(realpath_index, -1)
        self.assertNotEqual(validation_index, -1)
        self.assertNotEqual(export_index, -1)
        self.assertLess(realpath_index, validation_index)
        self.assertLess(validation_index, export_index)
        self.assertLess(export_index, backup_index)

    def test_update_script_runs_backup_from_usb_snapshot_with_deployed_project_cwd(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        self.assertIn('if [[ ! -f "${PROJECT_SRC}/scripts/backup.sh" ]]; then', script)
        self.assertIn(
            'run_as_app bash -c \'cd "$1" && bash "$2"\' _ "${PROJECT_DEST}" "${PROJECT_SRC}/scripts/backup.sh"',
            script,
        )

    def test_update_script_copies_backup_to_usb_without_posix_ownership(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        self.assertIn("rsync -a --no-owner --no-group --no-perms", script)

    def test_backup_script_sets_rootless_podman_runtime_defaults(self) -> None:
        script = (REPO_ROOT / "scripts" / "backup.sh").read_text()

        self.assertIn('export XDG_RUNTIME_DIR="/run/user/${current_uid}"', script)
        self.assertIn('export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"', script)

    def test_backup_script_has_no_compose_dump_fallback(self) -> None:
        script = (REPO_ROOT / "scripts" / "backup.sh").read_text()

        self.assertNotIn("BACKUP_DUMP_METHOD", script)
        self.assertNotIn("create_postgres_dump_with_compose", script)
        self.assertNotIn('"${COMPOSE}" -f "${COMPOSE_FILE}" exec -T timescaledb', script)

    def test_backup_dump_prefers_direct_podman_exec_with_bounded_waits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_source = tmp_path / "btc_usd_daily.csv"
            csv_source.write_text("date,close\n2026-07-07,100000\n")
            backup_dir = tmp_path / "backups"
            fake_podman = tmp_path / "podman"
            fake_timeout = tmp_path / "timeout"
            podman_log = tmp_path / "podman-args.txt"
            timeout_log = tmp_path / "timeout-args.txt"

            fake_podman.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$@\" >> \"${FAKE_PODMAN_LOG}\"\n"
                "if [[ \"${1:-}\" == \"ps\" ]]; then\n"
                "  printf 'abc123\\tbitcoin-risk-brief_timescaledb_1\\tdocker.io/timescale/timescaledb:2.17.2-pg16\\n'\n"
                "elif [[ \"${1:-}\" == \"exec\" ]]; then\n"
                "  printf 'fake-postgres-dump\\n'\n"
                "else\n"
                "  echo \"unexpected podman args: $*\" >&2\n"
                "  exit 2\n"
                "fi\n"
            )
            fake_timeout.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$@\" >> \"${FAKE_TIMEOUT_LOG}\"\n"
                "duration=\"$1\"\n"
                "shift\n"
                "exec \"$@\"\n"
            )
            fake_podman.chmod(0o755)
            fake_timeout.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "BACKUP_DIR": str(backup_dir),
                    "BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS": "5",
                    "BACKUP_DUMP_LOCK_WAIT_TIMEOUT": "12s",
                    "BACKUP_DUMP_TIMEOUT_SECONDS": "7",
                    "BACKUP_PODMAN_PS_TIMEOUT_SECONDS": "3",
                    "CSV_SOURCE": str(csv_source),
                    "FAKE_PODMAN_LOG": str(podman_log),
                    "FAKE_TIMEOUT_LOG": str(timeout_log),
                    "PATH": f"{tmp_path}{os.pathsep}{env.get('PATH', '')}",
                }
            )

            result = subprocess.run(
                ["bash", str(REPO_ROOT / "scripts" / "backup.sh")],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(timeout_log.exists(), "backup.sh did not run the dump through timeout")
            timeout_lines = timeout_log.read_text().splitlines()
            self.assertIn("3s", timeout_lines)
            self.assertIn("7s", timeout_lines)
            podman_args = podman_log.read_text()
            self.assertIn("ps\n--format\n", podman_args)
            self.assertIn("exec\nabc123\nsh\n-c\n", podman_args)
            self.assertIn('PGCONNECT_TIMEOUT="$1"', podman_args)
            self.assertIn('PGPASSWORD="${POSTGRES_PASSWORD:-}"', podman_args)
            self.assertIn("pg_dump --no-password", podman_args)
            self.assertIn('--lock-wait-timeout="$2"', podman_args)
            self.assertIn("-h 127.0.0.1", podman_args)
            backup_dirs = [path for path in backup_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(backup_dirs), 1)
            manifest = (backup_dirs[0] / "manifest.txt").read_text()
            self.assertIn("backup_dump_method=podman", manifest)


if __name__ == "__main__":
    unittest.main()
