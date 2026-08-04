#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kit_dir="$(cd "${script_dir}/.." && pwd)"
usb_root="$(cd "${kit_dir}/.." && pwd)"
fragment="${TURNSTILE_FRAGMENT:-${usb_root}/bitcoin-risk-brief-turnstile.env}"
env_file="${PROJECT_DEST}/.env"
validator="${script_dir}/turnstile-env-preflight.py"
current_user="$(id -un)"

run_as_app() {
  if [[ "${current_user}" == "${APP_USER}" ]]; then
    "$@"
  elif [[ "${EUID}" -eq 0 ]]; then
    runuser -u "${APP_USER}" -- "$@"
  else
    sudo -u "${APP_USER}" "$@"
  fi
}

if [[ "${current_user}" != "${APP_USER}" && "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

if ! id "${APP_USER}" >/dev/null 2>&1; then
  echo "User ${APP_USER} does not exist. Run 01-bootstrap-host.sh first." >&2
  exit 1
fi
if [[ ! -f "${env_file}" ]]; then
  echo "Production environment file not found: ${env_file}" >&2
  exit 1
fi
if [[ ! -f "${fragment}" ]]; then
  echo "Turnstile environment fragment not found: ${fragment}" >&2
  exit 1
fi
if [[ ! -f "${validator}" ]]; then
  echo "Turnstile validator not found: ${validator}" >&2
  exit 1
fi
if ! python3 "${validator}" --env-file "${fragment}"; then
  echo "Turnstile fragment validation failed." >&2
  exit 1
fi

run_as_app bash -c '
set -euo pipefail
env_file="$1"
fragment="$2"
validator="$3"
tmp_file="$(mktemp "${env_file}.turnstile.XXXXXX")"
cleanup() { rm -f "${tmp_file}"; }
trap cleanup EXIT

awk '\''!/^[[:space:]]*(export[[:space:]]+)?(VITE_TURNSTILE_SITE_KEY|TURNSTILE_SECRET|TURNSTILE_HOSTNAMES)[[:space:]]*=/'\'' \
  "${env_file}" > "${tmp_file}"
cat "${fragment}" >> "${tmp_file}"
python3 "${validator}" --env-file "${tmp_file}"
chmod 600 "${tmp_file}"
mv "${tmp_file}" "${env_file}"
trap - EXIT
' _ "${env_file}" "${fragment}" "${validator}"

printf 'Turnstile configuration installed in %s as %s.\n' "${env_file}" "${APP_USER}"
