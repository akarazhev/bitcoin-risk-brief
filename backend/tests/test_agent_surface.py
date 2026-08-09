from __future__ import annotations

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "frontend" / "public"

PRODUCT_URL = "https://bitcoinriskbrief.minihub.app/"
DOCS_URL = "https://docs.bitcoinriskbrief.minihub.app/"


class AgentStaticFileTests(unittest.TestCase):
    def test_all_agent_files_exist(self) -> None:
        for name in ("robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt"):
            self.assertTrue((PUBLIC_DIR / name).is_file(), f"frontend/public/{name} must exist")

    def test_robots_allows_crawling_and_points_at_the_sitemap(self) -> None:
        text = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", text)
        self.assertIn("Allow: /", text)
        self.assertIn(f"Sitemap: {PRODUCT_URL}sitemap.xml", text)

    def test_sitemap_is_valid_xml_listing_both_hosts(self) -> None:
        raw = (PUBLIC_DIR / "sitemap.xml").read_text(encoding="utf-8")
        # The stdlib parser resolves external entities. This input is a file we author in this
        # repository, but assert it declares no doctype or entities before parsing, so the test
        # stays safe without pulling defusedxml into backend/requirements.txt.
        self.assertNotIn("<!DOCTYPE", raw)
        self.assertNotIn("<!ENTITY", raw)
        root = ET.fromstring(raw)
        locations = {node.text for node in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
        self.assertIn(PRODUCT_URL, locations)
        self.assertIn(DOCS_URL, locations)

    def test_llms_txt_states_the_readiness_first_rule_and_the_advice_boundary(self) -> None:
        text = (PUBLIC_DIR / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Bitcoin Risk Brief"))
        self.assertIn("/api/readiness", text)
        self.assertIn("not financial advice", text.lower())

    def test_agent_files_never_embed_a_risk_value(self) -> None:
        import re

        pattern = re.compile(r"\brisk\b[^\n]*?\b0\.\d{3,}", re.IGNORECASE)
        for name in ("llms.txt", "llms-full.txt"):
            text = (PUBLIC_DIR / name).read_text(encoding="utf-8")
            self.assertIsNone(
                pattern.search(text),
                f"{name} must not embed a concrete risk reading; it would go stale",
            )
