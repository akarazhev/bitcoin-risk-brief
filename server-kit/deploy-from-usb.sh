#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
SERVICE_NAME="${SERVICE_NAME:-bitcoin-risk-brief}"
PUBLIC_URL="${PUBLIC_URL:-}"
WITH_BACKUP=false

usage() {
  cat <<'EOF'
Usage: bash deploy-from-usb.sh [--with-backup] [PUBLIC_URL]

Default mode verifies the USB kit, deploys the project snapshot, restarts the
service, and runs health checks. It preserves the existing production .env and
database volume. Use --with-backup only when you intentionally want the slower
backup-gated update flow before deploying.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-backup)
      WITH_BACKUP=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    http://*|https://*)
      PUBLIC_URL="$1"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export APP_USER PROJECT_NAME SERVICE_NAME PUBLIC_URL

log() {
  printf '\n==> %s\n' "$*"
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
  run_as_app env \
    HOME="/home/${APP_USER}" \
    XDG_RUNTIME_DIR="/run/user/${app_uid}" \
    systemctl --user "$@"
}

verify_kit_checksums() {
  if [[ ! -f "${script_dir}/SHA256SUMS" ]]; then
    echo "USB kit checksum file not found: ${script_dir}/SHA256SUMS" >&2
    exit 1
  fi
  if ! command -v sha256sum >/dev/null 2>&1; then
    echo "sha256sum is required on the server." >&2
    exit 1
  fi

  log "Verifying USB kit checksums"
  (
    cd "${script_dir}"
    sha256sum -c SHA256SUMS
  )
}

require_script() {
  local relative_path="$1"
  if [[ ! -f "${script_dir}/${relative_path}" ]]; then
    echo "Required script not found: ${script_dir}/${relative_path}" >&2
    exit 1
  fi
}

derive_public_hostname() {
  if [[ -n "${PUBLIC_HOSTNAME:-}" || -z "${PUBLIC_URL}" ]]; then
    return 0
  fi

  local host
  host="${PUBLIC_URL#http://}"
  host="${host#https://}"
  host="${host%%/*}"
  host="${host%%:*}"
  if [[ -n "${host}" ]]; then
    export PUBLIC_HOSTNAME="${host}"
  fi
}

deploy_without_backup() {
  require_script "scripts/03-deploy-bitcoin-risk-brief.sh"
  require_script "scripts/04-enable-bitcoin-risk-service.sh"
  require_script "scripts/05-health-check.sh"
  derive_public_hostname

  log "Deploying project snapshot from USB"
  bash "${script_dir}/scripts/03-deploy-bitcoin-risk-brief.sh"

  log "Enabling service"
  bash "${script_dir}/scripts/04-enable-bitcoin-risk-service.sh"

  log "Restarting service"
  run_user_systemctl restart "${SERVICE_NAME}.service"

  log "Running health checks"
  if [[ -n "${PUBLIC_URL}" ]]; then
    bash "${script_dir}/scripts/05-health-check.sh" "${PUBLIC_URL}"
  else
    bash "${script_dir}/scripts/05-health-check.sh"
  fi
}

deploy_with_backup() {
  require_script "scripts/07-update-bitcoin-risk-brief-from-usb.sh"

  log "Running backup-gated update"
  if [[ -n "${PUBLIC_URL}" ]]; then
    PUBLIC_URL="${PUBLIC_URL}" bash "${script_dir}/scripts/07-update-bitcoin-risk-brief-from-usb.sh"
  else
    bash "${script_dir}/scripts/07-update-bitcoin-risk-brief-from-usb.sh"
  fi
}

verify_kit_checksums

if [[ "${WITH_BACKUP}" == "true" ]]; then
  deploy_with_backup
else
  deploy_without_backup
fi

log "USB deploy complete"
