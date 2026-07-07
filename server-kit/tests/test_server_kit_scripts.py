import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


class ServerKitScriptTests(unittest.TestCase):
    def test_deploy_from_usb_defaults_to_deploy_without_backup_gate(self) -> None:
        script = (ROOT / "deploy-from-usb.sh").read_text()

        deploy_index = script.index('bash "${script_dir}/scripts/03-deploy-bitcoin-risk-brief.sh"')
        enable_index = script.index('bash "${script_dir}/scripts/04-enable-bitcoin-risk-service.sh"')
        restart_index = script.index('restart "${SERVICE_NAME}.service"')
        health_index = script.index('bash "${script_dir}/scripts/05-health-check.sh"')

        self.assertIn("--with-backup", script)
        self.assertIn("WITH_BACKUP=false", script)
        self.assertNotIn("./scripts/backup.sh", script)
        self.assertLess(deploy_index, enable_index)
        self.assertLess(enable_index, restart_index)
        self.assertLess(restart_index, health_index)

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

    def test_update_script_restarts_service_before_health_checks(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        enable_index = script.index("04-enable-bitcoin-risk-service.sh")
        restart_index = script.find('restart "${SERVICE_NAME}.service"')
        health_index = script.index("05-health-check.sh")
        self.assertNotEqual(restart_index, -1)
        self.assertLess(enable_index, restart_index)
        self.assertLess(restart_index, health_index)

    def test_update_script_validates_canonical_project_dest_before_backup(self) -> None:
        script = (ROOT / "scripts" / "07-update-bitcoin-risk-brief-from-usb.sh").read_text()

        realpath_index = script.find('project_dest_real="$(as_root realpath "${PROJECT_DEST}")"')
        validation_index = script.find('case "${project_dest_real}" in')
        export_index = script.find('PROJECT_DEST="${project_dest_real}"')
        backup_index = script.index("./scripts/backup.sh")
        self.assertNotEqual(realpath_index, -1)
        self.assertNotEqual(validation_index, -1)
        self.assertNotEqual(export_index, -1)
        self.assertLess(realpath_index, validation_index)
        self.assertLess(validation_index, export_index)
        self.assertLess(export_index, backup_index)

    def test_backup_dump_runs_non_interactively_with_bounded_waits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_source = tmp_path / "btc_usd_daily.csv"
            csv_source.write_text("date,close\n2026-07-07,100000\n")
            backup_dir = tmp_path / "backups"
            fake_compose = tmp_path / "podman-compose"
            fake_timeout = tmp_path / "timeout"
            compose_log = tmp_path / "compose-args.txt"
            timeout_log = tmp_path / "timeout-args.txt"

            fake_compose.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$@\" > \"${FAKE_COMPOSE_LOG}\"\n"
                "printf 'fake-postgres-dump\\n'\n"
            )
            fake_timeout.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$@\" > \"${FAKE_TIMEOUT_LOG}\"\n"
                "duration=\"$1\"\n"
                "shift\n"
                "exec \"$@\"\n"
            )
            fake_compose.chmod(0o755)
            fake_timeout.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "BACKUP_DIR": str(backup_dir),
                    "BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS": "5",
                    "BACKUP_DUMP_LOCK_WAIT_TIMEOUT": "12s",
                    "BACKUP_DUMP_TIMEOUT_SECONDS": "7",
                    "COMPOSE": str(fake_compose),
                    "CSV_SOURCE": str(csv_source),
                    "FAKE_COMPOSE_LOG": str(compose_log),
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
            self.assertEqual(timeout_log.read_text().splitlines()[0], "7s")
            compose_args = compose_log.read_text()
            self.assertIn("exec\n-T\ntimescaledb\nsh\n-c\n", compose_args)
            self.assertIn('PGCONNECT_TIMEOUT="$1"', compose_args)
            self.assertIn('PGPASSWORD="${POSTGRES_PASSWORD:-}"', compose_args)
            self.assertIn("pg_dump --no-password", compose_args)
            self.assertIn('--lock-wait-timeout="$2"', compose_args)
            self.assertIn("-h 127.0.0.1", compose_args)


if __name__ == "__main__":
    unittest.main()
