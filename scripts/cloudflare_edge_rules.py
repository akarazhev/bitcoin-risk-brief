#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"
CLOUDFLARE_MANAGED_RULESET_ID = "efb7b8c949ac4650a09736fc376e9aee"
OWNED_RULE_PREFIX = "bitcoin-risk-brief:"

READINESS_PATH = "/api/readiness"

PUBLIC_READ_PATHS = (
    "/api/risk/latest",
    "/api/risk/history",
    "/api/risk/levels",
    "/api/brief/latest",
)


class CloudflareApiError(RuntimeError):
    pass


def _cf_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _host_expression(hostname: str) -> str:
    return f'http.host eq "{_cf_string(hostname)}"'


def _waitlist_expression(hostname: str) -> str:
    return (
        f"({_host_expression(hostname)} and http.request.method eq \"POST\" "
        'and http.request.uri.path eq "/api/waitlist")'
    )


def _readiness_expression(hostname: str) -> str:
    return (
        f"({_host_expression(hostname)} and http.request.method eq \"GET\" "
        f'and http.request.uri.path eq "{READINESS_PATH}")'
    )


def _public_read_expression(hostname: str) -> str:
    paths = " or ".join(f'http.request.uri.path eq "{path}"' for path in PUBLIC_READ_PATHS)
    return (
        f"({_host_expression(hostname)} and http.request.method eq \"GET\" "
        f"and ({paths}))"
    )


def _api_burst_expression(hostname: str) -> str:
    return (
        f"({_host_expression(hostname)} and starts_with(http.request.uri.path, \"/api/\") "
        f"and not {_waitlist_expression(hostname)})"
    )


def _waitlist_bot_expression(hostname: str) -> str:
    return (
        f"({_waitlist_expression(hostname)} and not cf.client.bot and ("
        'not http.user_agent contains "Mozilla/" '
        'or lower(http.user_agent) contains "bot" '
        'or lower(http.user_agent) contains "crawler" '
        'or lower(http.user_agent) contains "spider"))'
    )


def build_edge_ruleset_plan(
    hostname: str,
    *,
    include_managed_waf: bool = True,
    include_api_rate_limit: bool = True,
    rate_limit_period_seconds: int = 60,
    rate_limit_mitigation_timeout_seconds: int | None = None,
    waitlist_requests_per_minute: int = 5,
    api_requests_per_minute: int = 120,
) -> dict[str, dict[str, Any]]:
    waitlist_mitigation_timeout = (
        rate_limit_mitigation_timeout_seconds
        if rate_limit_mitigation_timeout_seconds is not None
        else 600
    )
    api_mitigation_timeout = (
        rate_limit_mitigation_timeout_seconds
        if rate_limit_mitigation_timeout_seconds is not None
        else 300
    )
    plan = {
        "http_request_firewall_managed": {
            "name": "Bitcoin Risk Brief - WAF managed rules",
            "description": "Execute Cloudflare managed WAF rules for the public Bitcoin Risk Brief hostname.",
            "kind": "zone",
            "phase": "http_request_firewall_managed",
            "rules": [
                {
                    "ref": f"{OWNED_RULE_PREFIX}cloudflare-managed-ruleset",
                    "description": "Execute Cloudflare Managed Ruleset",
                    "enabled": True,
                    "expression": _host_expression(hostname),
                    "action": "execute",
                    "action_parameters": {"id": CLOUDFLARE_MANAGED_RULESET_ID},
                }
            ],
        },
        "http_request_firewall_custom": {
            "name": "Bitcoin Risk Brief - bot challenge rules",
            "description": "Low-friction bot challenge for suspicious waitlist submissions.",
            "kind": "zone",
            "phase": "http_request_firewall_custom",
            "rules": [
                {
                    "ref": f"{OWNED_RULE_PREFIX}waitlist-bot-challenge",
                    "description": "Managed challenge for non-verified bot-like waitlist submissions",
                    "enabled": True,
                    "expression": _waitlist_bot_expression(hostname),
                    "action": "managed_challenge",
                }
            ],
        },
        "http_ratelimit": {
            "name": "Bitcoin Risk Brief - API rate limits",
            "description": "Pilot traffic limits for waitlist and public API bursts.",
            "kind": "zone",
            "phase": "http_ratelimit",
            "rules": [
                {
                    "ref": f"{OWNED_RULE_PREFIX}waitlist-rate-limit",
                    "description": "Rate limit waitlist submissions",
                    "enabled": True,
                    "expression": _waitlist_expression(hostname),
                    "action": "block",
                    "action_parameters": {
                        "response": {
                            "status_code": 429,
                            "content_type": "text/plain",
                            "content": "Too many waitlist requests",
                        }
                    },
                    "ratelimit": {
                        "characteristics": ["ip.src", "cf.colo.id"],
                        "period": rate_limit_period_seconds,
                        "requests_per_period": waitlist_requests_per_minute,
                        "mitigation_timeout": waitlist_mitigation_timeout,
                        "requests_to_origin": True,
                    },
                },
                {
                    "ref": f"{OWNED_RULE_PREFIX}api-rate-limit",
                    "description": "Rate limit public API bursts",
                    "enabled": True,
                    "expression": _api_burst_expression(hostname),
                    "action": "block",
                    "action_parameters": {
                        "response": {
                            "status_code": 429,
                            "content_type": "text/plain",
                            "content": "Too many API requests",
                        }
                    },
                    "ratelimit": {
                        "characteristics": ["ip.src", "cf.colo.id"],
                        "period": rate_limit_period_seconds,
                        "requests_per_period": api_requests_per_minute,
                        "mitigation_timeout": api_mitigation_timeout,
                        "requests_to_origin": True,
                    },
                },
            ],
        },
        "http_request_cache_settings": {
            "name": "Bitcoin Risk Brief - API cache settings",
            "description": "Respect origin cache headers for public reads and bypass waitlist writes.",
            "kind": "zone",
            "phase": "http_request_cache_settings",
            "rules": [
                {
                    "ref": f"{OWNED_RULE_PREFIX}waitlist-cache-bypass",
                    "description": "Bypass cache for waitlist submissions",
                    "enabled": True,
                    "expression": _waitlist_expression(hostname),
                    "action": "set_cache_settings",
                    "action_parameters": {"cache": False},
                },
                {
                    "ref": f"{OWNED_RULE_PREFIX}readiness-cache-bypass",
                    "description": "Bypass cache for readiness status",
                    "enabled": True,
                    "expression": _readiness_expression(hostname),
                    "action": "set_cache_settings",
                    "action_parameters": {"cache": False},
                },
                {
                    "ref": f"{OWNED_RULE_PREFIX}public-api-origin-cache",
                    "description": "Respect origin cache headers for cacheable public read endpoints",
                    "enabled": True,
                    "expression": _public_read_expression(hostname),
                    "action": "set_cache_settings",
                    "action_parameters": {
                        "cache": True,
                        "edge_ttl": {"mode": "respect_origin"},
                        "browser_ttl": {"mode": "respect_origin"},
                    },
                },
            ],
        },
    }
    if not include_managed_waf:
        del plan["http_request_firewall_managed"]
    if not include_api_rate_limit:
        plan["http_ratelimit"]["rules"] = [
            rule
            for rule in plan["http_ratelimit"]["rules"]
            if rule["ref"] == f"{OWNED_RULE_PREFIX}waitlist-rate-limit"
        ]
    return plan


