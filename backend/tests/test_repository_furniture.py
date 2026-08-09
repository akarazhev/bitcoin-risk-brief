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


class ReadmeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_readme_is_a_shopfront_not_a_manual(self) -> None:
        self.assertLess(
            len(self.text.splitlines()),
            160,
            "the README should be an overview; operational detail belongs in docs/operations/",
        )

    def test_the_first_forty_lines_describe_the_product(self) -> None:
        head = "\n".join(self.text.splitlines()[:40]).lower()
        self.assertIn("bitcoin", head)
        for phrase in ("accepted limitation", "remains pending", "unclaimed"):
            self.assertNotIn(phrase, head, "limitation language belongs in the operations tier, not the first screen")

    def test_readme_links_the_agent_surface_and_the_licence(self) -> None:
        self.assertIn("llms.txt", self.text)
        self.assertIn("/api/openapi.json", self.text)
        self.assertIn("Apache-2.0", self.text)

    def test_readme_keeps_the_advice_disclaimer(self) -> None:
        self.assertIn("not financial advice", self.text.lower())
