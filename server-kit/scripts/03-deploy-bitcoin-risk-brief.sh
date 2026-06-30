#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"
PUBLIC_HOSTNAME="${PUBLIC_HOSTNAME:-}"

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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kit_dir="$(cd "${script_dir}/.." && pwd)"
PROJECT_SRC="${PROJECT_SRC:-${kit_dir}/project/${PROJECT_NAME}}"

case "${PROJECT_DEST}" in
  /srv/projects/*) ;;
  *)
    echo "Refusing to deploy outside /srv/projects/: ${PROJECT_DEST}" >&2
    exit 1
    ;;
esac

if [[ ! -d "${PROJECT_SRC}" ]]; then
  echo "Project source not found: ${PROJECT_SRC}" >&2
  exit 1
fi

if [[ ! -f "${PROJECT_SRC}/podman-compose.yml" ]]; then
  echo "Project source does not look like bitcoin-risk-brief: ${PROJECT_SRC}" >&2
  exit 1
fi

if ! id "${APP_USER}" >/dev/null 2>&1; then
  echo "User ${APP_USER} does not exist. Run 01-bootstrap-host.sh first." >&2
  exit 1
fi

log "Copying project to ${PROJECT_DEST}"
as_root mkdir -p "${PROJECT_DEST}"
as_root rsync -a --delete \
  --exclude '.env' \
  --exclude '.git' \
  --exclude 'data' \
  --exclude 'backups' \
  --exclude 'server-kit' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/dist' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  "${PROJECT_SRC}/" "${PROJECT_DEST}/"

as_root chown -R "${APP_USER}:${APP_USER}" "${PROJECT_DEST}"
as_root chmod 750 "${PROJECT_DEST}"
if [[ -d "${PROJECT_DEST}/scripts" ]]; then
  as_root find "${PROJECT_DEST}/scripts" -type f -name '*.sh' -exec chmod 750 {} +
fi

env_file="${PROJECT_DEST}/.env"
if ! as_root test -f "${env_file}"; then
  log "Creating ${env_file} from .env.production.example"
  as_root install -o "${APP_USER}" -g "${APP_USER}" -m 600 \
    "${PROJECT_DEST}/.env.production.example" "${env_file}"

  db_password="$(openssl rand -hex 32)"
  as_root sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=${db_password}|" "${env_file}"
  as_root sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:${db_password}@timescaledb:5432/bitcoin_risk_brief|" "${env_file}"

  if [[ -n "${PUBLIC_HOSTNAME}" ]]; then
    as_root sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://${PUBLIC_HOSTNAME}|" "${env_file}"
  fi
else
  log "Keeping existing ${env_file}"
  as_root chmod 600 "${env_file}"
  as_root chown "${APP_USER}:${APP_USER}" "${env_file}"
fi

log "Validating compose configuration as ${APP_USER}"
run_as_app bash -lc "cd '${PROJECT_DEST}' && ./scripts/manage.sh validate"

log "Deployment copy complete"
cat <<EOF
Review before starting the service:
  sudoedit ${env_file}

Important values:
  CORS_ORIGINS=https://your-domain.example
  COINMARKETCAP_API_KEY=   # optional
EOF
