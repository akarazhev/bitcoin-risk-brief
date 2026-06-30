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


if __name__ == "__main__":
    unittest.main()
