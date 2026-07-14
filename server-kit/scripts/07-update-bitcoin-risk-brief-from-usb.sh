#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"
SERVICE_NAME="${SERVICE_NAME:-bitcoin-risk-brief}"
PUBLIC_URL="${PUBLIC_URL:-${1:-}}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kit_dir="$(cd "${script_dir}/.." && pwd)"
PROJECT_SRC="${PROJECT_SRC:-${kit_dir}/project/${PROJECT_NAME}}"
BACKUP_COPY_DEST="${BACKUP_COPY_DEST:-${kit_dir}/backups-from-server}"

export APP_USER PROJECT_NAME PROJECT_DEST PROJECT_SRC SERVICE_NAME PUBLIC_URL

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
  run_as_app env \
    HOME="/home/${APP_USER}" \
    XDG_RUNTIME_DIR="/run/user/${app_uid}" \
    systemctl --user "$@"
}

run_migrations() {
  log "Running database migrations"
  run_as_app bash -lc "cd '${PROJECT_DEST}' && ./scripts/manage.sh migrate"
}

verify_checksums_as_root() {
  local directory="$1"

  as_root bash -c 'cd "$1" && sha256sum -c SHA256SUMS' _ "${directory}"
}

first_matching_file_as_root() {
  local directory="$1"
  local name_pattern="$2"

  as_root find "${directory}" -maxdepth 1 -type f -name "${name_pattern}" -print -quit
}

require_backup_file() {
  local path="$1"
  local description="$2"

  if ! as_root test -s "${path}"; then
    echo "Backup ${description} not found or empty: ${path}" >&2
    exit 1
  fi
}

if ! id "${APP_USER}" >/dev/null 2>&1; then
  echo "User ${APP_USER} does not exist. Run 01-bootstrap-host.sh first." >&2
  exit 1
fi

if ! as_root test -d "${PROJECT_DEST}"; then
  echo "Project directory not found for update: ${PROJECT_DEST}" >&2
  exit 1
fi

project_dest_real="$(as_root realpath "${PROJECT_DEST}")"
case "${project_dest_real}" in
  /srv/projects/*) ;;
  *)
    echo "Refusing to update outside /srv/projects/: ${PROJECT_DEST} resolves to ${project_dest_real}" >&2
    exit 1
    ;;
esac
PROJECT_DEST="${project_dest_real}"
export PROJECT_DEST

if ! as_root test -f "${PROJECT_DEST}/.env"; then
  echo "Existing production environment file not found: ${PROJECT_DEST}/.env" >&2
  exit 1
fi

if [[ ! -f "${PROJECT_SRC}/podman-compose.yml" ]]; then
  echo "Project source does not look like bitcoin-risk-brief: ${PROJECT_SRC}" >&2
  exit 1
fi
if [[ ! -f "${PROJECT_SRC}/scripts/backup.sh" ]]; then
  echo "Project source backup script not found: ${PROJECT_SRC}/scripts/backup.sh" >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_log="/tmp/bitcoin-risk-update-backup-${timestamp}.log"

log "Creating backup before deploying update"
run_as_app bash -c 'cd "$1" && bash "$2"' _ "${PROJECT_DEST}" "${PROJECT_SRC}/scripts/backup.sh" | tee "${backup_log}"

backup_path_from_log="$(awk '/^Backup complete:/ {print $3}' "${backup_log}" | tail -n 1)"
if [[ -z "${backup_path_from_log}" ]]; then
  echo "Could not parse backup path from ${backup_log}" >&2
  exit 1
fi

if [[ "${backup_path_from_log}" == /* ]]; then
  backup_path="${backup_path_from_log}"
else
  backup_path="${PROJECT_DEST}/${backup_path_from_log#./}"
fi

if ! as_root test -d "${backup_path}"; then
  echo "Parsed backup directory does not exist: ${backup_path}" >&2
  exit 1
fi

postgres_dump="$(first_matching_file_as_root "${backup_path}" "postgres_*.dump")"
btc_csv="$(first_matching_file_as_root "${backup_path}" "btc_usd_daily_*.csv")"

if [[ -z "${postgres_dump}" ]]; then
  echo "Backup PostgreSQL dump not found in ${backup_path}" >&2
  exit 1
fi
if [[ -z "${btc_csv}" ]]; then
  echo "Backup BTC CSV not found in ${backup_path}" >&2
  exit 1
fi

require_backup_file "${postgres_dump}" "PostgreSQL dump"
require_backup_file "${btc_csv}" "BTC CSV"
require_backup_file "${backup_path}/manifest.txt" "manifest"
require_backup_file "${backup_path}/SHA256SUMS" "checksum file"

log "Verifying backup checksums"
verify_checksums_as_root "${backup_path}"

log "Copying verified backup to ${BACKUP_COPY_DEST}"
as_root mkdir -p "${BACKUP_COPY_DEST}"
as_root rsync -a --no-owner --no-group --no-perms "${backup_path}" "${BACKUP_COPY_DEST}/"
backup_copy_path="${BACKUP_COPY_DEST%/}/$(basename "${backup_path}")"

log "Verifying copied backup checksums"
verify_checksums_as_root "${backup_copy_path}"

log "Deploying project snapshot from USB"
bash "${script_dir}/03-deploy-bitcoin-risk-brief.sh"

log "Enabling and restarting service"
bash "${script_dir}/04-enable-bitcoin-risk-service.sh"
run_user_systemctl restart "${SERVICE_NAME}.service"

run_migrations

log "Running health checks"
if [[ -n "${PUBLIC_URL}" ]]; then
  bash "${script_dir}/05-health-check.sh" "${PUBLIC_URL}"
else
  bash "${script_dir}/05-health-check.sh"
fi

log "USB update complete"
