from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

EXPECTED_LAYOUT = {
    "product": {"product-spec.md", "risk-methodology.md"},
    "engineering": {
        "architecture.md",
        "data-pipeline.md",
        "api-reference.md",
        "testing-and-quality.md",
        "security-and-privacy.md",
        "frontend-qa.md",
        "waitlist.md",
    },
    "operations": {
        "operations.md",
        "production-readiness.md",
        "production-evidence-log.md",
        "production-roadmap.md",
        "deploy-ubuntu-cloudflare.md",
        "server-msi-cubi5-ubuntu-26.04.md",
        "pilot-learning-loop.md",
        "marketing-and-growth.md",
        "dependency-license-review.md",
        "backup-restore-evidence-packet-template.md",
        "import-provenance-evidence-packet-template.md",
        "launch-snapshot-evidence-packet-template.md",
        "monitoring-alert-evidence-packet-template.md",
        "operator-launch-decision-packet-template.md",
    },
}

OPERATIONAL_BANNER = "**Operational log.**"


class DocsStructureTests(unittest.TestCase):
    def test_every_document_is_in_its_tier(self) -> None:
        for tier, names in EXPECTED_LAYOUT.items():
            present = {path.name for path in (DOCS / tier).glob("*.md")}
            self.assertEqual(names, present, f"docs/{tier}/ contents differ from the planned layout")

    def test_no_stray_markdown_left_at_the_docs_root(self) -> None:
        stray = {path.name for path in DOCS.glob("*.md")} - {"README.md", "index.md"}
        self.assertEqual(set(), stray, f"unmoved documents remain at docs/: {stray}")

    def test_agents_tier_has_a_public_landing_page(self) -> None:
        landing = DOCS / "agents" / "index.md"
        self.assertTrue(landing.is_file(), "docs/agents/index.md must keep the agents tier tracked")
        self.assertIn("not financial advice", landing.read_text(encoding="utf-8").lower())

    def test_operations_pages_carry_the_operational_log_banner(self) -> None:
        for path in (DOCS / "operations").glob("*.md"):
            with self.subTest(path=path.name):
                self.assertIn(OPERATIONAL_BANNER, path.read_text(encoding="utf-8"))

    def test_no_markdown_link_points_at_a_moved_path(self) -> None:
        moved = {name for names in EXPECTED_LAYOUT.values() for name in names}
        broken: list[str] = []
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts or "node_modules" in path.parts:
                continue
            for target in re.findall(r"\]\(([^)#]+\.md)[^)]*\)", path.read_text(encoding="utf-8")):
                candidate = (path.parent / target).resolve()
                if candidate.name in moved and not candidate.exists():
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual([], broken, "links point at pre-restructure paths")

    def test_current_documentation_index_links_resolve(self) -> None:
        broken: list[str] = []
        for path in (DOCS / "README.md", DOCS / "index.md"):
            for target in re.findall(r"\]\(([^)#]+)[^)]*\)", path.read_text(encoding="utf-8")):
                if "://" in target:
                    continue
                candidate = path.parent / target
                if target.endswith("/"):
                    candidate /= "index.md"
                if not candidate.resolve().exists():
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual([], broken, "current documentation index links must resolve to tracked artifacts")
