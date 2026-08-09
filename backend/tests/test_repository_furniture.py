from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RepositoryFurnitureTests(unittest.TestCase):
    def test_licence_is_apache_2_0(self) -> None:
        licence = ROOT / "LICENSE"
        self.assertTrue(licence.is_file(), "LICENSE must exist at the repository root")
        text = licence.read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)

    def test_contributing_and_security_exist(self) -> None:
        for name in ("CONTRIBUTING.md", "SECURITY.md"):
            path = ROOT / name
            self.assertTrue(path.is_file(), f"{name} must exist at the repository root")
            self.assertGreater(len(path.read_text(encoding="utf-8").strip()), 200)

    def test_security_policy_names_a_reporting_channel(self) -> None:
        text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("@", text, "SECURITY.md must give a contact address for reports")

    def test_security_policy_preserves_advice_boundary_and_current_privacy_link(self) -> None:
        text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("not financial advice", text.lower())
        self.assertIn("docs/engineering/security-and-privacy.md", text)
        self.assertNotIn("docs/security-and-privacy.md", text)
