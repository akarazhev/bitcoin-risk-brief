from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cloudflare_edge_rules.py"
spec = importlib.util.spec_from_file_location("cloudflare_edge_rules", SCRIPT_PATH)
cloudflare_edge_rules = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cloudflare_edge_rules)


class CloudflareEdgeRulesPlanTest(unittest.TestCase):
    def test_plan_contains_waf_bot_rate_limit_and_cache_rules_for_hostname(self) -> None:
        plan = cloudflare_edge_rules.build_edge_ruleset_plan("risk.example.com")

        self.assertEqual(
            set(plan),
            {
                "http_request_firewall_managed",
                "http_request_firewall_custom",
                "http_ratelimit",
                "http_request_cache_settings",
            },
        )
        managed_rule = plan["http_request_firewall_managed"]["rules"][0]
        self.assertEqual(managed_rule["action"], "execute")
        self.assertEqual(
            managed_rule["action_parameters"]["id"],
            cloudflare_edge_rules.CLOUDFLARE_MANAGED_RULESET_ID,
        )
        self.assertIn('http.host eq "risk.example.com"', managed_rule["expression"])

        bot_rule = plan["http_request_firewall_custom"]["rules"][0]
        self.assertEqual(bot_rule["action"], "managed_challenge")
        self.assertIn('http.request.uri.path eq "/api/waitlist"', bot_rule["expression"])
        self.assertIn("not cf.client.bot", bot_rule["expression"])

        rate_rules = plan["http_ratelimit"]["rules"]
        self.assertEqual(rate_rules[0]["ratelimit"]["requests_per_period"], 5)
        self.assertEqual(rate_rules[0]["ratelimit"]["period"], 60)
        self.assertEqual(rate_rules[0]["action_parameters"]["response"]["status_code"], 429)
        self.assertIn('http.request.uri.path eq "/api/waitlist"', rate_rules[0]["expression"])
        self.assertEqual(rate_rules[1]["ratelimit"]["requests_per_period"], 120)
        self.assertIn('starts_with(http.request.uri.path, "/api/")', rate_rules[1]["expression"])

        cache_rules = plan["http_request_cache_settings"]["rules"]
        self.assertFalse(cache_rules[0]["action_parameters"]["cache"])
        self.assertIn('http.request.uri.path eq "/api/waitlist"', cache_rules[0]["expression"])
        self.assertTrue(cache_rules[1]["action_parameters"]["cache"])
        self.assertEqual(cache_rules[1]["action_parameters"]["edge_ttl"]["mode"], "respect_origin")
        self.assertIn('http.request.uri.path eq "/api/risk/latest"', cache_rules[1]["expression"])

    def test_plan_escapes_hostname_for_rules_language(self) -> None:
        plan = cloudflare_edge_rules.build_edge_ruleset_plan('risk."example".com')

        expression = plan["http_request_firewall_managed"]["rules"][0]["expression"]

        self.assertIn('http.host eq "risk.\\"example\\".com"', expression)

    def test_plan_can_skip_managed_waf_for_free_plan_zones(self) -> None:
        plan = cloudflare_edge_rules.build_edge_ruleset_plan("risk.example.com", include_managed_waf=False)

        self.assertNotIn("http_request_firewall_managed", plan)
        self.assertEqual(
            set(plan),
            {
                "http_request_firewall_custom",
                "http_ratelimit",
                "http_request_cache_settings",
            },
        )

    def test_plan_can_keep_only_waitlist_rate_limit_for_free_plan_zones(self) -> None:
        plan = cloudflare_edge_rules.build_edge_ruleset_plan("risk.example.com", include_api_rate_limit=False)

        rate_rules = plan["http_ratelimit"]["rules"]
        self.assertEqual(len(rate_rules), 1)
        self.assertEqual(rate_rules[0]["ref"], "bitcoin-risk-brief:waitlist-rate-limit")
        self.assertIn('http.request.uri.path eq "/api/waitlist"', rate_rules[0]["expression"])

    def test_plan_can_use_cloudflare_free_plan_rate_limit_period(self) -> None:
        plan = cloudflare_edge_rules.build_edge_ruleset_plan("risk.example.com", rate_limit_period_seconds=10)

        rate_rules = plan["http_ratelimit"]["rules"]
        self.assertEqual(rate_rules[0]["ratelimit"]["period"], 10)
        self.assertEqual(rate_rules[1]["ratelimit"]["period"], 10)

    def test_plan_can_use_cloudflare_free_plan_mitigation_timeout(self) -> None:
        plan = cloudflare_edge_rules.build_edge_ruleset_plan(
            "risk.example.com",
            rate_limit_mitigation_timeout_seconds=10,
        )

        rate_rules = plan["http_ratelimit"]["rules"]
        self.assertEqual(rate_rules[0]["ratelimit"]["mitigation_timeout"], 10)
        self.assertEqual(rate_rules[1]["ratelimit"]["mitigation_timeout"], 10)

    def test_merge_replaces_only_owned_rules_and_preserves_existing_rules(self) -> None:
        desired = cloudflare_edge_rules.build_edge_ruleset_plan("risk.example.com")["http_ratelimit"]
        existing = {
            "id": "existing-ruleset-id",
            "rules": [
                {"ref": "customer-owned", "description": "keep me", "action": "log", "expression": "true"},
                {
                    "ref": "bitcoin-risk-brief:old-rule",
                    "description": "replace me",
                    "action": "block",
                    "expression": "true",
                },
            ],
        }

        merged = cloudflare_edge_rules.merge_rules(existing, desired)

        self.assertEqual(merged[0]["ref"], "customer-owned")
        self.assertEqual([rule["ref"] for rule in merged[1:]], [rule["ref"] for rule in desired["rules"]])

    def test_render_plan_outputs_rulesets_and_bot_dashboard_checklist(self) -> None:
        rendered = json.loads(cloudflare_edge_rules.render_edge_plan("risk.example.com"))

        self.assertIn("rulesets", rendered)
        self.assertIn("bot_protection", rendered)
        self.assertEqual(rendered["hostname"], "risk.example.com")
        self.assertIn("Bot Fight Mode", rendered["bot_protection"]["dashboard_setting"])

    def test_apply_plan_updates_existing_entrypoints_and_creates_missing_entrypoints(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.created = []
                self.updated = []

            def get_phase_entrypoint(self, zone_id, phase):
                self.zone_id = zone_id
                if phase == "http_ratelimit":
                    return {
                        "id": "rate-ruleset-id",
                        "rules": [
                            {
                                "ref": "customer-rule",
                                "description": "preserve",
                                "action": "block",
                                "expression": "true",
                            }
                        ],
                    }
                return None

            def create_ruleset(self, zone_id, payload):
                self.created.append((zone_id, payload))

            def update_ruleset(self, zone_id, ruleset_id, rules):
                self.updated.append((zone_id, ruleset_id, rules))

        fake_client = FakeClient()

        operations = cloudflare_edge_rules.apply_edge_plan("zone-123", "risk.example.com", fake_client)

        self.assertEqual(fake_client.zone_id, "zone-123")
        self.assertEqual(len(fake_client.created), 3)
        self.assertEqual(len(fake_client.updated), 1)
        updated_rules = fake_client.updated[0][2]
        self.assertEqual(updated_rules[0]["ref"], "customer-rule")
        self.assertEqual(updated_rules[1]["ref"], "bitcoin-risk-brief:waitlist-rate-limit")
        self.assertIn("created http_request_firewall_managed", operations[0])
        self.assertIn("updated http_ratelimit", " ".join(operations))

    def test_apply_plan_can_skip_managed_waf_for_free_plan_zones(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.phases = []
                self.created = []

            def get_phase_entrypoint(self, zone_id, phase):
                self.phases.append(phase)
                return None

            def create_ruleset(self, zone_id, payload):
                self.created.append((zone_id, payload))

            def update_ruleset(self, zone_id, ruleset_id, rules):
                raise AssertionError("no existing entrypoints should be updated")

        fake_client = FakeClient()

        operations = cloudflare_edge_rules.apply_edge_plan(
            "zone-123",
            "risk.example.com",
            fake_client,
            include_managed_waf=False,
        )

        self.assertNotIn("http_request_firewall_managed", fake_client.phases)
        self.assertEqual(len(fake_client.created), 3)
        self.assertEqual(len(operations), 3)

    def test_apply_plan_can_keep_only_waitlist_rate_limit_for_free_plan_zones(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.rate_rules = None

            def get_phase_entrypoint(self, zone_id, phase):
                return None

            def create_ruleset(self, zone_id, payload):
                if payload["phase"] == "http_ratelimit":
                    self.rate_rules = payload["rules"]

            def update_ruleset(self, zone_id, ruleset_id, rules):
                raise AssertionError("no existing entrypoints should be updated")

        fake_client = FakeClient()

        cloudflare_edge_rules.apply_edge_plan(
            "zone-123",
            "risk.example.com",
            fake_client,
            include_api_rate_limit=False,
        )

        self.assertIsNotNone(fake_client.rate_rules)
        self.assertEqual(len(fake_client.rate_rules), 1)
        self.assertEqual(fake_client.rate_rules[0]["ref"], "bitcoin-risk-brief:waitlist-rate-limit")

    def test_apply_plan_can_use_cloudflare_free_plan_rate_limit_period(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.rate_rules = None

            def get_phase_entrypoint(self, zone_id, phase):
                return None

            def create_ruleset(self, zone_id, payload):
                if payload["phase"] == "http_ratelimit":
                    self.rate_rules = payload["rules"]

            def update_ruleset(self, zone_id, ruleset_id, rules):
                raise AssertionError("no existing entrypoints should be updated")

        fake_client = FakeClient()

        cloudflare_edge_rules.apply_edge_plan(
            "zone-123",
            "risk.example.com",
            fake_client,
            rate_limit_period_seconds=10,
        )

        self.assertIsNotNone(fake_client.rate_rules)
        self.assertEqual(fake_client.rate_rules[0]["ratelimit"]["period"], 10)
        self.assertEqual(fake_client.rate_rules[1]["ratelimit"]["period"], 10)

    def test_apply_plan_can_use_cloudflare_free_plan_mitigation_timeout(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.rate_rules = None

            def get_phase_entrypoint(self, zone_id, phase):
                return None

            def create_ruleset(self, zone_id, payload):
                if payload["phase"] == "http_ratelimit":
                    self.rate_rules = payload["rules"]

            def update_ruleset(self, zone_id, ruleset_id, rules):
                raise AssertionError("no existing entrypoints should be updated")

        fake_client = FakeClient()

        cloudflare_edge_rules.apply_edge_plan(
            "zone-123",
            "risk.example.com",
            fake_client,
            rate_limit_mitigation_timeout_seconds=10,
        )

        self.assertIsNotNone(fake_client.rate_rules)
        self.assertEqual(fake_client.rate_rules[0]["ratelimit"]["mitigation_timeout"], 10)
        self.assertEqual(fake_client.rate_rules[1]["ratelimit"]["mitigation_timeout"], 10)


if __name__ == "__main__":
    unittest.main()
