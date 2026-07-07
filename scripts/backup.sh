#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/backup.sh [--dry-run]

Creates a timestamped backup containing:
  - compressed PostgreSQL custom-format dump from the running timescaledb service;
  - canonical BTC CSV source file;
  - checksum file and manifest.

Environment variables:
  COMPOSE                  Compose command. Default: podman-compose
  COMPOSE_FILE             Compose file. Default: podman-compose.yml
  BACKUP_DUMP_METHOD       Dump runner: podman or compose. Default: podman
  PODMAN                   Podman command. Default: podman
  POSTGRES_CONTAINER       Explicit TimescaleDB container id/name. Default: auto-detect
  BACKUP_DIR               Backup output directory. Default: ./backups
  BACKUP_RETENTION_DAYS    Retention window for timestamped backup dirs. Default: 30
  BACKUP_DUMP_TIMEOUT_SECONDS
                           Hard timeout for pg_dump. Default: 300
  BACKUP_PODMAN_PS_TIMEOUT_SECONDS
                           Hard timeout for finding the TimescaleDB container. Default: 20
  BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS
                           PostgreSQL connection timeout for pg_dump. Default: 10
  BACKUP_DUMP_LOCK_WAIT_TIMEOUT
                           Maximum pg_dump table-lock wait. Default: 30s
  POSTGRES_USER            PostgreSQL user. Default: postgres
  POSTGRES_DB              PostgreSQL database. Default: bitcoin_risk_brief
  CSV_SOURCE               Canonical CSV path. Default: collector/btc-csv/btc_usd_daily.csv
EOF
}

DRY_RUN=false
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
elif [[ -n "${1:-}" ]]; then
  usage >&2
  exit 2
fi

COMPOSE="${COMPOSE:-podman-compose}"
COMPOSE_FILE="${COMPOSE_FILE:-podman-compose.yml}"
BACKUP_DUMP_METHOD="${BACKUP_DUMP_METHOD:-podman}"
PODMAN="${PODMAN:-podman}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_DUMP_TIMEOUT_SECONDS="${BACKUP_DUMP_TIMEOUT_SECONDS:-300}"
BACKUP_PODMAN_PS_TIMEOUT_SECONDS="${BACKUP_PODMAN_PS_TIMEOUT_SECONDS:-20}"
BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS="${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS:-10}"
BACKUP_DUMP_LOCK_WAIT_TIMEOUT="${BACKUP_DUMP_LOCK_WAIT_TIMEOUT:-30s}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-bitcoin_risk_brief}"
CSV_SOURCE="${CSV_SOURCE:-collector/btc-csv/btc_usd_daily.csv}"

current_uid="$(id -u)"
if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "/run/user/${current_uid}" ]]; then
  export XDG_RUNTIME_DIR="/run/user/${current_uid}"
fi
if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -n "${XDG_RUNTIME_DIR:-}" && -S "${XDG_RUNTIME_DIR}/bus" ]]; then
  export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
fi

if ! [[ "${BACKUP_RETENTION_DAYS}" =~ ^[0-9]+$ ]]; then
  echo "BACKUP_RETENTION_DAYS must be a non-negative integer" >&2
  exit 2
fi
if ! [[ "${BACKUP_DUMP_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BACKUP_DUMP_TIMEOUT_SECONDS must be a positive integer" >&2
  exit 2
fi
if ! [[ "${BACKUP_PODMAN_PS_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BACKUP_PODMAN_PS_TIMEOUT_SECONDS must be a positive integer" >&2
  exit 2
fi
if ! [[ "${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS must be a positive integer" >&2
  exit 2
fi
case "${BACKUP_DUMP_METHOD}" in
  podman|compose) ;;
  *)
    echo "BACKUP_DUMP_METHOD must be podman or compose" >&2
    exit 2
    ;;
esac

case "${BACKUP_DIR}" in
  ""|"/"|".")
    echo "BACKUP_DIR must point to a dedicated backup directory" >&2
    exit 2
    ;;
esac

if [[ ! -f "${CSV_SOURCE}" ]]; then
  echo "CSV source not found: ${CSV_SOURCE}" >&2
  exit 1
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET_DIR="${BACKUP_DIR%/}/${TIMESTAMP}"
DUMP_FILE="${TARGET_DIR}/postgres_${TIMESTAMP}.dump"
CSV_FILE="${TARGET_DIR}/btc_usd_daily_${TIMESTAMP}.csv"
MANIFEST_FILE="${TARGET_DIR}/manifest.txt"
CHECKSUM_FILE="${TARGET_DIR}/SHA256SUMS"

checksum_command() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$@"
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$@"
  else
    echo "sha256sum or shasum is required" >&2
    exit 1
  fi
}

timeout_command() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$@"
  else
    echo "Warning: timeout/gtimeout not found; PostgreSQL dump hard timeout is disabled" >&2
    shift
    "$@"
  fi
}

find_timescaledb_container() {
  if [[ -n "${POSTGRES_CONTAINER}" ]]; then
    printf '%s\n' "${POSTGRES_CONTAINER}"
    return 0
  fi

  if ! command -v "${PODMAN}" >/dev/null 2>&1; then
    echo "Podman command not found: ${PODMAN}" >&2
    return 1
  fi

  local containers
  local status
  containers="$(timeout_command "${BACKUP_PODMAN_PS_TIMEOUT_SECONDS}s" "${PODMAN}" ps --format '{{.ID}}\t{{.Names}}\t{{.Image}}')"
  status=$?
  if [[ "${status}" -ne 0 ]]; then
    echo "Could not list Podman containers with ${PODMAN} ps; exit code ${status}." >&2
    echo "If rootless Podman is unhealthy, run the backup as the app user with HOME and XDG_RUNTIME_DIR set." >&2
    return "${status}"
  fi

  local container_id
  container_id="$(
    printf '%s\n' "${containers}" \
      | awk 'tolower($0) ~ /(^|[[:space:]_-])timescaledb([[:space:]_-]|$)|timescale\/timescaledb/ {print $1; exit}'
  )"
  if [[ -z "${container_id}" ]]; then
    echo "Running TimescaleDB container not found. Set POSTGRES_CONTAINER to the container id/name if auto-detection fails." >&2
    return 1
  fi

  printf '%s\n' "${container_id}"
}