def merge_rules(existing_ruleset: dict[str, Any] | None, desired_ruleset: dict[str, Any]) -> list[dict[str, Any]]:
    existing_rules = []
    if existing_ruleset:
        existing_rules = [
            rule
            for rule in existing_ruleset.get("rules", [])
            if not str(rule.get("ref", "")).startswith(OWNED_RULE_PREFIX)
        ]
    return existing_rules + list(desired_ruleset["rules"])


def render_edge_plan(
    hostname: str,
    *,
    include_managed_waf: bool = True,
    include_api_rate_limit: bool = True,
    rate_limit_period_seconds: int = 60,
    rate_limit_mitigation_timeout_seconds: int | None = None,
) -> str:
    plan = build_edge_ruleset_plan(
        hostname,
        include_managed_waf=include_managed_waf,
        include_api_rate_limit=include_api_rate_limit,
        rate_limit_period_seconds=rate_limit_period_seconds,
        rate_limit_mitigation_timeout_seconds=rate_limit_mitigation_timeout_seconds,
    )
    rendered = {
        "hostname": hostname,
        "rulesets": plan,
        "bot_protection": {
            "dashboard_setting": "Enable Cloudflare Bot Fight Mode, Super Bot Fight Mode, or equivalent bot protection for the hostname after ruleset deployment.",
            "repo_managed_rule": f"{OWNED_RULE_PREFIX}waitlist-bot-challenge",
        },
    }
    return json.dumps(rendered, indent=2, sort_keys=True)


