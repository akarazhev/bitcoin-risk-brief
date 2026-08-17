from __future__ import annotations

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import re

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "frontend" / "public"
NGINX_CONF = ROOT / "frontend" / "nginx.conf"

PRODUCT_URL = "https://bitcoinriskbrief.minihub.app/"
DOCS_URL = "https://docs.bitcoinriskbrief.minihub.app/"
DOCS = ROOT / "docs"
CONCRETE_RISK_READING_RE = re.compile(
    r"(?:\\?[\"']risk\\?[\"']|\brisk\b)\s*(?:[:=]|\s)\s*\\?[\"']?0\.\d{3,}\b",
    re.IGNORECASE,
)


class AgentStaticFileTests(unittest.TestCase):
    def test_all_agent_files_exist(self) -> None:
        for name in ("robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt"):
            self.assertTrue((PUBLIC_DIR / name).is_file(), f"frontend/public/{name} must exist")

    def test_robots_allows_crawling_and_points_at_the_sitemap(self) -> None:
        text = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", text)
        self.assertIn("Allow: /", text)
        self.assertIn(f"Sitemap: {PRODUCT_URL}sitemap.xml", text)
        self.assertIn("not financial advice", text.lower())

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
        self.assertIn("not financial advice", raw.lower())

    def test_llms_txt_states_the_readiness_first_rule_and_the_advice_boundary(self) -> None:
        text = (PUBLIC_DIR / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Bitcoin Risk Brief"))
        self.assertIn("/api/readiness", text)
        self.assertIn("not financial advice", text.lower())

    def test_agent_files_never_embed_a_risk_value(self) -> None:
        for name in ("llms.txt", "llms-full.txt"):
            text = (PUBLIC_DIR / name).read_text(encoding="utf-8")
            self.assertIsNone(
                CONCRETE_RISK_READING_RE.search(text),
                f"{name} must not embed a concrete risk reading; it would go stale",
            )

    def test_concrete_risk_pattern_catches_json_key_examples_without_banning_shapes(self) -> None:
        blocked = (
            '"risk": 0.3025',
            '\\"risk\\": 0.3025',
            "risk = 0.3025",
            "risk 0.3025",
        )
        allowed = (
            '"risk": "number in [0.0, 1.0]"',
            '"current_risk": "number in [0.0, 1.0]"',
            "target risk values from `0.0` to `1.0`",
        )
        for sample in blocked:
            with self.subTest(sample=sample):
                self.assertIsNotNone(CONCRETE_RISK_READING_RE.search(sample))
        for sample in allowed:
            with self.subTest(sample=sample):
                self.assertIsNone(CONCRETE_RISK_READING_RE.search(sample))

    def test_agent_files_describe_runtime_readiness_semantics(self) -> None:
        for name in ("llms.txt", "llms-full.txt"):
            text = (PUBLIC_DIR / name).read_text(encoding="utf-8")
            normalized = " ".join(text.split())
            with self.subTest(name=name):
                self.assertNotIn("not_ready", text)
                self.assertNotIn("version travels with every response", normalized)
                self.assertNotIn("product returns 503 rather than serving a stale figure", normalized)
                self.assertIn("Product data endpoints can still return the latest stored rows", normalized)
                self.assertIn("not current unless readiness is `ready`", normalized)

        full_text = (PUBLIC_DIR / "llms-full.txt").read_text(encoding="utf-8")
        self.assertIn('"status": "ready | degraded"', full_text)


class NginxRouteTests(unittest.TestCase):
    def test_unknown_paths_are_not_rewritten_to_the_app_shell(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertNotIn(
            "try_files $uri $uri/ /index.html;",
            text,
            "the catch-all fallback answers 200 for every path, including nonexistent ones",
        )

    def test_root_serves_the_app_shell(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("location = / {", text)
        self.assertIn("try_files /index.html =404;", text)

    def test_fallthrough_location_returns_404(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("try_files $uri =404;", text)


class AgentDocumentationTests(unittest.TestCase):
    def test_the_three_agent_pages_exist(self) -> None:
        for relative in (
            "agents/agent-access-pack.md",
            "agents/openapi.md",
            "engineering/freshness-and-validation.md",
        ):
            self.assertTrue((DOCS / relative).is_file(), f"docs/{relative} must exist")

    def test_the_access_pack_states_the_readiness_first_rule(self) -> None:
        text = (DOCS / "agents" / "agent-access-pack.md").read_text(encoding="utf-8")
        self.assertIn("/api/readiness", text)
        self.assertIn("X-Cache-Version", text)
        self.assertIn("not financial advice", text.lower())

    def test_brief_shape_examples_use_a_state_matching_the_example_risk(self) -> None:
        expected = (
            '"as_of": "2026-06-25T00:00:00+00:00",\n'
            '    "risk": 0.3025,\n'
            '    "risk_state": "neutral"'
        )
        for relative in (
            "agents/agent-access-pack.md",
            "engineering/api-reference.md",
        ):
            text = (DOCS / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn(expected, text)

    def test_access_pack_binds_product_dates_to_current_readiness(self) -> None:
        text = (DOCS / "agents" / "agent-access-pack.md").read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        for token in (
            "`data.timestamp`",
            "`meta.evaluation_date`",
            "`meta.base.timestamp`",
            "`data.as_of`",
            "`data[*].timestamp`",
            "both readiness `latest_date` and `covered_end`",
            "reject the value or label it as not matching current readiness",
            "browser or edge cache",
        ):
            with self.subTest(token=token):
                self.assertIn(token, normalized)

    def test_access_pack_documents_agent_demand_tracking(self) -> None:
        text = (DOCS / "agents" / "agent-access-pack.md").read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        for token in (
            "source=agent_access",
            "source=risk_signal_license",
            '"source": "agent_access"',
            "Collect manual requests for",
            "API keys",
            "webhooks",
            "MCP",
            "SDKs",
            "embeds",
            "alerts",
            "commercial use",
            "one-product risk-signal licensing",
        ):
            with self.subTest(token=token):
                self.assertIn(token, normalized)

    def test_the_freshness_page_explains_every_readiness_check(self) -> None:
        text = (DOCS / "engineering" / "freshness-and-validation.md").read_text(encoding="utf-8")
        for token in (
            "data_fresh",
            "data_age_days",
            "covered_end",
            "latest_matches_validation_end",
            "btc_risk_validation",
            "X-Cache-Version",
            "503",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_mcp_server_page_is_installable_and_discoverable(self) -> None:
        page = DOCS / "agents" / "mcp-server.md"
        self.assertTrue(page.is_file(), "docs/agents/mcp-server.md must exist")

        text = page.read_text(encoding="utf-8")
        self.assertIn("npx -y @akarazhev/bitcoin-risk-brief-mcp", text)
        self.assertIn("not financial advice", text.lower())

        public_llms = (PUBLIC_DIR / "llms.txt").read_text(encoding="utf-8")
        self.assertIn(
            "https://docs.bitcoinriskbrief.minihub.app/agents/mcp-server/",
            public_llms,
        )


class DocsSiteAgentFileTests(unittest.TestCase):
    def test_docs_site_serves_its_own_llms_txt(self) -> None:
        path = DOCS / "llms.txt"
        self.assertTrue(path.is_file(), "docs/llms.txt must exist so the docs site publishes it")

    def test_docs_llms_txt_points_at_pages_that_exist(self) -> None:
        text = (DOCS / "llms.txt").read_text(encoding="utf-8")
        prefix = "https://docs.bitcoinriskbrief.minihub.app/"
        referenced = []
        for line in text.splitlines():
            if prefix not in line:
                continue
            tail = line.split(prefix, 1)[1].lstrip()
            if tail:
                referenced.append(tail)

        self.assertGreater(len(referenced), 3, "the map should cover more than a couple of pages")
        for ref in referenced:
            with self.subTest(page=ref):
                self.assertEqual(ref, ref.rstrip(), "the URL must terminate the line without trailing whitespace")
                self.assertNotIn(" ", ref, "the URL must end its line, so no prose follows it")
                self.assertTrue(
                    (DOCS / f"{ref.rstrip('/')}.md").is_file(),
                    f"docs/{ref} does not exist, so the published URL would 404",
                )

    def test_docs_llms_txt_is_not_excluded_from_the_build(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        exclude_block = config.split("exclude_docs:", 1)[1].split("nav:", 1)[0]
        self.assertNotIn("llms.txt", exclude_block)