create_postgres_dump_with_podman() {
  local container_id
  container_id="$(find_timescaledb_container)" || return $?

  timeout_command "${BACKUP_DUMP_TIMEOUT_SECONDS}s" \
    "${PODMAN}" exec "${container_id}" \
    sh -c 'PGCONNECT_TIMEOUT="$1" PGPASSWORD="${POSTGRES_PASSWORD:-}" exec pg_dump --no-password --lock-wait-timeout="$2" -Fc --no-owner --no-privileges -h 127.0.0.1 -U "$3" -d "$4"' \
    _ "${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS}" "${BACKUP_DUMP_LOCK_WAIT_TIMEOUT}" "${POSTGRES_USER}" "${POSTGRES_DB}"
}

create_postgres_dump_with_compose() {
  timeout_command "${BACKUP_DUMP_TIMEOUT_SECONDS}s" \
    "${COMPOSE}" -f "${COMPOSE_FILE}" exec -T timescaledb \
    sh -c 'PGCONNECT_TIMEOUT="$1" PGPASSWORD="${POSTGRES_PASSWORD:-}" exec pg_dump --no-password --lock-wait-timeout="$2" -Fc --no-owner --no-privileges -h 127.0.0.1 -U "$3" -d "$4"' \
    _ "${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS}" "${BACKUP_DUMP_LOCK_WAIT_TIMEOUT}" "${POSTGRES_USER}" "${POSTGRES_DB}"
}

create_postgres_dump() {
  case "${BACKUP_DUMP_METHOD}" in
    podman)
      create_postgres_dump_with_podman
      ;;
    compose)
      create_postgres_dump_with_compose
      ;;
  esac
}

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "Would create backup directory: ${TARGET_DIR}"
  if [[ "${BACKUP_DUMP_METHOD}" == "podman" ]]; then
    echo "Would create a custom-format dump of ${POSTGRES_DB} using ${PODMAN} exec against the running timescaledb container"
    echo "Would fail container discovery after ${BACKUP_PODMAN_PS_TIMEOUT_SECONDS}s"
  else
    echo "Would create a custom-format dump of ${POSTGRES_DB} from service timescaledb using ${COMPOSE} -f ${COMPOSE_FILE}"
  fi
  echo "Would fail the dump after ${BACKUP_DUMP_TIMEOUT_SECONDS}s, connect timeout ${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS}s, lock wait ${BACKUP_DUMP_LOCK_WAIT_TIMEOUT}"
  echo "Would copy ${CSV_SOURCE} to ${CSV_FILE}"
  echo "Would prune timestamped backups older than ${BACKUP_RETENTION_DAYS} days under ${BACKUP_DIR}"
  exit 0
fi

umask 077
mkdir -p "${TARGET_DIR}"
chmod 700 "${BACKUP_DIR}" "${TARGET_DIR}" 2>/dev/null || true

echo "Creating PostgreSQL custom-format dump: ${DUMP_FILE}"
set +e
create_postgres_dump > "${DUMP_FILE}"
dump_status=$?
set -e
if [[ "${dump_status}" -ne 0 ]]; then
  rm -f "${DUMP_FILE}"
  if [[ "${dump_status}" -eq 124 ]]; then
    echo "PostgreSQL dump timed out after ${BACKUP_DUMP_TIMEOUT_SECONDS}s." >&2
    echo "Check Podman health, the running TimescaleDB container, database locks, and disk pressure, then retry or increase BACKUP_DUMP_TIMEOUT_SECONDS." >&2
  else
    echo "PostgreSQL dump failed with exit code ${dump_status}." >&2
    echo "The dump runs non-interactively with --no-password; verify the TimescaleDB container has POSTGRES_PASSWORD and is healthy." >&2
  fi
  exit "${dump_status}"
fi

echo "Copying canonical CSV: ${CSV_FILE}"
cp "${CSV_SOURCE}" "${CSV_FILE}"

{
  echo "created_at_utc=${TIMESTAMP}"
  echo "backup_dump_method=${BACKUP_DUMP_METHOD}"
  echo "podman=${PODMAN}"
  echo "postgres_container=${POSTGRES_CONTAINER:-auto}"
  echo "compose=${COMPOSE}"
  echo "compose_file=${COMPOSE_FILE}"
  echo "postgres_user=${POSTGRES_USER}"
  echo "postgres_db=${POSTGRES_DB}"
  echo "csv_source=${CSV_SOURCE}"
  echo "dump_file=$(basename "${DUMP_FILE}")"
  echo "csv_file=$(basename "${CSV_FILE}")"
} > "${MANIFEST_FILE}"

(
  cd "${TARGET_DIR}"
  checksum_command "$(basename "${DUMP_FILE}")" "$(basename "${CSV_FILE}")" "$(basename "${MANIFEST_FILE}")"
) > "${CHECKSUM_FILE}"

echo "Pruning timestamped backups older than ${BACKUP_RETENTION_DAYS} days in ${BACKUP_DIR}"
find "${BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d -name '20*T*Z' -mtime +"${BACKUP_RETENTION_DAYS}" -exec rm -rf {} +

echo "Backup complete: ${TARGET_DIR}"
