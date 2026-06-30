#!/usr/bin/env bash
set -uo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"
SERVICE_NAME="${SERVICE_NAME:-bitcoin-risk-brief}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
REPORT_FILE="${REPORT_FILE:-/tmp/bitcoin-risk-debug-$(date -u +%Y%m%dT%H%M%SZ).log}"

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

app_uid() {
  id -u "${APP_USER}" 2>/dev/null
}

run_user_systemctl() {
  local uid
  uid="$(app_uid)" || return 1
  run_as_app env \
    HOME="/home/${APP_USER}" \
    XDG_RUNTIME_DIR="/run/user/${uid}" \
    systemctl --user "$@"
}

section() {
  printf '\n### %s\n' "$*"
}

run_check() {
  printf '\n$ %s\n' "$*"
  "$@"
  local status=$?
  printf '[exit %s]\n' "${status}"
  return 0
}

run_shell() {
  printf '\n$ %s\n' "$*"
  bash -lc "$*"
  local status=$?
  printf '[exit %s]\n' "${status}"
  return 0
}

mask_secret_stream() {
  sed -E \
    -e '/^(DB_PASSWORD|DATABASE_URL|POSTGRES_PASSWORD|COINMARKETCAP_API_KEY|CLOUDFLARE_API_TOKEN|CLOUDFLARE_TUNNEL_TOKEN|CLOUDFLARE_ZONE_ID):/s/:.*/: <masked>/' \
    -e '/^(DB_PASSWORD|DATABASE_URL|POSTGRES_PASSWORD|COINMARKETCAP_API_KEY|CLOUDFLARE_API_TOKEN|CLOUDFLARE_TUNNEL_TOKEN|CLOUDFLARE_ZONE_ID)=/s/=.*/=<masked>/' \
    -e '/(TOKEN|SECRET|PASSWORD|API_KEY)(:|=)/s/(:|=).*/\1 <masked>/I' \
    -e 's#postgres://postgres:[^@[:space:]]+@#postgres://postgres:<masked>@#g' \
    -e 's#postgresql://postgres:[^@[:space:]]+@#postgresql://postgres:<masked>@#g'
}

run_masked_shell() {
  printf '\n$ %s\n' "$*"
  bash -lc "$*" | mask_secret_stream
  local status=${PIPESTATUS[0]}
  printf '[exit %s]\n' "${status}"
  return 0
}

mask_env_file() {
  local env_file="$1"

  if ! as_root test -f "${env_file}"; then
    printf 'env file not found: %s\n' "${env_file}"
    return 0
  fi

  as_root sed -E \
    -e '/^(DB_PASSWORD|DATABASE_URL|COINMARKETCAP_API_KEY|CLOUDFLARE_API_TOKEN|CLOUDFLARE_TUNNEL_TOKEN|CLOUDFLARE_ZONE_ID)=/s/=.*/=<masked>/' \
    -e '/(TOKEN|SECRET|PASSWORD|API_KEY)=/s/=.*/=<masked>/I' \
    "${env_file}"
}

