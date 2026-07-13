#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/apply-cloudflare-cache-rules.sh [--purge] [--hostname HOSTNAME] [--zone-id ZONE_ID]

Applies only the Bitcoin Risk Brief Cloudflare cache settings rules:
- bypass POST /api/waitlist
- bypass GET /api/readiness
- cache GET product API reads that remain cacheable

Environment:
  CLOUDFLARE_API_TOKEN  Required. Cloudflare API token.
  CLOUDFLARE_ZONE_ID    Required unless --zone-id is provided.
  CLOUDFLARE_HOSTNAME   Optional. Defaults to bitcoinriskbrief.minihub.app.

Options:
  --purge              Purge https://<hostname>/api/readiness after applying rules.
  --hostname HOSTNAME  Public hostname. Overrides CLOUDFLARE_HOSTNAME.
  --zone-id ZONE_ID    Cloudflare zone ID. Overrides CLOUDFLARE_ZONE_ID.
  -h, --help           Show this help.
USAGE
}

hostname="${CLOUDFLARE_HOSTNAME:-bitcoinriskbrief.minihub.app}"
zone_id="${CLOUDFLARE_ZONE_ID:-}"
purge=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge)
      purge=true
      shift
      ;;
    --hostname)
      if [[ -z "${2:-}" ]]; then
        echo "--hostname requires a value" >&2
        exit 2
      fi
      hostname="$2"
      shift 2
      ;;
    --zone-id)
      if [[ -z "${2:-}" ]]; then
        echo "--zone-id requires a value" >&2
        exit 2
      fi
      zone_id="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "CLOUDFLARE_API_TOKEN is required" >&2
  exit 2
fi

if [[ -z "${zone_id}" ]]; then
  echo "CLOUDFLARE_ZONE_ID or --zone-id is required" >&2
  exit 2
fi

args=(
  scripts/cloudflare_edge_rules.py
  apply-cache
  --hostname "${hostname}"
  --zone-id "${zone_id}"
)

if [[ "${purge}" == true ]]; then
  args+=(--purge)
fi

python3 "${args[@]}"
