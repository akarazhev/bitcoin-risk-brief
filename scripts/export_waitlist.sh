#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/export_waitlist.sh [--recent N]
       scripts/export_waitlist.sh --include-contacts --output /secure/path/waitlist.csv

Shows a local operator report for waitlist leads stored in PostgreSQL.

Default mode prints aggregate counts and recent leads with masked contacts.
Full contact export is PII and requires both --include-contacts and --output.

Environment variables:
  COMPOSE          Compose command binary. Default: podman-compose
  COMPOSE_FILE     Compose file. Default: podman-compose.yml
  POSTGRES_USER    PostgreSQL user. Default: postgres
  POSTGRES_DB      PostgreSQL database. Default: bitcoin_risk_brief
EOF
}

COMPOSE="${COMPOSE:-podman-compose}"
COMPOSE_FILE="${COMPOSE_FILE:-podman-compose.yml}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-bitcoin_risk_brief}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
RECENT_LIMIT=20
INCLUDE_CONTACTS=false
OUTPUT_PATH=""

die_usage() {
  echo "$*" >&2
  usage >&2
  exit 2
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --recent)
      if [[ -z "${2:-}" ]]; then
        die_usage "--recent requires a positive integer"
      fi
      RECENT_LIMIT="$2"
      shift 2
      ;;
    --include-contacts)
      INCLUDE_CONTACTS=true
      shift
      ;;
    --output)
      if [[ -z "${2:-}" ]]; then
        die_usage "--output requires a file path"
      fi
      OUTPUT_PATH="$2"
      shift 2
      ;;
    *)
      die_usage "Unknown argument: $1"
      ;;
  esac
done

if ! [[ "${RECENT_LIMIT}" =~ ^[1-9][0-9]*$ ]]; then
  die_usage "--recent requires a positive integer"
fi

if [[ "${INCLUDE_CONTACTS}" == "true" && -z "${OUTPUT_PATH}" ]]; then
  die_usage "--output is required when --include-contacts is used"
fi

if [[ "${INCLUDE_CONTACTS}" != "true" && -n "${OUTPUT_PATH}" ]]; then
  die_usage "--output is only supported with --include-contacts"
fi

run_psql() {
  "${COMPOSE}" -f "${COMPOSE_FILE}" exec -T timescaledb \
    psql -X -v ON_ERROR_STOP=1 -v "recent_limit=${RECENT_LIMIT}" \
    -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" "$@"
}

if [[ "${INCLUDE_CONTACTS}" == "true" ]]; then
  output_dir="$(dirname "${OUTPUT_PATH}")"
  if [[ ! -d "${output_dir}" ]]; then
    echo "Output directory does not exist: ${output_dir}" >&2
    exit 2
  fi
  output_dir="$(cd "${output_dir}" && pwd -P)"
  output_name="$(basename "${OUTPUT_PATH}")"
  output_path="${output_dir}/${output_name}"
  case "${output_path}" in
    "${REPO_ROOT}"|"${REPO_ROOT}"/*)
      echo "Full waitlist exports contain PII; choose an output path outside the repository checkout." >&2
      exit 2
      ;;
  esac
  if [[ -e "${output_path}" ]]; then
    echo "Output file already exists: ${output_path}" >&2
    exit 2
  fi

  umask 077
  temp_path="$(mktemp "${output_path}.tmp.XXXXXX")"
  cleanup() {
    rm -f "${temp_path}"
  }
  trap cleanup EXIT

  run_psql -q <<'SQL' > "${temp_path}"
COPY (
  SELECT
    id::text,
    contact,
    normalized_contact,
    contact_type,
    locale,
    source,
    status,
    created_at,
    updated_at
  FROM waitlist_leads
  ORDER BY created_at DESC, id DESC
) TO STDOUT WITH CSV HEADER;
SQL

  chmod 600 "${temp_path}"
  if ! ln "${temp_path}" "${output_path}"; then
    echo "Output file already exists or could not be created safely: ${output_path}" >&2
    exit 2
  fi
  rm -f "${temp_path}"
  trap - EXIT
  echo "Exported waitlist contacts to ${output_path}" >&2
  exit 0
fi

run_psql <<'SQL'
\pset pager off
\pset null '(null)'

\echo Waitlist totals by status
SELECT status, count(*) AS leads
FROM waitlist_leads
GROUP BY status
ORDER BY status;

\echo
\echo Waitlist totals by contact type
SELECT contact_type, count(*) AS leads
FROM waitlist_leads
GROUP BY contact_type
ORDER BY contact_type;

\echo
\echo Waitlist totals by locale and source
SELECT locale, source, count(*) AS leads
FROM waitlist_leads
GROUP BY locale, source
ORDER BY leads DESC, locale, source;

\echo
\echo Recent waitlist leads with masked contacts
SELECT
  id::text,
  contact_type,
  locale,
  source,
  status,
  CASE
    WHEN contact_type = 'email' THEN left(contact, 1) || '***@***'
    WHEN contact_type = 'telegram' THEN left(contact, 2) || '***'
    ELSE '<masked>'
  END AS masked_contact,
  created_at,
  updated_at
FROM waitlist_leads
ORDER BY created_at DESC, id DESC
LIMIT :'recent_limit';
SQL