{
  section "Debug Report Metadata"
  printf 'created_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'hostname=%s\n' "$(hostname 2>/dev/null || true)"
  printf 'kernel=%s\n' "$(uname -a 2>/dev/null || true)"
  printf 'script_path=%s\n' "${BASH_SOURCE[0]}"
  printf 'report_file=%s\n' "${REPORT_FILE}"
  printf 'app_user=%s\n' "${APP_USER}"
  printf 'project_dest=%s\n' "${PROJECT_DEST}"
  printf 'service_name=%s\n' "${SERVICE_NAME}"

  section "Operating System"
  run_check cat /etc/os-release
  run_check timedatectl

  section "Current User And Environment"
  run_check id
  run_check whoami
  run_masked_shell "env | sort"

  section "apps User"
  run_check id "${APP_USER}"
  run_check getent passwd "${APP_USER}"
  run_shell "grep '^${APP_USER}:' /etc/subuid /etc/subgid"
  run_check loginctl user-status "${APP_USER}"

  section "Project Paths"
  run_check ls -ld /srv /srv/projects "${PROJECT_DEST}"
  run_check ls -la "${PROJECT_DEST}"
  run_check ls -la "${PROJECT_DEST}/scripts"
  run_check test -f "${PROJECT_DEST}/podman-compose.yml"
  run_check test -f "${PROJECT_DEST}/.env"

  section "Masked Project Environment"
  mask_env_file "${PROJECT_DEST}/.env"

  section "Kit Script Versions When Running From USB"
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
  kit_dir="$(cd "${script_dir}/.." 2>/dev/null && pwd)"
  printf 'script_dir=%s\n' "${script_dir}"
  printf 'kit_dir=%s\n' "${kit_dir}"
  run_check ls -la "${kit_dir}/scripts"
  run_shell "grep -n 'as_root test -d\\|systemctl start \"user@\\|HOME=' '${kit_dir}/scripts/04-enable-bitcoin-risk-service.sh' || true"

  section "systemd User Manager"
  if app_uid_value="$(app_uid)"; then
    printf 'apps_uid=%s\n' "${app_uid_value}"
    run_check ls -ld "/run/user/${app_uid_value}"
    run_check systemctl status "user@${app_uid_value}.service" --no-pager
  else
    printf 'apps user is missing; cannot check user manager\n'
  fi

  section "User Service Files"
  run_check ls -la "/home/${APP_USER}/.config/systemd/user"
  run_check cat "/home/${APP_USER}/.config/systemd/user/${SERVICE_NAME}.service"

  section "User Service Status"
  run_user_systemctl daemon-reload
  printf '[exit %s]\n' "$?"
  run_user_systemctl list-unit-files
  printf '[exit %s]\n' "$?"
  run_user_systemctl list-unit-files | grep -F "${SERVICE_NAME}" || true
  printf '[exit %s]\n' "$?"
  run_user_systemctl status "${SERVICE_NAME}.service" --no-pager
  printf '[exit %s]\n' "$?"
  run_as_app env HOME="/home/${APP_USER}" XDG_RUNTIME_DIR="/run/user/$(app_uid)" journalctl --user -u "${SERVICE_NAME}.service" -n 200 --no-pager
  printf '[exit %s]\n' "$?"

  section "System Service Status"
  run_check systemctl status "${SERVICE_NAME}.service" --no-pager
  run_check journalctl -u "${SERVICE_NAME}.service" -n 200 --no-pager

  section "Podman And Compose"
  run_check command -v podman
  run_check command -v podman-compose
  run_as_app podman info | mask_secret_stream
  printf '[exit %s]\n' "$?"
  run_as_app bash -lc "cd '${PROJECT_DEST}' && podman-compose config" | mask_secret_stream
  printf '[exit %s]\n' "$?"
  run_as_app bash -lc "cd '${PROJECT_DEST}' && podman-compose ps"
  printf '[exit %s]\n' "$?"
  run_as_app bash -lc "cd '${PROJECT_DEST}' && podman ps -a"
  printf '[exit %s]\n' "$?"
  run_as_app bash -lc "cd '${PROJECT_DEST}' && podman-compose logs --tail=120" | mask_secret_stream
  printf '[exit %s]\n' "$?"

  section "Network And Health"
  run_check ss -tulpn
  run_check curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/api/health"
  run_check curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/api/readiness"

  section "Firewall And Cloudflared"
  run_check ufw status verbose
  run_check command -v cloudflared
  run_check cloudflared --version
  run_check systemctl status cloudflared --no-pager

  section "Disk And Resources"
  run_check df -h
  run_check free -h
  run_check podman system df
} >"${REPORT_FILE}" 2>&1

printf 'Debug report written to: %s\n' "${REPORT_FILE}"
printf 'Show it with:\n'
printf '  sudo sed -n '\''1,260p'\'' %q\n' "${REPORT_FILE}"