class CloudflareApiClient:
    def __init__(self, api_token: str, *, api_base: str = CLOUDFLARE_API_BASE) -> None:
        self.api_token = api_token
        self.api_base = api_base.rstrip("/")

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        allow_404: bool = False,
    ) -> dict[str, Any] | None:
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.api_base}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if allow_404 and exc.code == 404:
                return None
            error_body = exc.read().decode("utf-8", errors="replace")
            raise CloudflareApiError(f"Cloudflare API {method} {path} failed: HTTP {exc.code} {error_body}") from exc

        if not decoded.get("success", False):
            raise CloudflareApiError(f"Cloudflare API {method} {path} failed: {decoded.get('errors')}")
        return decoded.get("result")

    def get_phase_entrypoint(self, zone_id: str, phase: str) -> dict[str, Any] | None:
        return self.request_json(
            "GET",
            f"/zones/{zone_id}/rulesets/phases/{phase}/entrypoint",
            allow_404=True,
        )

    def create_ruleset(self, zone_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        return self.request_json("POST", f"/zones/{zone_id}/rulesets", payload)

    def update_ruleset(self, zone_id: str, ruleset_id: str, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
        return self.request_json("PUT", f"/zones/{zone_id}/rulesets/{ruleset_id}", {"rules": rules})


def apply_edge_plan(
    zone_id: str,
    hostname: str,
    client: CloudflareApiClient,
    *,
    include_managed_waf: bool = True,
    include_api_rate_limit: bool = True,
    rate_limit_period_seconds: int = 60,
    rate_limit_mitigation_timeout_seconds: int | None = None,
) -> list[str]:
    operations: list[str] = []
    for phase, desired_ruleset in build_edge_ruleset_plan(
        hostname,
        include_managed_waf=include_managed_waf,
        include_api_rate_limit=include_api_rate_limit,
        rate_limit_period_seconds=rate_limit_period_seconds,
        rate_limit_mitigation_timeout_seconds=rate_limit_mitigation_timeout_seconds,
    ).items():
        existing = client.get_phase_entrypoint(zone_id, phase)
        rules = merge_rules(existing, desired_ruleset)
        if existing and existing.get("id"):
            client.update_ruleset(zone_id, str(existing["id"]), rules)
            operations.append(f"updated {phase} entrypoint with {len(desired_ruleset['rules'])} managed rules")
        else:
            payload = dict(desired_ruleset)
            payload["rules"] = rules
            client.create_ruleset(zone_id, payload)
            operations.append(f"created {phase} entrypoint with {len(desired_ruleset['rules'])} managed rules")
    return operations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render or apply Bitcoin Risk Brief Cloudflare edge rules.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Print the desired Cloudflare edge rules JSON.")
    render_parser.add_argument("--hostname", required=True, help="Public hostname, for example risk.example.com")
    render_parser.add_argument(
        "--skip-managed-waf",
        action="store_true",
        help="Do not render the Cloudflare Managed Ruleset entrypoint. Use this when the zone plan is not entitled to execute it.",
    )
    render_parser.add_argument(
        "--waitlist-rate-limit-only",
        action="store_true",
        help="Render only the waitlist rate-limit rule. Use this when the zone plan allows only one rate-limit rule.",
    )
    render_parser.add_argument(
        "--rate-limit-period",
        type=int,
        default=60,
        help="Cloudflare rate-limit period in seconds. Some plans only allow 10.",
    )
    render_parser.add_argument(
        "--rate-limit-mitigation-timeout",
        type=int,
        default=None,
        help="Cloudflare rate-limit mitigation timeout in seconds. Some plans only allow 10.",
    )

    apply_parser = subparsers.add_parser("apply", help="Apply the desired rules through the Cloudflare Rulesets API.")
    apply_parser.add_argument("--hostname", required=True, help="Public hostname, for example risk.example.com")
    apply_parser.add_argument("--zone-id", required=True, help="Cloudflare zone ID")
    apply_parser.add_argument(
        "--skip-managed-waf",
        action="store_true",
        help="Do not apply the Cloudflare Managed Ruleset entrypoint. Use this when the zone plan is not entitled to execute it.",
    )
    apply_parser.add_argument(
        "--waitlist-rate-limit-only",
        action="store_true",
        help="Apply only the waitlist rate-limit rule. Use this when the zone plan allows only one rate-limit rule.",
    )
    apply_parser.add_argument(
        "--rate-limit-period",
        type=int,
        default=60,
        help="Cloudflare rate-limit period in seconds. Some plans only allow 10.",
    )
    apply_parser.add_argument(
        "--rate-limit-mitigation-timeout",
        type=int,
        default=None,
        help="Cloudflare rate-limit mitigation timeout in seconds. Some plans only allow 10.",
    )
    apply_parser.add_argument(
        "--api-token",
        default=os.getenv("CLOUDFLARE_API_TOKEN"),
        help="Cloudflare API token; defaults to CLOUDFLARE_API_TOKEN",
    )

    args = parser.parse_args(argv)
    if args.command == "render":
        print(
            render_edge_plan(
                args.hostname,
                include_managed_waf=not args.skip_managed_waf,
                include_api_rate_limit=not args.waitlist_rate_limit_only,
                rate_limit_period_seconds=args.rate_limit_period,
                rate_limit_mitigation_timeout_seconds=args.rate_limit_mitigation_timeout,
            )
        )
        return 0

    if not args.api_token:
        print("CLOUDFLARE_API_TOKEN or --api-token is required for apply", file=sys.stderr)
        return 2

    client = CloudflareApiClient(args.api_token)
    for operation in apply_edge_plan(
        args.zone_id,
        args.hostname,
        client,
        include_managed_waf=not args.skip_managed_waf,
        include_api_rate_limit=not args.waitlist_rate_limit_only,
        rate_limit_period_seconds=args.rate_limit_period,
        rate_limit_mitigation_timeout_seconds=args.rate_limit_mitigation_timeout,
    ):
        print(operation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
