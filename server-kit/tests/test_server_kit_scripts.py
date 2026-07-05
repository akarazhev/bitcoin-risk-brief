from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ServerKitScriptTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
