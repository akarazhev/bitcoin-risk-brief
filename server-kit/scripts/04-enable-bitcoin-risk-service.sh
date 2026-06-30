#!/usr/bin/env bash
set -euo pipefail

APP_USER="${APP_USER:-apps}"
PROJECT_NAME="${PROJECT_NAME:-bitcoin-risk-brief}"
PROJECT_DEST="${PROJECT_DEST:-/srv/projects/${PROJECT_NAME}}"
SERVICE_NAME="${SERVICE_NAME:-bitcoin-risk-brief}"

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

if ! id "${APP_USER}" >/dev/null 2>&1; then
  echo "User ${APP_USER} does not exist. Run 01-bootstrap-host.sh first." >&2
  exit 1
fi

if ! as_root test -d "${PROJECT_DEST}"; then
  echo "Project directory not found: ${PROJECT_DEST}. Run 03-deploy-bitcoin-risk-brief.sh first." >&2
  exit 1
fi

compose_bin="${COMPOSE_BIN:-$(command -v podman-compose || true)}"
if [[ -z "${compose_bin}" ]]; then
  echo "podman-compose not found. Run 01-bootstrap-host.sh first." >&2
  exit 1
fi

log "Ensuring linger and user systemd directory"
as_root loginctl enable-linger "${APP_USER}"
app_uid="$(id -u "${APP_USER}")"
as_root systemctl start "user@${app_uid}.service"
run_as_app mkdir -p "/home/${APP_USER}/.config/systemd/user"

service_file="/home/${APP_USER}/.config/systemd/user/${SERVICE_NAME}.service"
tmp_service="$(mktemp)"
cat >"${tmp_service}" <<EOF
[Unit]
Description=${PROJECT_NAME} Podman Compose stack
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=${PROJECT_DEST}
ExecStart=${compose_bin} up -d --build --remove-orphans
ExecStop=${compose_bin} down
RemainAfterExit=yes
TimeoutStartSec=900

[Install]
WantedBy=default.target
EOF

as_root install -o "${APP_USER}" -g "${APP_USER}" -m 644 "${tmp_service}" "${service_file}"
rm -f "${tmp_service}"
if ! as_root test -f "${service_file}"; then
  echo "Service file was not created: ${service_file}" >&2
  exit 1
fi

log "Enabling and starting ${SERVICE_NAME}.service for ${APP_USER}"
run_user_systemctl daemon-reload
run_user_systemctl enable --now "${SERVICE_NAME}.service"

log "Service status"
run_user_systemctl status "${SERVICE_NAME}.service" --no-pager
