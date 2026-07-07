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
  BACKUP_DIR               Backup output directory. Default: ./backups
  BACKUP_RETENTION_DAYS    Retention window for timestamped backup dirs. Default: 30
  BACKUP_DUMP_TIMEOUT_SECONDS
                           Hard timeout for pg_dump. Default: 300
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
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_DUMP_TIMEOUT_SECONDS="${BACKUP_DUMP_TIMEOUT_SECONDS:-300}"
BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS="${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS:-10}"
BACKUP_DUMP_LOCK_WAIT_TIMEOUT="${BACKUP_DUMP_LOCK_WAIT_TIMEOUT:-30s}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-bitcoin_risk_brief}"
CSV_SOURCE="${CSV_SOURCE:-collector/btc-csv/btc_usd_daily.csv}"

if ! [[ "${BACKUP_RETENTION_DAYS}" =~ ^[0-9]+$ ]]; then
  echo "BACKUP_RETENTION_DAYS must be a non-negative integer" >&2
  exit 2
fi
if ! [[ "${BACKUP_DUMP_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BACKUP_DUMP_TIMEOUT_SECONDS must be a positive integer" >&2
  exit 2
fi
if ! [[ "${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS must be a positive integer" >&2
  exit 2
fi

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

create_postgres_dump() {
  timeout_command "${BACKUP_DUMP_TIMEOUT_SECONDS}s" \
    "${COMPOSE}" -f "${COMPOSE_FILE}" exec -T timescaledb \
    sh -c 'PGCONNECT_TIMEOUT="$1" PGPASSWORD="${POSTGRES_PASSWORD:-}" exec pg_dump --no-password --lock-wait-timeout="$2" -Fc --no-owner --no-privileges -h 127.0.0.1 -U "$3" -d "$4"' \
    _ "${BACKUP_DUMP_CONNECT_TIMEOUT_SECONDS}" "${BACKUP_DUMP_LOCK_WAIT_TIMEOUT}" "${POSTGRES_USER}" "${POSTGRES_DB}"
}

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "Would create backup directory: ${TARGET_DIR}"
  echo "Would create a custom-format dump of ${POSTGRES_DB} from service timescaledb using ${COMPOSE} -f ${COMPOSE_FILE}"
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
    echo "Check podman-compose ps/logs, database locks, and disk pressure, then retry or increase BACKUP_DUMP_TIMEOUT_SECONDS." >&2
  else
    echo "PostgreSQL dump failed with exit code ${dump_status}." >&2
    echo "The dump runs non-interactively with --no-password; verify the timescaledb container has POSTGRES_PASSWORD and is healthy." >&2
  fi
  exit "${dump_status}"
fi

echo "Copying canonical CSV: ${CSV_FILE}"
cp "${CSV_SOURCE}" "${CSV_FILE}"

{
  echo "created_at_utc=${TIMESTAMP}"
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
