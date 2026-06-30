#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"
SERVICE_NAME="${SERVICE_NAME:-bitcoin-risk-brief}"
PUBLIC_URL="${PUBLIC_URL:-${1:-}}"

log() {
  printf '\n==> %s\n' "$*"
}

as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

run_as_app() {
  if [[ "${EUID}" -eq 0 ]]; then
    runuser -u "${APP_USER}" -- "$@"
  else
    sudo -u "${APP_USER}" "$@"
  fi
}

run_user_systemctl() {
  local app_uid
  app_uid="$(id -u "${APP_USER}")"
  run_as_app env XDG_RUNTIME_DIR="/run/user/${app_uid}" systemctl --user "$@"
}

env_file="${PROJECT_DEST}/.env"
frontend_port="3001"
if [[ -f "${env_file}" ]]; then
  configured_port="$(grep -E '^FRONTEND_PORT=' "${env_file}" | tail -n 1 | cut -d= -f2- | tr -d '"' || true)"
  if [[ -n "${configured_port}" ]]; then
    frontend_port="${configured_port}"
  fi
fi

local_base="http://127.0.0.1:${frontend_port}"

log "Checking local application endpoints"
curl -fsS "${local_base}/api/health" >/dev/null
printf 'OK %s/api/health\n' "${local_base}"

curl -fsS "${local_base}/api/readiness" >/dev/null
printf 'OK %s/api/readiness\n' "${local_base}"

log "Checking systemd user service"
run_user_systemctl status "${SERVICE_NAME}.service" --no-pager

log "Checking Podman containers"
run_as_app bash -lc "cd '${PROJECT_DEST}' && podman-compose ps"

log "Checking listening sockets"
ss -tulpn | grep -E "127\\.0\\.0\\.1:${frontend_port}\\b" || {
  echo "Expected frontend listener on 127.0.0.1:${frontend_port} was not found." >&2
  exit 1
}

if [[ -n "${PUBLIC_URL}" ]]; then
  public_base="${PUBLIC_URL%/}"
  log "Checking public endpoints through ${public_base}"
  curl -fsS "${public_base}/api/health" >/dev/null
  printf 'OK %s/api/health\n' "${public_base}"
  curl -fsS "${public_base}/api/readiness" >/dev/null
  printf 'OK %s/api/readiness\n' "${public_base}"
fi

log "Health check complete"
