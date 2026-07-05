#!/usr/bin/env bash
set -euo pipefail

base_url="${PUBLIC_BASE_URL:-http://localhost:3001}"
base_url="${base_url%/}"

paths=(
  "/api/readiness"
  "/api/risk/latest"
  "/api/risk/history?limit=2000"
  "/api/risk/levels"
  "/api/brief/latest"
)

for path in "${paths[@]}"; do
  curl -fsS -o /dev/null "${base_url}${path}"
  echo "warmed ${base_url}${path}"
done
